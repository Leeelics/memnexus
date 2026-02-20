"""ACP (Agent Client Protocol) implementation for MemNexus.

This module implements the ACP protocol for communication with
Claude Code, Kimi CLI, and other ACP-compatible agents.

ACP Protocol: JSON-RPC over stdio with bidirectional streaming.
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Protocol


class ACPMessageType(str, Enum):
    """ACP message types."""
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    TOOLS_CALL = "tools/call"
    TOOLS_RESULT = "tools/result"
    RESOURCES_READ = "resources/read"
    RESOURCES_RESULT = "resources/result"
    PROMPTS_REQUEST = "prompts/request"
    PROMPTS_RESULT = "prompts/result"
    NOTIFICATION = "notifications/message"
    PING = "ping"
    PONG = "pong"


class ACPEventType(str, Enum):
    """ACP event types."""
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class ACPEvent:
    """ACP event."""
    type: ACPEventType
    data: Dict[str, Any]
    id: Optional[str] = None
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())


@dataclass
class ACPCapabilities:
    """ACP capabilities."""
    tools: bool = True
    resources: bool = True
    prompts: bool = True
    logging: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        caps = {}
        if self.tools:
            caps["tools"] = {"listChanged": True}
        if self.resources:
            caps["resources"] = {"subscribe": True, "listChanged": True}
        if self.prompts:
            caps["prompts"] = {"listChanged": True}
        if self.logging:
            caps["logging"] = {}
        return caps


class ToolHandler(Protocol):
    """Protocol for tool handlers."""
    
    async def __call__(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call."""
        ...


