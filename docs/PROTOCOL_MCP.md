# MCP (Model Context Protocol) 协议规范

## 概述

MCP 是 Anthropic 开放的协议标准，用于连接 AI 模型与外部数据源和工具。

## 与 ACP 的区别

| 特性 | ACP | MCP |
|-----|-----|-----|
| 设计目标 | IDE-Agent 通信 | 模型-工具连接 |
| 通信方向 | 双向流 | 请求-响应 + 通知 |
| 连接模式 | 长连接 | 可短连接 |
| 工具发现 | 运行时协商 | 预注册 |

## 核心概念

### Resources（资源）

```json
// Server 注册资源
{
  "resources": [
    {
      "uri": "memory://sess_abc123",
      "name": "Session Memory",
      "mimeType": "application/json",
      "description": "Shared memory for session"
    }
  ]
}

// Client 读取资源
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/read",
  "params": {
    "uri": "memory://sess_abc123"
  }
}
```

### Tools（工具）

```json
// Server 注册工具
{
  "tools": [
    {
      "name": "query_memory",
      "description": "Query shared memory",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "tags": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["query"]
      }
    }
  ]
}

// Client 调用工具
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "query_memory",
    "arguments": {
      "query": "user authentication",
      "tags": ["backend", "api"]
    }
  }
}
```

### Prompts（提示模板）

```json
// Server 注册提示
{
  "prompts": [
    {
      "name": "collaborate",
      "description": "Collaborate with other agents",
      "arguments": [
        {
          "name": "other_agent_output",
          "description": "Output from another agent",
          "required": true
        }
      ]
    }
  ]
}
```

## MemNexus 作为 MCP Server

```python
class MemNexusMCPServer:
    """MemNexus MCP 服务器实现"""
    
    def __init__(self, memory_engine: MemoryEngine):
        self.memory = memory_engine
        
    async def handle_request(self, request: dict) -> dict:
        method = request.get("method")
        
        if method == "initialize":
            return self._handle_initialize()
        elif method == "resources/list":
            return self._handle_resources_list()
        elif method == "resources/read":
            return await self._handle_resources_read(request)
        elif method == "tools/list":
            return self._handle_tools_list()
        elif method == "tools/call":
            return await self._handle_tools_call(request)
        elif method == "prompts/list":
            return self._handle_prompts_list()
        elif method == "prompts/get":
            return await self._handle_prompts_get(request)
            
    def _handle_tools_list(self) -> dict:
        return {
            "tools": [
                {
                    "name": "query_memory",
                    "description": "Query shared memory by semantic search",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session ID"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by tags"
                            }
                        },
                        "required": ["query", "session_id"]
                    }
                },
                {
                    "name": "save_memory",
                    "description": "Save to shared memory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "object",
                                "description": "Content to save"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["code", "decision", "note"]
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["content", "type"]
                    }
                }
            ]
        }
        
    async def _handle_tools_call(self, request: dict) -> dict:
        tool_name = request["params"]["name"]
        arguments = request["params"]["arguments"]
        
        if tool_name == "query_memory":
            results = await self.memory.query(
                session_id=arguments["session_id"],
                semantic_search=arguments["query"],
                tags=arguments.get("tags", [])
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps([r.dict() for r in results], indent=2)
                    }
                ]
            }
        elif tool_name == "save_memory":
            memory_id = await self.memory.save(
                type=arguments["type"],
                content=arguments["content"],
                tags=arguments.get("tags", [])
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Saved memory: {memory_id}"
                    }
                ]
            }
```

## MemNexus 作为 MCP Client

```python
class MemNexusMCPClient:
    """MemNexus MCP 客户端 - 连接外部工具"""
    
    def __init__(self):
        self.servers: Dict[str, MCPConnection] = {}
        
    async def connect_to_server(self, name: str, command: str, args: List[str]):
        """连接到 MCP 服务器"""
        process = await asyncio.create_subprocess_exec(
            command, *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        conn = MCPConnection(process)
        
        # 初始化
        await conn.send({
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "MemNexus",
                    "version": "0.1.0"
                }
            }
        })
        
        response = await conn.receive()
        
        self.servers[name] = conn
        return conn
        
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict
    ) -> dict:
        """调用远程工具"""
        conn = self.servers[server_name]
        
        await conn.send({
            "jsonrpc": "2.0",
            "id": generate_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        })
        
        return await conn.receive()
```

## 参考

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
