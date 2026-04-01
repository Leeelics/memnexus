"""Synthetic dataset generation for benchmarking.

Generates synthetic Git repositories and codebases with known ground truth
for evaluating retrieval quality.

Example:
    >>> generator = SyntheticRepoGenerator("./test_repo")
    >>> generator.create_repo()
    >>> generator.add_commits_with_queries()
"""

import os
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class SyntheticRepoGenerator:
    """Generator for synthetic Git repositories.

    Creates a Git repository with commits that have known relationships
    to specific queries for evaluation purposes.

    Example:
        >>> generator = SyntheticRepoGenerator("./benchmark_repo")
        >>> generator.create_repo()
        >>> generator.add_feature_commits()
        >>> generator.add_bugfix_commits()
    """

    # Query templates mapped to commit message patterns
    QUERY_COMMIT_PATTERNS = {
        "user authentication": [
            ("feat: add user login endpoint", "authentication"),
            ("feat: implement JWT token generation", "authentication"),
            ("feat: add password hashing", "authentication"),
            ("fix: resolve auth token expiration bug", "authentication"),
        ],
        "database connection": [
            ("feat: add database connection pool", "database"),
            ("feat: implement connection retry logic", "database"),
            ("refactor: optimize db query performance", "database"),
            ("fix: handle database timeout", "database"),
        ],
        "API rate limiting": [
            ("feat: implement rate limiting middleware", "rate_limit"),
            ("feat: add redis-based rate limiter", "rate_limit"),
            ("fix: correct rate limit headers", "rate_limit"),
        ],
        "error handling": [
            ("feat: add global exception handler", "error_handling"),
            ("feat: implement custom error classes", "error_handling"),
            ("refactor: improve error messages", "error_handling"),
        ],
        "user registration": [
            ("feat: add user signup endpoint", "registration"),
            ("feat: implement email verification", "registration"),
            ("fix: validate password strength", "registration"),
        ],
    }

    def __init__(self, repo_path: str, seed: int = 42):
        self.repo_path = Path(repo_path)
        self.seed = seed
        random.seed(seed)
        self._commit_hashes: list[str] = []
        self._commit_tags: dict[str, str] = {}  # hash -> tag

    def create_repo(self) -> None:
        """Create a new Git repository."""
        self.repo_path.mkdir(parents=True, exist_ok=True)

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=self.repo_path,
            capture_output=True,
            check=True,
        )

        # Configure git user
        subprocess.run(
            ["git", "config", "user.email", "benchmark@memnexus.local"],
            cwd=self.repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Benchmark Bot"],
            cwd=self.repo_path,
            capture_output=True,
            check=True,
        )

    def add_commit(self, message: str, files: dict[str, str], date: datetime | None = None) -> str:
        """Add a commit to the repository.

        Args:
            message: Commit message
            files: Dictionary of {file_path: content}
            date: Optional commit date

        Returns:
            Commit hash
        """
        # Create files
        for file_path, content in files.items():
            full_path = self.repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            subprocess.run(
                ["git", "add", file_path],
                cwd=self.repo_path,
                capture_output=True,
                check=True,
            )

        # Commit
        env = os.environ.copy()
        if date:
            env["GIT_AUTHOR_DATE"] = date.isoformat()
            env["GIT_COMMITTER_DATE"] = date.isoformat()

        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            capture_output=True,
            env=env,
            check=True,
        )

        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()[:8]
        self._commit_hashes.append(commit_hash)

        return commit_hash

    def add_feature_commits(self) -> dict[str, list[str]]:
        """Add feature-related commits.

        Returns:
            Mapping of tags to commit hashes
        """
        base_date = datetime(2024, 1, 1)
        tag_commits = {}

        features = [
            ("feat: implement user authentication system", "auth.py", "authentication"),
            ("feat: add database connection pooling", "db.py", "database"),
            ("feat: implement API rate limiting", "middleware.py", "rate_limit"),
            ("feat: add request validation", "validation.py", "validation"),
            ("feat: implement caching layer", "cache.py", "caching"),
        ]

        for i, (message, filename, tag) in enumerate(features):
            content = self._generate_code_content(tag, filename)
            commit_hash = self.add_commit(
                message,
                {f"src/{filename}": content},
                date=base_date + timedelta(days=i),
            )
            self._commit_tags[commit_hash] = tag
            if tag not in tag_commits:
                tag_commits[tag] = []
            tag_commits[tag].append(commit_hash)

        return tag_commits

    def add_bugfix_commits(self) -> dict[str, list[str]]:
        """Add bug fix commits.

        Returns:
            Mapping of tags to commit hashes
        """
        base_date = datetime(2024, 1, 10)
        tag_commits = {}

        bugfixes = [
            ("fix: resolve authentication bypass vulnerability", "auth.py", "authentication"),
            ("fix: handle database connection timeout", "db.py", "database"),
            ("fix: correct rate limit calculation", "middleware.py", "rate_limit"),
            ("fix: validate email format in registration", "validation.py", "validation"),
            ("fix: clear cache on logout", "cache.py", "caching"),
        ]

        for i, (message, filename, tag) in enumerate(bugfixes):
            content = self._generate_code_content(tag, filename, is_fix=True)
            commit_hash = self.add_commit(
                message,
                {f"src/{filename}": content},
                date=base_date + timedelta(days=i),
            )
            self._commit_tags[commit_hash] = tag
            if tag not in tag_commits:
                tag_commits[tag] = []
            tag_commits[tag].append(commit_hash)

        return tag_commits

    def add_refactor_commits(self) -> dict[str, list[str]]:
        """Add refactoring commits.

        Returns:
            Mapping of tags to commit hashes
        """
        base_date = datetime(2024, 1, 20)
        tag_commits = {}

        refactors = [
            ("refactor: extract auth utilities", "auth.py", "authentication"),
            ("refactor: simplify database queries", "db.py", "database"),
            ("refactor: reorganize middleware structure", "middleware.py", "rate_limit"),
        ]

        for i, (message, filename, tag) in enumerate(refactors):
            content = self._generate_code_content(tag, filename, is_refactor=True)
            commit_hash = self.add_commit(
                message,
                {f"src/{filename}": content},
                date=base_date + timedelta(days=i),
            )
            self._commit_tags[commit_hash] = tag
            if tag not in tag_commits:
                tag_commits[tag] = []
            tag_commits[tag].append(commit_hash)

        return tag_commits

    def _generate_code_content(
        self, tag: str, filename: str, is_fix: bool = False, is_refactor: bool = False
    ) -> str:
        """Generate code content based on tag."""
        templates = {
            "authentication": """
def authenticate_user(username: str, password: str) -> dict:
    \"\"\"Authenticate a user with username and password.\"\"\"
    # Authentication logic here
    return {"user": username, "token": "abc123"}

def logout_user(token: str) -> bool:
    \"\"\"Logout a user by invalidating their token.\"\"\"
    return True
""",
            "database": """
class DatabasePool:
    \"\"\"Database connection pool.\"\"\"

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections

    def get_connection(self):
        \"\"\"Get a connection from the pool.\"\"\"
        pass
""",
            "rate_limit": """
class RateLimiter:
    \"\"\"Rate limiting middleware.\"\"\"

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute

    def is_allowed(self, client_id: str) -> bool:
        \"\"\"Check if request is within rate limit.\"\"\"
        return True
""",
            "validation": """
def validate_email(email: str) -> bool:
    \"\"\"Validate email format.\"\"\"
    return "@" in email

def validate_password(password: str) -> bool:
    \"\"\"Validate password strength.\"\"\"
    return len(password) >= 8
""",
            "caching": """
class Cache:
    \"\"\"Simple in-memory cache.\"\"\"

    def get(self, key: str) -> any:
        \"\"\"Get value from cache.\"\"\"
        return None

    def set(self, key: str, value: any) -> None:
        \"\"\"Set value in cache.\"\"\"
        pass

    def clear(self) -> None:
        \"\"\"Clear all cached values.\"\"\"
        pass
""",
        }

        content = templates.get(tag, "# Placeholder code\n")

        if is_fix:
            content += "\n# Fixed edge cases\n"
        elif is_refactor:
            content += "\n# Refactored for clarity\n"

        return content

    def get_commit_hash_by_tag(self, tag: str) -> list[str]:
        """Get all commit hashes with a specific tag."""
        return [h for h, t in self._commit_tags.items() if t == tag]

    def get_all_commits(self) -> list[str]:
        """Get all commit hashes."""
        return self._commit_hashes


