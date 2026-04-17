"""Base adapter for real dataset integration."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import sys

# Handle both relative and absolute imports
try:
    from core.base import StandardSample, StandardQA
except ImportError:
    from ..core.base import StandardSample, StandardQA


class BaseAdapter(ABC):
    """Base adapter interface for all benchmark datasets."""

    def __init__(self, raw_data_path: str, logger: Optional[logging.Logger] = None):
        self.raw_data_path = Path(raw_data_path)
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def load_and_transform(self) -> List[StandardSample]:
        """Load raw data and convert to standardized format."""
        pass

    @abstractmethod
    def get_expected_evidence(self, qa: StandardQA) -> List[str]:
        """Get expected evidence for a QA pair."""
        pass

    def validate(self) -> bool:
        """Validate that the raw data exists and is readable."""
        if not self.raw_data_path.exists():
            self.logger.error(f"Raw data path does not exist: {self.raw_data_path}")
            return False
        return True
