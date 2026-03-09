"""Knowledge graph builder using LLM-based open information extraction.

This module implements HippoRAG-style knowledge graph construction,
extracting (subject, relation, object) triples from text using LLM.
"""

import json
import re
from typing import Any, Dict, List, Optional, Protocol

from memnexus.memory.core.types import Triple


class LLMClient(Protocol):
    """Protocol for LLM client interface.

    Any LLM client that implements this protocol can be used with
    KnowledgeGraphBuilder for triple extraction.
    """

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from the LLM.

        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """
        ...


class KnowledgeGraphBuilder:
    """Build knowledge graphs by extracting triples from text using LLM.

    Implements open-domain information extraction (no predefined schema)
    as described in HippoRAG. Extracts (subject, relation, object) triples
    from unstructured text for knowledge graph construction.

    Attributes:
        llm_client: LLM client for triple extraction
        extraction_prompt: Prompt template for extraction
        confidence_threshold: Minimum confidence for filtering triples

    Example:
        >>> builder = KnowledgeGraphBuilder(llm_client=openai_client)
        >>> triples = await builder.extract_triples(
        ...     "Python is a programming language created by Guido van Rossum."
        ... )
        >>> print(triples[0])
        Triple(Python --[is a]--> programming language, conf=0.95)
    """

    DEFAULT_PROMPT = """Extract all factual relationships from the following text as structured triples.

A triple consists of:
- Subject: The main entity or concept
- Relation: The relationship or action connecting subject to object  
- Object: The target entity, concept, or value
- Confidence: Your confidence in this extraction (0.0 to 1.0)

Guidelines:
1. Extract ALL relevant facts, not just the main ones
2. Use clear, concise relations (e.g., "is a", "created by", "requires", "located in")
3. Normalize entity names (e.g., "Python" not "the Python language")
4. Set confidence based on clarity and explicitness of the relationship
5. Return ONLY valid JSON in the specified format

Text to analyze:
```
{text}
```

Return your response as JSON with this exact structure:
{{
    "triples": [
        {{
            "subject": "entity name",
            "relation": "relationship",
            "object": "target entity",
            "confidence": 0.95
        }}
    ]
}}

