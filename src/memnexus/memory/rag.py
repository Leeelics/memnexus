"""LlamaIndex RAG Pipeline for MemNexus.

Provides advanced document processing, indexing, and retrieval capabilities
using LlamaIndex and LanceDB.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from memnexus.core.config import settings


@dataclass
class Document:
    """Document for RAG processing."""
    content: str
    source: str
    doc_type: str = "text"  # text, code, markdown, etc.
    metadata: Dict[str, Any] = None
    doc_id: str = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.doc_id is None:
            # Generate ID from content hash
            self.doc_id = hashlib.md5(
                f"{self.source}:{self.content[:100]}".encode()
            ).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.doc_id,
            "content": self.content,
            "source": self.source,
            "type": self.doc_type,
            "metadata": self.metadata,
        }


@dataclass
class Chunk:
    """Document chunk."""
    text: str
    doc_id: str
    chunk_index: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DocumentChunker:
    """Document chunker with language-aware splitting."""
    
    DEFAULT_CHUNK_SIZE = 512
    DEFAULT_CHUNK_OVERLAP = 50
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, document: Document) -> List[Chunk]:
        """Chunk a document.
        
        Uses language-aware splitting for code files.
        """
        if document.doc_type in ["code", "python", "javascript", "typescript"]:
            return self._chunk_code(document)
        elif document.doc_type == "markdown":
            return self._chunk_markdown(document)
        else:
            return self._chunk_text(document)
    
    def _chunk_text(self, document: Document) -> List[Chunk]:
        """Simple text chunking by size."""
        content = document.content
        chunks = []
        
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # Try to find a good breaking point
            if end < len(content):
                # Look for sentence boundary
                for i in range(min(end, len(content) - 1), start, -1):
                    if content[i] in ".!?:\n":
                        end = i + 1
                        break
            
            chunk_text = content[start:end]
            chunks.append(Chunk(
                text=chunk_text,
                doc_id=document.doc_id,
                chunk_index=chunk_index,
                metadata={
                    "source": document.source,
                    "type": document.doc_type,
                },
            ))
            
            chunk_index += 1
            start = end - self.chunk_overlap
        
        return chunks
    
    def _chunk_code(self, document: Document) -> List[Chunk]:
        """Code-aware chunking."""
        content = document.content
        chunks = []
        chunk_index = 0
        
        # Split by functions/classes for code
        import re
        
        # Python pattern
        pattern = r'(?:^|\n)(class\s+\w+|def\s+\w+|function\s+\w+)'
        matches = list(re.finditer(pattern, content))
        
        if len(matches) < 2:
            # Not enough functions, use text chunking
            return self._chunk_text(document)
        
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            
            chunk_text = content[start:end].strip()
            if len(chunk_text) > self.chunk_size:
                # Further split large chunks
                sub_chunks = self._split_large_chunk(
                    chunk_text, document.doc_id, chunk_index, document.source
                )
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
            else:
                chunks.append(Chunk(
                    text=chunk_text,
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    metadata={
                        "source": document.source,
                        "type": "code",
                        "function": match.group(1) if match.groups() else "",
                    },
                ))
                chunk_index += 1
        
        return chunks
    
    def _chunk_markdown(self, document: Document) -> List[Chunk]:
        """Markdown-aware chunking."""
        content = document.content
        chunks = []
        chunk_index = 0
        
        # Split by headers
        import re
        pattern = r'(^|\n)#{1,6}\s+.+'
        matches = list(re.finditer(pattern, content))
        
        if len(matches) < 2:
            return self._chunk_text(document)
        
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            
            chunk_text = content[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    doc_id=document.doc_id,
                    chunk_index=chunk_index,
                    metadata={
                        "source": document.source,
                        "type": "markdown",
                        "header": match.group(0).strip(),
                    },
                ))
                chunk_index += 1
        
        return chunks
    
    def _split_large_chunk(
        self,
        text: str,
        doc_id: str,
        start_index: int,
        source: str,
    ) -> List[Chunk]:
        """Split a large chunk into smaller pieces."""
        chunks = []
        start = 0
        chunk_index = start_index
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to find line break
            if end < len(text):
                newline_pos = text.rfind('\n', start, end)
                if newline_pos > start:
                    end = newline_pos + 1
            
            chunks.append(Chunk(
                text=text[start:end],
                doc_id=doc_id,
                chunk_index=chunk_index,
                metadata={"source": source, "type": "code"},
            ))
            
            chunk_index += 1
            start = end
        
        return chunks


class RAGPipeline:
    """LlamaIndex-based RAG Pipeline.
    
    Provides document ingestion, chunking, indexing, and retrieval.
    
    Example:
        pipeline = RAGPipeline(session_id="sess_123")
        await pipeline.initialize()
        
        # Ingest document
        doc = Document(content="...", source="readme.md", doc_type="markdown")
        await pipeline.ingest_document(doc)
        
        # Query
        results = await pipeline.query("What is the architecture?")
    """
    
    def __init__(
        self,
        session_id: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        self.session_id = session_id
        self.chunker = DocumentChunker(chunk_size, chunk_overlap)
        self._initialized = False
        self._index: Any = None  # LlamaIndex index
        self._embed_model: Any = None
        self._vector_store: Any = None
    
    async def initialize(self) -> None:
        """Initialize the RAG pipeline."""
        try:
            from llama_index.core import Settings, VectorStoreIndex
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            from llama_index.vector_stores.lancedb import LanceDBVectorStore
            
            # Initialize embedding model
            self._embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            Settings.embed_model = self._embed_model
            
            # Initialize vector store
            uri = str(Path(settings.LANCEDB_URI).expanduser())
            self._vector_store = LanceDBVectorStore(
                uri=uri,
                table_name=f"rag_{self.session_id}",
            )
            
            # Create or load index
            try:
                self._index = VectorStoreIndex.from_vector_store(
                    vector_store=self._vector_store,
                )
            except Exception:
                # New index
                self._index = None
            
            self._initialized = True
            
        except ImportError as e:
            raise RuntimeError(
                f"LlamaIndex not installed. Install with: pip install llama-index"
            ) from e
    
    async def ingest_document(self, document: Document) -> List[str]:
        """Ingest a document into the RAG pipeline.
        
        Args:
            document: Document to ingest
            
        Returns:
            List of chunk IDs
        """
        if not self._initialized:
            raise RuntimeError("RAG pipeline not initialized")
        
        from llama_index.core import Document as LlamaDocument
        from llama_index.core.node_parser import SentenceSplitter
        
        # Chunk document
        chunks = self.chunker.chunk(document)
        
        # Convert to LlamaIndex documents
        llama_docs = []
        for chunk in chunks:
            llama_docs.append(LlamaDocument(
                text=chunk.text,
                doc_id=f"{chunk.doc_id}_{chunk.chunk_index}",
                metadata={
                    **chunk.metadata,
                    "session_id": self.session_id,
                    "doc_id": chunk.doc_id,
                    "chunk_index": chunk.chunk_index,
                },
            ))
        
        # Add to index
        if self._index is None:
            from llama_index.core import VectorStoreIndex
            self._index = VectorStoreIndex.from_documents(
                llama_docs,
                vector_store=self._vector_store,
            )
        else:
            for doc in llama_docs:
                self._index.insert(doc)
        
        return [d.doc_id for d in llama_docs]
    
    async def ingest_file(self, file_path: Union[str, Path]) -> List[str]:
        """Ingest a file into the RAG pipeline.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of chunk IDs
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine document type
        suffix = path.suffix.lower()
        if suffix in ['.py']:
            doc_type = "python"
        elif suffix in ['.js', '.ts', '.jsx', '.tsx']:
            doc_type = "javascript"
        elif suffix in ['.md', '.markdown']:
            doc_type = "markdown"
        elif suffix in ['.json']:
            doc_type = "json"
        elif suffix in ['.yaml', '.yml']:
            doc_type = "yaml"
        else:
            doc_type = "text"
        
        # Read content
        content = path.read_text(encoding='utf-8')
        
        # Create document
        document = Document(
            content=content,
            source=str(path),
            doc_type=doc_type,
            metadata={
                "file_size": path.stat().st_size,
                "modified": path.stat().st_mtime,
            },
        )
        
        return await self.ingest_document(document)
    
    async def query(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query the RAG pipeline.
        
        Args:
            query_text: Query text
            top_k: Number of results
            filters: Optional filters
            
        Returns:
            List of results with text and score
        """
        if not self._initialized:
            raise RuntimeError("RAG pipeline not initialized")
        
        if self._index is None:
            return []
        
        # Create retriever
        retriever = self._index.as_retriever(similarity_top_k=top_k)
        
        # Query
        nodes = retriever.retrieve(query_text)
        
        results = []
        for node in nodes:
            results.append({
                "text": node.text,
                "score": float(node.score) if hasattr(node, 'score') else 0.0,
                "source": node.metadata.get("source", "unknown"),
                "type": node.metadata.get("type", "text"),
                "metadata": node.metadata,
            })
        
        return results
    
    async def query_with_context(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Query with full context building.
        
        Returns query results with formatted context for LLM consumption.
        """
        results = await self.query(query_text, top_k)
        
        # Build context string
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[{i}] Source: {result['source']}\n"
                f"Content: {result['text'][:500]}...\n"
            )
        
        context = "\n".join(context_parts)
        
        return {
            "query": query_text,
            "results": results,
            "context": context,
            "sources": list(set(r["source"] for r in results)),
        }
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index."""
        # Note: LanceDB doesn't support easy deletion by metadata
        # This is a placeholder for future implementation
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        if not self._initialized or self._index is None:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "session_id": self.session_id,
            "chunk_size": self.chunker.chunk_size,
            "chunk_overlap": self.chunker.chunk_overlap,
        }