class GitBenchmarkDataset:
    """Dataset for Git retrieval benchmarking.

    Contains queries with expected relevant commits.

    Example:
        >>> dataset = GitBenchmarkDataset.create_from_repo("./repo")
        >>> print(f"Queries: {len(dataset.queries)}")
    """

    def __init__(self, queries: list[dict[str, Any]], metadata: dict[str, Any] | None = None):
        self.queries = queries
        self.metadata = metadata or {}

    def __len__(self) -> int:
        return len(self.queries)

    @classmethod
    def create_from_generator(cls, generator: SyntheticRepoGenerator) -> "GitBenchmarkDataset":
        """Create dataset from a synthetic repo generator.

        Args:
            generator: SyntheticRepoGenerator with created repo

        Returns:
            GitBenchmarkDataset with queries and expected results
        """
        queries = []

        # Map query patterns to tags
        query_tag_mapping = {
            "用户认证功能": "authentication",
            "user authentication": "authentication",
            "登录系统": "authentication",
            "数据库连接": "database",
            "database connection": "database",
            "API 限流": "rate_limit",
            "rate limiting": "rate_limit",
            "缓存系统": "caching",
            "caching layer": "caching",
        }

        for query_text, tag in query_tag_mapping.items():
            relevant_commits = generator.get_commit_hash_by_tag(tag)
            if relevant_commits:
                queries.append(
                    {
                        "query": query_text,
                        "expected": [{"id": h, "relevance": 1.0} for h in relevant_commits],
                        "metadata": {
                            "tag": tag,
                            "language": "zh" if "\u4e00" <= query_text[0] <= "\u9fff" else "en",
                        },
                    }
                )

        return cls(
            queries,
            metadata={"source": "synthetic", "num_commits": len(generator.get_all_commits())},
        )