If no clear relationships can be extracted, return: {{"triples": []}}"""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        extraction_prompt: Optional[str] = None,
        confidence_threshold: float = 0.5,
    ):
        """Initialize the knowledge graph builder.

        Args:
            llm_client: LLM client for triple extraction. If None, must be
                set before calling extract methods.
            extraction_prompt: Custom prompt template. Uses DEFAULT_PROMPT if None.
            confidence_threshold: Minimum confidence score for triples (0.0-1.0).
                Triples below this threshold are filtered out.
        """
        self.llm_client = llm_client
        self.extraction_prompt = extraction_prompt or self.DEFAULT_PROMPT
        self.confidence_threshold = confidence_threshold

    async def extract_triples(self, text: str) -> List[Triple]:
        """Extract triples from a single text using LLM.

        Uses the configured LLM client to perform open information extraction,
        returning a list of Triple objects with confidence scores.

        Args:
            text: Input text to analyze

        Returns:
            List of extracted Triple objects, filtered by confidence threshold

        Raises:
            RuntimeError: If no LLM client is configured
            ValueError: If LLM response cannot be parsed
        """
        if self.llm_client is None:
            raise RuntimeError(
                "LLM client not configured. Provide llm_client in constructor "
                "or set it before calling extract_triples()"
            )

        if not text or not text.strip():
            return []

        # Prepare prompt
        prompt = self.extraction_prompt.format(text=text.strip())

        # Call LLM
        response = await self.llm_client.generate(prompt)

        # Parse and validate triples
        triples = self._parse_triples(response, source_text=text)

        # Filter by confidence threshold
        return [t for t in triples if t.confidence >= self.confidence_threshold]

    async def extract_triples_batch(
        self,
        texts: List[str],
        batch_size: int = 10,
    ) -> List[List[Triple]]:
        """Extract triples from multiple texts in batches.

        Processes texts sequentially to avoid overwhelming the LLM API.
        For production use with high volume, consider implementing
        parallel processing with rate limiting.

        Args:
            texts: List of input texts to analyze
            batch_size: Number of texts to process in each batch (for progress tracking)

        Returns:
            List of triple lists, one per input text

        Example:
            >>> texts = [
            ...     "Python is a programming language.",
            ...     "FastAPI is a web framework.",
            ... ]
            >>> results = await builder.extract_triples_batch(texts)
            >>> len(results)
            2
        """
        results = []

        for i, text in enumerate(texts):
            triples = await self.extract_triples(text)
            results.append(triples)

            # Simple progress indicator (could be replaced with proper logging)
            if (i + 1) % batch_size == 0:
                pass  # Progress logging could go here

        return results

    def _parse_triples(self, response: str, source_text: Optional[str] = None) -> List[Triple]:
        """Parse LLM response into Triple objects.

        Attempts to extract JSON from the response, handling common
        formatting issues like markdown code blocks.

        Args:
            response: Raw LLM response text
            source_text: Original source text for metadata

        Returns:
            List of parsed Triple objects

        Raises:
            ValueError: If response cannot be parsed as valid triples
        """
        # Clean up response - extract JSON from markdown code blocks if present
        cleaned = self._extract_json(response)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse LLM response as JSON: {e}\nResponse: {response[:200]}"
            )

        # Handle both {"triples": [...]} and direct list formats
        if isinstance(data, dict) and "triples" in data:
            triples_data = data["triples"]
        elif isinstance(data, list):
            triples_data = data
        else:
            raise ValueError(
                f"Unexpected response format. Expected 'triples' key or list, got: {type(data)}"
            )

        if not isinstance(triples_data, list):
            raise ValueError(f"Expected 'triples' to be a list, got: {type(triples_data)}")

        # Convert to Triple objects
        triples = []
        for item in triples_data:
            if not isinstance(item, dict):
                continue

            # Validate required fields
            required = ["subject", "relation", "object"]
            if not all(k in item for k in required):
                continue

            # Create Triple with metadata
            triple = Triple(
                subject=str(item["subject"]).strip(),
                relation=str(item["relation"]).strip(),
                obj=str(item["object"]).strip(),
                confidence=float(item.get("confidence", 1.0)),
                source_text=source_text,
                metadata={
                    "extraction_method": "llm",
                    "raw_response": item,
                },
            )
            triples.append(triple)

        return triples

    def _extract_json(self, text: str) -> str:
        """Extract JSON content from text, handling markdown code blocks.

        Args:
            text: Raw text that may contain JSON

        Returns:
            Cleaned JSON string
        """
        # Try to find JSON in markdown code blocks
        patterns = [
            r"```json\s*(.*?)\s*```",  # ```json ... ```
            r"```\s*(.*?)\s*```",  # ``` ... ```
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Try to find JSON object/array directly
        # Look for balanced braces
        for start_char in ["{", "["]:
            start_idx = text.find(start_char)
            if start_idx != -1:
                # Find matching end
                count = 0
                end_idx = start_idx
                for i, char in enumerate(text[start_idx:]):
                    if char == start_char:
                        count += 1
                    elif char == ("}" if start_char == "{" else "]"):
                        count -= 1
                        if count == 0:
                            end_idx = start_idx + i + 1
                            break

                if end_idx > start_idx:
                    return text[start_idx:end_idx].strip()

        # Return original if no JSON found
        return text.strip()

    def set_llm_client(self, llm_client: LLMClient) -> "KnowledgeGraphBuilder":
        """Set or update the LLM client.

        Args:
            llm_client: New LLM client to use

        Returns:
            Self for method chaining
        """
        self.llm_client = llm_client
        return self

    def with_confidence_threshold(self, threshold: float) -> "KnowledgeGraphBuilder":
        """Set confidence threshold with method chaining.

        Args:
            threshold: New confidence threshold (0.0-1.0)

        Returns:
            Self for method chaining

        Example:
            >>> builder = KnowledgeGraphBuilder(llm_client)
            ...     .with_confidence_threshold(0.8)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        self.confidence_threshold = threshold
        return self


# Simple built-in LLM client implementations for common providers


class OpenAIClient:
    """OpenAI API client wrapper for KnowledgeGraphBuilder."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            model: Model to use for generation
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "OpenAI client requires 'openai' package. Install with: pip install openai"
            )

        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens", 2000),
        )
        return response.choices[0].message.content or ""


class AnthropicClient:
    """Anthropic API client wrapper for KnowledgeGraphBuilder."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
            model: Model to use for generation
        """
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "Anthropic client requires 'anthropic' package. Install with: pip install anthropic"
            )

        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using Anthropic API."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.0),
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text if response.content else ""