class ACPConnection:
    """ACP connection handler.
    
    Manages a single ACP connection over stdio.
    
    Example:
        process = await asyncio.create_subprocess_exec(
            "claude", "--acp",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        
        conn = ACPConnection(process)
        await conn.initialize()
        
        async for event in conn.send_prompt("Hello"):
            print(event)
    """
    
    PROTOCOL_VERSION = "2025-01-01"
    
    def __init__(
        self,
        process: asyncio.subprocess.Process,
        server_name: str = "MemNexus",
        server_version: str = "0.1.0",
    ):
        self.process = process
        self.server_name = server_name
        self.server_version = server_version
        self.capabilities = ACPCapabilities()
        
        self._initialized = False
        self._request_id = 0
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._message_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._read_task: Optional[asyncio.Task] = None
        self._tool_handlers: Dict[str, ToolHandler] = {}
    
    def register_tool_handler(self, name: str, handler: ToolHandler) -> None:
        """Register a tool handler."""
        self._tool_handlers[name] = handler
    
    async def initialize(self) -> bool:
        """Initialize the ACP connection.
        
        Sends initialize request and waits for response.
        """
        if self._initialized:
            return True
        
        # Start reading messages
        self._read_task = asyncio.create_task(self._read_messages())
        
        # Send initialize request
        response = await self._send_request(
            method="initialize",
            params={
                "protocolVersion": self.PROTOCOL_VERSION,
                "capabilities": self.capabilities.to_dict(),
                "clientInfo": {
                    "name": self.server_name,
                    "version": self.server_version,
                },
            },
        )
        
        if response and "result" in response:
            self._initialized = True
            # Send initialized notification
            await self._send_notification("notifications/initialized", {})
            return True
        
        return False
    
    async def close(self) -> None:
        """Close the connection."""
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
        
        self._initialized = False
    
    async def send_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[ACPEvent]:
        """Send a prompt and stream responses.
        
        Args:
            prompt: The prompt text
            context: Optional context data
            
        Yields:
            ACPEvent events (messages, tool calls, etc.)
        """
        if not self._initialized:
            raise RuntimeError("ACP connection not initialized")
        
        request_id = await self._send(
            method="prompts/request",
            params={
                "name": "default",
                "arguments": {
                    "prompt": prompt,
                    **(context or {}),
                },
            },
        )
        
        # Collect events until completion
        completion_event = asyncio.Event()
        event_buffer: List[ACPEvent] = []
        
        async def event_collector():
            while not completion_event.is_set():
                try:
                    message = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=0.1
                    )
                    event = self._parse_message(message)
                    if event:
                        event_buffer.append(event)
                        
                        # Check for completion
                        if self._is_completion_message(message, request_id):
                            completion_event.set()
                except asyncio.TimeoutError:
                    continue
        
        collector_task = asyncio.create_task(event_collector())
        
        try:
            # Yield events as they arrive
            last_index = 0
            while not completion_event.is_set():
                while last_index < len(event_buffer):
                    yield event_buffer[last_index]
                    last_index += 1
                await asyncio.sleep(0.01)
            
            # Yield remaining events
            while last_index < len(event_buffer):
                yield event_buffer[last_index]
                last_index += 1
                
        finally:
            completion_event.set()
            collector_task.cancel()
            try:
                await collector_task
            except asyncio.CancelledError:
                pass
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Call a tool on the agent.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if not self._initialized:
            raise RuntimeError("ACP connection not initialized")
        
        response = await self._send_request(
            method="tools/call",
            params={
                "name": name,
                "arguments": arguments,
            },
        )
        
        return response.get("result", {}) if response else {}
    
    def _parse_message(self, message: Dict[str, Any]) -> Optional[ACPEvent]:
        """Parse an ACP message into an event."""
        if "error" in message:
            return ACPEvent(
                type=ACPEventType.ERROR,
                data={"error": message["error"]},
                id=message.get("id"),
            )
        
        method = message.get("method", "")
        
        if method == "notifications/message":
            return ACPEvent(
                type=ACPEventType.MESSAGE,
                data=message.get("params", {}),
                id=message.get("id"),
            )
        elif method == "tools/call":
            return ACPEvent(
                type=ACPEventType.TOOL_CALL,
                data=message.get("params", {}),
                id=message.get("id"),
            )
        elif "result" in message:
            return ACPEvent(
                type=ACPEventType.TOOL_RESULT,
                data=message["result"],
                id=message.get("id"),
            )
        
        return None
    
    def _is_completion_message(self, message: Dict[str, Any], request_id: str) -> bool:
        """Check if message indicates completion of a request."""
        # Check for completion indicators
        if message.get("id") == request_id and "result" in message:
            return True
        
        params = message.get("params", {})
        if params.get("type") == "completion":
            return True
        
        return False
    
    async def _read_messages(self) -> None:
        """Read messages from stdout."""
        if not self.process.stdout:
            return
        
        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                try:
                    message = json.loads(line.decode().strip())
                    
                    # Handle requests that need responses
                    if "method" in message and "id" in message:
                        await self._handle_request(message)
                    # Handle responses to our requests
                    elif "id" in message:
                        future = self._pending_requests.pop(message["id"], None)
                        if future and not future.done():
                            future.set_result(message)
                    # Handle notifications
                    elif "method" in message:
                        await self._message_queue.put(message)
                        
                except json.JSONDecodeError:
                    # Not JSON, might be regular output
                    await self._message_queue.put({
                        "method": "notifications/message",
                        "params": {
                            "level": "info",
                            "message": line.decode().strip(),
                        },
                    })
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self._message_queue.put({
                "error": str(e),
            })
    
    async def _handle_request(self, message: Dict[str, Any]) -> None:
        """Handle incoming request from agent."""
        method = message.get("method", "")
        params = message.get("params", {})
        req_id = message.get("id")
        
        if method == "tools/call":
            # Handle tool call from agent
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            handler = self._tool_handlers.get(tool_name)
            if handler:
                try:
                    result = await handler(tool_name, arguments)
                    await self._send_response(req_id, result)
                except Exception as e:
                    await self._send_error(req_id, str(e))
            else:
                await self._send_error(req_id, f"Unknown tool: {tool_name}", code=-32601)
        
        elif method == "ping":
            await self._send_response(req_id, {})
    
    def _next_id(self) -> str:
        """Generate next request ID."""
        self._request_id += 1
        return str(self._request_id)
    
    async def _send(
        self,
        method: str,
        params: Dict[str, Any],
    ) -> str:
        """Send a request without waiting for response."""
        req_id = self._next_id()
        
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        
        await self._write_message(message)
        return req_id
    
    async def _send_request(
        self,
        method: str,
        params: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Optional[Dict[str, Any]]:
        """Send a request and wait for response."""
        req_id = self._next_id()
        
        # Create future for response
        future: asyncio.Future[Dict[str, Any]] = asyncio.get_event_loop().create_future()
        self._pending_requests[req_id] = future
        
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        
        await self._write_message(message)
        
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            return None
    
    async def _send_response(self, req_id: str, result: Dict[str, Any]) -> None:
        """Send a response."""
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }
        await self._write_message(message)
    
    async def _send_error(
        self,
        req_id: str,
        message: str,
        code: int = -32600,
    ) -> None:
        """Send an error response."""
        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": code,
                "message": message,
            },
        }
        await self._write_message(msg)
    
    async def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send a notification (no response expected)."""
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        await self._write_message(message)
    
    async def _write_message(self, message: Dict[str, Any]) -> None:
        """Write a message to stdin."""
        if not self.process.stdin:
            raise RuntimeError("Process stdin not available")
        
        data = json.dumps(message) + "\n"
        self.process.stdin.write(data.encode())
        await self.process.stdin.drain()


class ACPProtocolServer:
    """ACP Protocol Server for MemNexus.
    
    Manages multiple ACP connections and routes messages between
    agents and the memory system.
    
    Example:
        server = ACPProtocolServer(session_manager)
        await server.start()
        
        # Connect an agent
        conn = await server.connect_agent("claude", session_id="sess_123")
        
        # Send prompt
        async for event in conn.send_prompt("Hello"):
            print(event)
    """
    
    def __init__(self, session_manager: Any):
        self.session_manager = session_manager
        self._connections: Dict[str, ACPConnection] = {}
        self._running = False
    
    async def start(self) -> None:
        """Start the protocol server."""
        self._running = True
    
    async def stop(self) -> None:
        """Stop the protocol server."""
        self._running = False
        
        # Close all connections
        for conn in self._connections.values():
            await conn.close()
        self._connections.clear()
    
    async def connect_agent(
        self,
        cli: str,
        session_id: str,
        working_dir: str = ".",
        env: Optional[Dict[str, str]] = None,
    ) -> Optional[ACPConnection]:
        """Connect an ACP-compatible agent.
        
        Args:
            cli: CLI command (e.g., "claude --acp")
            session_id: Session ID
            working_dir: Working directory
            env: Additional environment variables
            
        Returns:
            ACPConnection if successful
        """
        import shutil
        
        # Parse CLI command
        cli_parts = cli.split()
        cli_name = cli_parts[0]
        cli_args = cli_parts[1:] if len(cli_parts) > 1 else []
        
        # Find CLI executable
        cli_path = shutil.which(cli_name)
        if not cli_path:
            raise RuntimeError(f"CLI not found: {cli_name}")
        
        # Add --acp flag if not present
        if "--acp" not in cli_args:
            cli_args.append("--acp")
        
        # Prepare environment
        process_env = {
            **os.environ,
            "MEMNEXUS_SESSION_ID": session_id,
            "MEMNEXUS_ENABLED": "1",
            **(env or {}),
        }
        
        # Start process
        process = await asyncio.create_subprocess_exec(
            cli_path,
            *cli_args,
            cwd=working_dir,
            env=process_env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Create connection
        conn = ACPConnection(process)
        
        # Register memory tools
        self._register_memory_tools(conn, session_id)
        
        # Initialize
        if await conn.initialize():
            conn_id = str(uuid.uuid4())[:8]
            self._connections[conn_id] = conn
            return conn
        else:
            await conn.close()
            return None
    
    def _register_memory_tools(self, conn: ACPConnection, session_id: str) -> None:
        """Register memory-related tool handlers."""
        
        async def handle_memory_search(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            """Handle memory search tool call."""
            context = self.session_manager.get_context_manager(session_id)
            if not context:
                return {"error": "Session not found"}
            
            query = args.get("query", "")
            limit = args.get("limit", 5)
            
            results = await context.get_context(query, limit)
            
            return {
                "memories": [
                    {
                        "id": m.id,
                        "content": m.content,
                        "source": m.source,
                        "type": m.memory_type,
                    }
                    for m in results.relevant_memories
                ],
                "summary": results.summary,
            }
        
        async def handle_memory_store(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            """Handle memory store tool call."""
            context = self.session_manager.get_context_manager(session_id)
            if not context:
                return {"error": "Session not found"}
            
            content = args.get("content", "")
            source = args.get("source", "agent")
            memory_type = args.get("type", "generic")
            
            entry_id = await context.store_agent_output(
                agent=source,
                content=content,
                memory_type=memory_type,
            )
            
            return {"id": entry_id, "status": "stored"}
        
        conn.register_tool_handler("memory_search", handle_memory_search)
        conn.register_tool_handler("memory_store", handle_memory_store)
    
    def get_connection(self, conn_id: str) -> Optional[ACPConnection]:
        """Get a connection by ID."""
        return self._connections.get(conn_id)
    
    async def disconnect(self, conn_id: str) -> None:
        """Disconnect an agent."""
        conn = self._connections.pop(conn_id, None)
        if conn:
            await conn.close()


import os
