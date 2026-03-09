"""Knowledge graph module for HippoRAG-style memory enhancement.

This module provides tools for building and managing knowledge graphs
using LLM-based open information extraction, enabling multi-hop
reasoning for RAG applications.

Example:
    >>> from memnexus.memory.knowledge_graph import KnowledgeGraphBuilder
    >>> builder = KnowledgeGraphBuilder(llm_client=client)
    >>> triples = await builder.extract_triples("Python is a programming language.")
"""

from memnexus.memory.knowledge_graph.builder import (
    AnthropicClient,
    KnowledgeGraphBuilder,
    LLMClient,
    OpenAIClient,
)

__all__ = [
    "AnthropicClient",
    "KnowledgeGraphBuilder",
    "LLMClient",
    "OpenAIClient",
]
