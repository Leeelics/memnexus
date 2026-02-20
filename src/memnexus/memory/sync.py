"""Real-time memory synchronization for MemNexus.

Provides real-time synchronization of memories between agents in a session.
Uses WebSocket and pub/sub for efficient distribution.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from memnexus.memory.store import MemoryEntry, MemoryStore


@dataclass
class SyncEvent:
    """Memory synchronization event."""
    event_type: str  # created, updated, deleted
    memory: MemoryEntry
    session_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "system"  # Which agent/system created the event
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.event_type,
            "session_id": self.session_id,
            "memory": self.memory.to_dict() if hasattr(self.memory, 'to_dict') else str(self.memory),
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class MemorySyncBus:
    """In-memory pub/sub bus for memory synchronization.
    
    Acts as a message broker between agents in a session.
    Can be backed by Redis for multi-instance deployments.
    
    Example:
        bus = MemorySyncBus()
        
        # Subscribe to session
        async def handler(event):
            print(f"New memory: {event.memory.content}")
        
        bus.subscribe("sess_123", handler)
        
        # Publish event
        await bus.publish(SyncEvent(...))
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self._subscribers: Dict[str, Set[Callable[[SyncEvent], None]]] = {}
        self._redis_url = redis_url
        self._redis: Optional[Any] = None
        self._running = False
    
    async def initialize(self) -> None:
        """Initialize the sync bus."""
        if self._redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(self._redis_url)
            except ImportError:
                pass  # Fall back to in-memory
        
        self._running = True
    
    async def close(self) -> None:
        """Close the sync bus."""
        self._running = False
        if self._redis:
            await self._redis.close()
    
    def subscribe(
        self,
        session_id: str,
        callback: Callable[[SyncEvent], None],
    ) -> None:
        """Subscribe to a session's memory events."""
        if session_id not in self._subscribers:
            self._subscribers[session_id] = set()
        self._subscribers[session_id].add(callback)
    
    def unsubscribe(
        self,
        session_id: str,
        callback: Callable[[SyncEvent], None],
    ) -> None:
        """Unsubscribe from a session."""
        if session_id in self._subscribers:
            self._subscribers[session_id].discard(callback)
            if not self._subscribers[session_id]:
                del self._subscribers[session_id]
    
    async def publish(self, event: SyncEvent) -> None:
        """Publish an event to all subscribers."""
        session_id = event.session_id
        
        # Notify local subscribers
        if session_id in self._subscribers:
            for callback in list(self._subscribers[session_id]):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(event))
                    else:
                        callback(event)
                except Exception as e:
                    print(f"Error notifying subscriber: {e}")
        
        # Publish to Redis for distributed sync
        if self._redis:
            try:
                await self._redis.publish(
                    f"memnexus:session:{session_id}",
                    event.to_json(),
                )
            except Exception as e:
                print(f"Error publishing to Redis: {e}")


