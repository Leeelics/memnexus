"""Base classes for benchmark system.

Provides standardized data structures and interfaces for all benchmark datasets.
Inspired by OpenViking's RAG benchmark design.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
from abc import ABC, abstractmethod
from pathlib import Path


@dataclass
class StandardQA:
    """Standardized QA pair structure.

    Attributes:
        question: The query text
        gold_answers: List of acceptable answers
        evidence: List of expected evidence/retrieval targets
        category: Question category/type
        metadata: Additional information (file paths, line numbers, etc.)
    """

    question: str
    gold_answers: List[str]
    evidence: List[str] = field(default_factory=list)
    category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StandardSample:
    """Standardized sample structure containing multiple QA pairs.

    Attributes:
        sample_id: Unique identifier (e.g., file path, commit hash)
        qa_pairs: List of QA pairs for this sample
        context: Optional context information (file content, commit message, etc.)
    """

    sample_id: str
    qa_pairs: List[StandardQA]
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of a benchmark task.

    Attributes:
        task_name: Name of the benchmark task
        metrics: Dictionary of metric names to values
        duration_seconds: Time taken to run the task
        metadata: Additional result information
    """

    task_name: str
    metrics: Dict[str, Any]
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "task_name": self.task_name,
            "metrics": self.metrics,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


class BaseAdapter(ABC):
    """Base adapter interface for all benchmark datasets.

    All real dataset adapters must implement this interface.
    """

    def __init__(self, raw_data_path: str, logger=None):
        self.raw_data_path = Path(raw_data_path)
        self.logger = logger

    @abstractmethod
    def load_and_transform(self) -> List[StandardSample]:
        """Load raw data and convert to standardized format.

        Returns:
            List of StandardSample objects
        """
        pass

    @abstractmethod
    def get_expected_evidence(self, qa: StandardQA) -> List[str]:
        """Get expected evidence for a QA pair.

        Used for retrieval quality evaluation.

        Returns:
            List of evidence identifiers (file paths, commit hashes, etc.)
        """
        pass


# Question categories for code memory evaluation
class QuestionCategory:
    """Standard question categories for code memory benchmark."""

    # Code understanding
    FUNCTION_PURPOSE = "function_purpose"  # What does this function do?
    CODE_EXPLANATION = "code_explanation"  # Explain this code

    # Code location
    FIND_DEFINITION = "find_definition"  # Where is X defined?
    FIND_USAGE = "find_usage"  # Where is X used?

    # Code history
    CHANGE_HISTORY = "change_history"  # What changed in X?
    WHO_CHANGED = "who_changed"  # Who modified X?
    WHEN_CHANGED = "when_changed"  # When was X modified?

    # Code relationships
    DEPENDENCIES = "dependencies"  # What does X depend on?
    DEPENDENTS = "dependents"  # What depends on X?

    # Code comparison
    BEFORE_AFTER = "before_after"  # What changed between versions?

    @classmethod
    def get_description(cls, category: str) -> str:
        """Get human-readable description for category."""
        descriptions = {
            cls.FUNCTION_PURPOSE: "Understanding what a function or class does",
            cls.CODE_EXPLANATION: "Explaining code behavior or logic",
            cls.FIND_DEFINITION: "Locating where something is defined",
            cls.FIND_USAGE: "Finding where something is used",
            cls.CHANGE_HISTORY: "Understanding what changed and why",
            cls.WHO_CHANGED: "Identifying who made changes",
            cls.WHEN_CHANGED: "Determining when changes were made",
            cls.DEPENDENCIES: "Finding dependencies of a component",
            cls.DEPENDENTS: "Finding what depends on a component",
            cls.BEFORE_AFTER: "Comparing code across versions",
        }
        return descriptions.get(category, "Unknown category")


# Category-specific instructions for LLM evaluation
CATEGORY_INSTRUCTIONS = {
    QuestionCategory.FUNCTION_PURPOSE: """Answer what the function/class does based on:
- Function signature and docstring
- Implementation logic
- Usage patterns in the codebase

Be specific about inputs, outputs, and behavior.""",
    QuestionCategory.CODE_EXPLANATION: """Explain the code behavior:
- What does this code do step by step?
- What are the key logic flows?
- What are edge cases handled?

Provide a clear, structured explanation.""",
    QuestionCategory.FIND_DEFINITION: """Locate the exact definition:
- Provide file path and line number
- Show the complete definition
- Include any relevant context

Be precise about location.""",
    QuestionCategory.FIND_USAGE: """Find all usages:
- List all files where this is used
- Show usage patterns
- Include import statements

Be comprehensive but concise.""",
    QuestionCategory.CHANGE_HISTORY: """Summarize the change history:
- What was changed?
- Why was it changed (if commit message explains)?
- When did the change occur?

Focus on significant changes.""",
}