class CodeBenchmarkDataset:
    """Dataset for code retrieval benchmarking.

    Contains queries with expected relevant code symbols.

    Example:
        >>> dataset = CodeBenchmarkDataset.create_synthetic()
        >>> print(f"Queries: {len(dataset.queries)}")
    """

    def __init__(self, queries: list[dict[str, Any]], metadata: dict[str, Any] | None = None):
        self.queries = queries
        self.metadata = metadata or {}

    def __len__(self) -> int:
        return len(self.queries)

    @classmethod
    def create_synthetic(cls) -> "CodeBenchmarkDataset":
        """Create a synthetic code retrieval dataset.

        Returns:
            CodeBenchmarkDataset with code retrieval queries
        """
        queries = [
            {
                "query": "authenticate user function",
                "expected": [
                    {"id": "auth.py:authenticate_user", "relevance": 1.0},
                    {"id": "auth.py:AuthManager.login", "relevance": 0.8},
                ],
                "metadata": {"symbol_type": "function"},
            },
            {
                "query": "database connection pool",
                "expected": [
                    {"id": "db.py:DatabasePool", "relevance": 1.0},
                    {"id": "db.py:DatabasePool.get_connection", "relevance": 0.9},
                ],
                "metadata": {"symbol_type": "class"},
            },
            {
                "query": "rate limiter middleware",
                "expected": [
                    {"id": "middleware.py:RateLimiter", "relevance": 1.0},
                    {"id": "middleware.py:RateLimiter.is_allowed", "relevance": 0.9},
                ],
                "metadata": {"symbol_type": "class"},
            },
            {
                "query": "email validation",
                "expected": [
                    {"id": "validation.py:validate_email", "relevance": 1.0},
                    {"id": "validation.py:EmailValidator", "relevance": 0.8},
                ],
                "metadata": {"symbol_type": "function"},
            },
            {
                "query": "cache implementation",
                "expected": [
                    {"id": "cache.py:Cache", "relevance": 1.0},
                    {"id": "cache.py:Cache.get", "relevance": 0.8},
                    {"id": "cache.py:Cache.set", "relevance": 0.8},
                ],
                "metadata": {"symbol_type": "class"},
            },
            {
                "query": "用户登录",
                "expected": [
                    {"id": "auth.py:authenticate_user", "relevance": 1.0},
                    {"id": "auth.py:login", "relevance": 0.9},
                ],
                "metadata": {"symbol_type": "function", "language": "zh"},
            },
            {
                "query": "数据库查询优化",
                "expected": [
                    {"id": "db.py:DatabasePool", "relevance": 0.9},
                    {"id": "db.py:query_optimizer", "relevance": 1.0},
                ],
                "metadata": {"symbol_type": "function", "language": "zh"},
            },
            {
                "query": "password hashing",
                "expected": [
                    {"id": "auth.py:hash_password", "relevance": 1.0},
                    {"id": "auth.py:verify_password", "relevance": 0.9},
                ],
                "metadata": {"symbol_type": "function"},
            },
            {
                "query": "JWT token generation",
                "expected": [
                    {"id": "auth.py:generate_token", "relevance": 1.0},
                    {"id": "auth.py:verify_token", "relevance": 0.8},
                ],
                "metadata": {"symbol_type": "function"},
            },
            {
                "query": "request logging middleware",
                "expected": [
                    {"id": "middleware.py:LoggingMiddleware", "relevance": 1.0},
                    {"id": "middleware.py:log_request", "relevance": 0.9},
                ],
                "metadata": {"symbol_type": "class"},
            },
        ]

        return cls(queries, metadata={"source": "synthetic", "num_queries": len(queries)})