class MemorySyncManager:
    """Manager for real-time memory synchronization.
    
    Coordinates memory sync between agents and maintains
    consistency across the session.
    
    Example:
        manager = MemorySyncManager(session_id="sess_123")
        await manager.initialize()
        
        # Watch for changes
        async for event in manager.watch():
            print(f"New event: {event.event_type}")
        
        # Sync a new memory
        await manager.sync_memory(memory_entry, source="claude")
    """
    
    def __init__(self, session_id: str, store: Optional[MemoryStore] = None):
        self.session_id = session_id
        self.store = store
        self.bus = MemorySyncBus()
        self._handlers: List[Callable[[SyncEvent], None]] = []
        self._initialized = False
        self._sync_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize the sync manager."""
        if self.store is None:
            self.store = MemoryStore()
            await self.store.initialize()
        
        await self.bus.initialize()
        
        # Subscribe to our own session
        self.bus.subscribe(self.session_id, self._on_event)
        
        self._initialized = True
    
    async def close(self) -> None:
        """Close the sync manager."""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        
        await self.bus.close()
        self._initialized = False
    
    async def sync_memory(
        self,
        memory: MemoryEntry,
        event_type: str = "created",
        source: str = "system",
    ) -> None:
        """Sync a memory to all subscribers.
        
        Args:
            memory: Memory entry to sync
            event_type: Type of sync event
            source: Source of the event
        """
        if not self._initialized:
            raise RuntimeError("Sync manager not initialized")
        
        # Store in database
        await self.store.add(memory)
        
        # Create and publish event
        event = SyncEvent(
            event_type=event_type,
            memory=memory,
            session_id=self.session_id,
            source=source,
        )
        
        await self.bus.publish(event)
    
    def add_handler(self, handler: Callable[[SyncEvent], None]) -> None:
        """Add an event handler."""
        self._handlers.append(handler)
    
    def remove_handler(self, handler: Callable[[SyncEvent], None]) -> None:
        """Remove an event handler."""
        self._handlers.remove(handler)
    
    def _on_event(self, event: SyncEvent) -> None:
        """Handle incoming events."""
        # Notify all registered handlers
        for handler in self._handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception as e:
                print(f"Error in sync handler: {e}")
    
    async def watch(self) -> asyncio.Queue[SyncEvent]:
        """Get a queue for watching events.
        
        Returns:
            Queue that receives all sync events
        """
        queue: asyncio.Queue[SyncEvent] = asyncio.Queue()
        
        def handler(event: SyncEvent) -> None:
            queue.put_nowait(event)
        
        self.add_handler(handler)
        
        return queue
    
    async def start_sync_loop(self, interval: float = 1.0) -> None:
        """Start a background sync loop.
        
        Periodically checks for new memories and broadcasts them.
        
        Args:
            interval: Check interval in seconds
        """
        if self._sync_task:
            return
        
        self._sync_task = asyncio.create_task(
            self._sync_loop(interval),
            name=f"sync-loop-{self.session_id}",
        )
    
    async def _sync_loop(self, interval: float) -> None:
        """Background sync loop."""
        last_check = datetime.utcnow()
        
        while True:
            try:
                await asyncio.sleep(interval)
                
                # Get new memories since last check
                # This is a placeholder - actual implementation would
                # query by timestamp
                last_check = datetime.utcnow()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in sync loop: {e}")


class AgentMemoryBridge:
    """Bridge between an agent and the memory sync system.
    
    Connects an agent's output to the shared memory system,
    automatically syncing all outputs.
    
    Example:
        bridge = AgentMemoryBridge(
            session_id="sess_123",
            agent_name="claude",
            sync_manager=sync_manager,
        )
        
        # Capture agent output
        bridge.capture_output("I've created the API endpoint")
        
        # Capture file changes
        bridge.capture_file_change("/path/to/file.py", "created", content="...")
    """
    
    def __init__(
        self,
        session_id: str,
        agent_name: str,
        sync_manager: MemorySyncManager,
    ):
        self.session_id = session_id
        self.agent_name = agent_name
        self.sync_manager = sync_manager
    
    async def capture_output(
        self,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Capture and sync agent output.
        
        Returns:
            Memory entry ID
        """
        memory = MemoryEntry(
            content=content,
            source=self.agent_name,
            session_id=self.session_id,
            memory_type=memory_type,
            metadata=metadata or {},
        )
        
        await self.sync_manager.sync_memory(
            memory,
            event_type="created",
            source=self.agent_name,
        )
        
        return memory.id
    
    async def capture_file_change(
        self,
        file_path: str,
        change_type: str,
        content: Optional[str] = None,
    ) -> str:
        """Capture a file change.
        
        Args:
            file_path: Path to file
            change_type: Type of change (created, modified, deleted)
            content: Optional file content
            
        Returns:
            Memory entry ID
        """
        content_str = f"[{change_type.upper()}] {file_path}"
        if content:
            content_str += f"\n{content[:1000]}..."
        
        return await self.capture_output(
            content=content_str,
            memory_type="file_change",
            metadata={
                "file_path": file_path,
                "change_type": change_type,
            },
        )
    
    async def capture_thought(
        self,
        thought: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Capture an agent's thought process.
        
        Args:
            thought: The thought content
            context: Optional context
            
        Returns:
            Memory entry ID
        """
        return await self.capture_output(
            content=thought,
            memory_type="thought",
            metadata=context,
        )
    
    def create_sync_callback(self) -> Callable[[str], None]:
        """Create a callback function for capturing output.
        
        Returns a callback that can be passed to agent.on_output().
        """
        async def callback(output: str) -> None:
            await self.capture_output(output)
        
        return callback
