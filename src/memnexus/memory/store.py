"""Vector memory store using LanceDB."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import lancedb
from lancedb.pydantic import LanceModel, Vector

from memnexus.core.config import settings


@dataclass
class MemoryEntry:
    """A single memory entry.
    
    Attributes:
        content: The actual content/text
        source: Source of the memory (agent name, user, etc.)
        session_id: Associated session ID
        memory_type: Type of memory (code, conversation, file, etc.)
        metadata: Additional metadata
        embedding: Vector embedding (optional, auto-generated if not provided)
    """
    content: str
    source: str = "system"
    session_id: Optional[str] = None
    memory_type: str = "generic"
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "session_id": self.session_id,
            "memory_type": self.memory_type,
            "metadata": json.dumps(self.metadata),
            "timestamp": self.timestamp.isoformat(),
        }


# LanceDB Schema
class MemorySchema(LanceModel):
    """LanceDB schema for memory entries."""
    id: str
    content: str
    source: str
    session_id: Optional[str]
    memory_type: str
    metadata: str
    timestamp: str
    # Vector field - using sentence-transformers embeddings
    vector: Vector(384)  # all-MiniLM-L6-v2 dimension


class MemoryStore:
    """Vector memory store using LanceDB.
    
    Provides semantic search and storage for agent context:
    - Code snippets
    - Conversation history
    - File contents
    - Task results
    
    Example:
        store = MemoryStore()
        await store.initialize()
        
        # Add memory
        entry = MemoryEntry(
            content="User wants to build a REST API",
            source="claude",
            session_id="sess_123",
            memory_type="conversation"
        )
        await store.add(entry)
        
        # Search memories
        results = await store.search("REST API requirements", limit=5)
    """
    
    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or settings.LANCEDB_URI
        self._db: Optional[lancedb.DBConnection] = None
        self._table: Optional[lancedb.table.Table] = None
        self._embedding_func = None
    
    async def initialize(self) -> None:
        """Initialize the memory store."""
        # Expand home directory
        uri = Path(self.uri).expanduser()
        uri.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to LanceDB
        self._db = await lancedb.connect_async(str(uri))
        
        # Get or create table
        table_name = "memories"
        try:
            self._table = await self._db.open_table(table_name)
        except Exception:
            # Table doesn't exist, create it
            self._table = await self._db.create_table(
                table_name,
                schema=MemorySchema,
            )
        
        # Initialize embedding function (sentence-transformers)
        try:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            self._embedding_model = None
    
    async def add(self, entry: MemoryEntry) -> str:
        """Add a memory entry to the store.
        
        Args:
            entry: The memory entry to add
            
        Returns:
            The ID of the added entry
        """
        if self._table is None:
            raise RuntimeError("Memory store not initialized. Call initialize() first.")
        
        # Generate embedding if not provided
        if entry.embedding is None and self._embedding_model is not None:
            entry.embedding = self._embedding_model.encode(
                entry.content
            ).tolist()
        
        if entry.embedding is None:
            # Fallback: zero vector
            entry.embedding = [0.0] * 384
        
        # Create record
        record = {
            "id": entry.id,
            "content": entry.content,
            "source": entry.source,
            "session_id": entry.session_id,
            "memory_type": entry.memory_type,
            "metadata": json.dumps(entry.metadata),
            "timestamp": entry.timestamp.isoformat(),
            "vector": entry.embedding,
        }
        
        # Add to table
        await self._table.add([record])
        
        return entry.id
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        session_id: Optional[str] = None,
        memory_type: Optional[str] = None,
    ) -> List[MemoryEntry]:
        """Search memories by semantic similarity.
        
        Args:
            query: Search query
            limit: Maximum number of results
            session_id: Filter by session ID
            memory_type: Filter by memory type
            
        Returns:
            List of matching memory entries
        """
        if self._table is None:
            raise RuntimeError("Memory store not initialized. Call initialize() first.")
        
        # Generate query embedding
        if self._embedding_model is not None:
            query_vector = self._embedding_model.encode(query).tolist()
        else:
            query_vector = [0.0] * 384
        
        # Build search
        search = self._table.search(query_vector).limit(limit)
        
        # Apply filters
        filters = []
        if session_id:
            filters.append(f"session_id = '{session_id}'")
        if memory_type:
            filters.append(f"memory_type = '{memory_type}'")
        
        if filters:
            where_clause = " AND ".join(filters)
            search = search.where(where_clause)
        
        # Execute search
        results = await search.to_list()
        
        # Convert to MemoryEntry objects
        entries = []
        for r in results:
            entry = MemoryEntry(
                id=r["id"],
                content=r["content"],
                source=r["source"],
                session_id=r["session_id"],
                memory_type=r["memory_type"],
                metadata=json.loads(r["metadata"]),
                timestamp=datetime.fromisoformat(r["timestamp"]),
            )
            entries.append(entry)
        
        return entries
    
    async def get_by_session(
        self,
        session_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryEntry]:
        """Get all memories for a session.
        
        Args:
            session_id: Session ID
            memory_type: Optional filter by type
            limit: Maximum results
            
        Returns:
            List of memory entries
        """
        if self._table is None:
            raise RuntimeError("Memory store not initialized")
        
        # Build query
        query = self._table.query().limit(limit)
        
        # Apply filters
        filters = [f"session_id = '{session_id}'"]
        if memory_type:
            filters.append(f"memory_type = '{memory_type}'")
        
        where_clause = " AND ".join(filters)
        query = query.where(where_clause)
        
        # Execute
        results = await query.to_list()
        
        return [
            MemoryEntry(
                id=r["id"],
                content=r["content"],
                source=r["source"],
                session_id=r["session_id"],
                memory_type=r["memory_type"],
                metadata=json.loads(r["metadata"]),
                timestamp=datetime.fromisoformat(r["timestamp"]),
            )
            for r in results
        ]
    
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry.
        
        Args:
            entry_id: ID of entry to delete
            
        Returns:
            True if deleted, False if not found
        """
        if self._table is None:
            raise RuntimeError("Memory store not initialized")
        
        try:
            await self._table.delete(f"id = '{entry_id}'")
            return True
        except Exception:
            return False
    
    async def clear_session(self, session_id: str) -> int:
        """Delete all memories for a session.
        
        Args:
            session_id: Session ID to clear
            
        Returns:
            Number of entries deleted
        """
        if self._table is None:
            raise RuntimeError("Memory store not initialized")
        
        try:
            # Get count before delete
            before = len(await self._table.to_pandas())
            await self._table.delete(f"session_id = '{session_id}'")
            after = len(await self._table.to_pandas())
            return before - after
        except Exception:
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics.
        
        Returns:
            Dictionary with stats
        """
        if self._table is None:
            return {"error": "Not initialized"}
        
        try:
            df = await self._table.to_pandas()
            return {
                "total_entries": len(df),
                "sessions": df["session_id"].nunique() if len(df) > 0 else 0,
                "memory_types": df["memory_type"].value_counts().to_dict() if len(df) > 0 else {},
            }
        except Exception as e:
            return {"error": str(e)}
