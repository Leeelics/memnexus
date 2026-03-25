"""Git integration for code memory.

Extracts commit history and code changes from Git repositories
to build a searchable memory of project evolution.

Week 2 Implementation Target:
- Extract commit history with messages and diffs
- Index code changes over time
- Enable queries like "what changed in auth module recently"
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class GitCommit:
    """Represents a Git commit."""
    hash: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]
    diff_summary: str


class GitMemoryExtractor:
    """Extracts Git history for memory indexing.
    
    Week 2 Implementation.
    
    Example:
        >>> extractor = GitMemoryExtractor("/path/to/repo")
        >>> commits = extractor.extract_recent("auth/login.py", limit=10)
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def extract_recent(self, file_path: Optional[str] = None, limit: int = 100) -> List[GitCommit]:
        """Extract recent commits.
        
        Args:
            file_path: Optional file to filter commits by
            limit: Maximum number of commits to extract
            
        Returns:
            List of GitCommit objects
            
        Note:
            Week 2 Implementation - currently returns empty list
        """
        # TODO: Week 2 - Implement using gitpython
        return []
    
    def extract_file_history(self, file_path: str) -> List[GitCommit]:
        """Extract full history for a specific file.
        
        Args:
            file_path: Path to file (relative to repo root)
            
        Returns:
            List of commits affecting this file
            
        Note:
            Week 2 Implementation - currently returns empty list
        """
        # TODO: Week 2 - Implement
        return []
