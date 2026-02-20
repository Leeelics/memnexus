"""Context manager for session memory."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from memnexus.memory.store import MemoryEntry, MemoryStore


@dataclass
class ContextSnapshot:
    """Snapshot of session context."""
    session_id: str
    recent_memories: List[MemoryEntry]
    relevant_memories: List[MemoryEntry]
    summary: str = ""


class ContextManager:
    """Manages context for a session.
    
    Coordinates memory storage and retrieval:
    - Stores agent outputs as memories
    - Retrieves relevant context for queries
    - Maintains conversation history
    
    Example:
        context = ContextManager(session_id="sess_123")
        await context.initialize()
        
        # Store agent output
        await context.store_agent_output(
            agent="claude",
            content="I've created the API endpoint",
            memory_type="code"
        )
        
        # Get context for a query
        snapshot = await context.get_context(
            query="What did claude build?",
            limit=10
        )
    """
    
    def __init__(self, session_id: str, store: Optional[MemoryStore] = None):
        self.session_id = session_id
        self.store = store
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the context manager."""
        if self.store is None:
            self.store = MemoryStore()
            await self.store.initialize()
        self._initialized = True
    
    async def store_agent_output(
        self,
        agent: str,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store agent output as memory.
        
        Args:
            agent: Agent name/source
            content: The content to store
            memory_type: Type of memory
            metadata: Additional metadata
            
        Returns:
            Memory entry ID
        """
        if not self._initialized:
            raise RuntimeError("Context manager not initialized")
        
        entry = MemoryEntry(
            content=content,
            source=agent,
            session_id=self.session_id,
            memory_type=memory_type,
            metadata=metadata or {},
        )
        
        return await self.store.add(entry)
    
    async def store_file_change(
        self,
        agent: str,
        file_path: str,
        change_type: str,  # created, modified, deleted
        content: Optional[str] = None,
    ) -> str:
        """Store a file change.
        
        Args:
            agent: Agent that made the change
            file_path: Path to the file
            change_type: Type of change
            content: Optional file content
            
        Returns:
            Memory entry ID
        """
        content_str = f"[{change_type.upper()}] {file_path}"
        if content:
            content_str += f"\n{content[:1000]}..."  # Truncate long content
        
        return await self.store_agent_output(
            agent=agent,
            content=content_str,
            memory_type="file_change",
            metadata={
                "file_path": file_path,
                "change_type": change_type,
            },
        )
    
    async def store_task_result(
        self,
        agent: str,
        task: str,
        result: str,
        success: bool = True,
    ) -> str:
        """Store a task result.
        
        Args:
            agent: Agent that completed the task
            task: Task description
            result: Task result/output
            success: Whether task succeeded
            
        Returns:
            Memory entry ID
        """
        content = f"Task: {task}\nResult: {result}"
        
        return await self.store_agent_output(
            agent=agent,
            content=content,
            memory_type="task_result",
            metadata={
                "task": task,
                "success": success,
            },
        )
    
    async def get_context(
        self,
        query: str,
        limit: int = 10,
    ) -> ContextSnapshot:
        """Get relevant context for a query.
        
        Args:
            query: The query to search for
            limit: Maximum number of results
            
        Returns:
            Context snapshot with relevant memories
        """
        if not self._initialized:
            raise RuntimeError("Context manager not initialized")
        
        # Search for relevant memories
        relevant = await self.store.search(
            query=query,
            limit=limit,
            session_id=self.session_id,
        )
        
        # Get recent memories (last 20)
        recent = await self.store.get_by_session(
            session_id=self.session_id,
            limit=20,
        )
        
        # Sort by timestamp descending
        recent.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Generate summary
        summary = self._generate_summary(recent, relevant)
        
        return ContextSnapshot(
            session_id=self.session_id,
            recent_memories=recent[:10],
            relevant_memories=relevant,
            summary=summary,
        )
    
    async def get_conversation_history(
        self,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """Get conversation history.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of conversation memories
        """
        if not self._initialized:
            raise RuntimeError("Context manager not initialized")
        
        memories = await self.store.get_by_session(
            session_id=self.session_id,
            memory_type="conversation",
            limit=limit,
        )
        
        # Sort by timestamp
        memories.sort(key=lambda x: x.timestamp)
        
        return memories
    
    async def get_code_context(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Get code-related context.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of code-related memories
        """
        if not self._initialized:
            raise RuntimeError("Context manager not initialized")
        
        # Search for code-related memories
        code_types = ["code", "file_change"]
        results = []
        
        for mem_type in code_types:
            memories = await self.store.get_by_session(
                session_id=self.session_id,
                memory_type=mem_type,
                limit=limit,
            )
            results.extend(memories)
        
        # Also do semantic search
        semantic = await self.store.search(
            query=query,
            limit=limit,
            session_id=self.session_id,
        )
        
        # Combine and deduplicate
        seen_ids = set()
        combined = []
        for m in results + semantic:
            if m.id not in seen_ids:
                seen_ids.add(m.id)
                combined.append(m)
        
        return combined[:limit]
    
    def _generate_summary(
        self,
        recent: List[MemoryEntry],
        relevant: List[MemoryEntry],
    ) -> str:
        """Generate a summary of the context."""
        if not recent:
            return "No context available."
        
        # Count by source
        sources = {}
        for m in recent:
            sources[m.source] = sources.get(m.source, 0) + 1
        
        # Count by type
        types = {}
        for m in recent:
            types[m.memory_type] = types.get(m.memory_type, 0) + 1
        
        summary_parts = [
            f"Session has {len(recent)} recent memories from {len(sources)} sources.",
            f"Sources: {', '.join(f'{k}({v})' for k, v in sources.items())}",
            f"Types: {', '.join(f'{k}({v})' for k, v in types.items())}",
        ]
        
        return " ".join(summary_parts)
    
    async def clear(self) -> int:
        """Clear all memories for this session.
        
        Returns:
            Number of entries deleted
        """
        if not self._initialized:
            raise RuntimeError("Context manager not initialized")
        
        return await self.store.clear_session(self.session_id)
