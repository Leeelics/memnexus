"""Code retrieval benchmark task.

Evaluates the quality of code symbol search.

Example:
    >>> task = CodeRetrievalTask("code_retrieval", project_path="./my-project")
    >>> result = await task.run(dataset)
    >>> print(f"Recall@5: {result.metrics['recall@5']:.4f}")
"""

import sys
import tempfile
from pathlib import Path
from typing import Any

# Add src to path for importing memnexus
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from benchmark.core.base import BenchmarkResult, BenchmarkTask, Dataset
from benchmark.datasets.synthetic import CodeBenchmarkDataset
from benchmark.metrics.ranking import compute_ranking_metrics
from benchmark.metrics.retrieval import compute_metrics_at_k


class CodeRetrievalTask(BenchmarkTask):
    """Benchmark task for code symbol retrieval.

    Measures how well the system can retrieve relevant code symbols
    (functions, classes, methods) based on semantic queries.

    Metrics:
        - Recall@K: Can we find the relevant symbols?
        - Precision@K: Are the top results relevant?
        - NDCG@K: Are relevant symbols ranked highly?
        - MRR: How early is the first relevant symbol?
    """

    def __init__(
        self,
        name: str,
        project_path: str | None = None,
        k_values: list[int] | None = None,
        **kwargs: Any,
    ):
        super().__init__(name, **kwargs)
        self.project_path = project_path
        self.k_values = k_values or [1, 3, 5, 10]
        self._memory = None
        self._dataset = None
        self._temp_dir = None

    def setup(self) -> None:
        """Setup: Create synthetic codebase and initialize CodeMemory."""
        from memnexus import CodeMemory

        print("[CodeRetrievalTask] Setting up...")

        # Create temporary directory for synthetic codebase
        self._temp_dir = tempfile.mkdtemp(prefix="memnexus_benchmark_")
        repo_path = Path(self._temp_dir) / "codebase"
        repo_path.mkdir(parents=True, exist_ok=True)

        # Initialize Git repo (required for CodeMemory)
        import subprocess

        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "benchmark@memnexus.local"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Benchmark Bot"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )

        # Create synthetic Python files
        print("[CodeRetrievalTask] Creating synthetic codebase...")
        self._create_codebase(repo_path)

        # Create dataset
        self._dataset = CodeBenchmarkDataset.create_synthetic()
        print(f"[CodeRetrievalTask] Dataset: {len(self._dataset)} queries")

        # Initialize CodeMemory
        print("[CodeRetrievalTask] Initializing CodeMemory...")
        memnexus_dir = repo_path / ".memnexus"
        memnexus_dir.mkdir(exist_ok=True)

        # Create minimal config
        config_path = memnexus_dir / "config.yaml"
        config_path.write_text("embedding:\n  method: tfidf\n  dim: 384\n")

        self._memory = CodeMemory(str(repo_path))

    def _create_codebase(self, repo_path: Path) -> None:
        """Create synthetic Python codebase."""
        src_dir = repo_path / "src"
        src_dir.mkdir(exist_ok=True)

        # auth.py
        auth_code = """
def authenticate_user(username: str, password: str) -> dict:
    \"\"\"Authenticate a user with username and password.

    Args:
        username: The username
        password: The password

    Returns:
        Dictionary with user info and token
    \"\"\"
    return {"user": username, "token": "abc123"}

def hash_password(password: str) -> str:
    \"\"\"Hash a password securely.\"\"\"
    return f"hashed_{password}"

def verify_password(password: str, hashed: str) -> bool:
    \"\"\"Verify a password against its hash.\"\"\"
    return hash_password(password) == hashed

def generate_token(user_id: str) -> str:
    \"\"\"Generate a JWT token for a user.\"\"\"
    return f"token_{user_id}"

def verify_token(token: str) -> dict:
    \"\"\"Verify a JWT token.\"\"\"
    return {"valid": True}

class AuthManager:
    \"\"\"Manager for authentication operations.\"\"\"

    def login(self, username: str, password: str) -> dict:
        \"\"\"Handle user login.\"\"\"
        return authenticate_user(username, password)

    def logout(self, token: str) -> bool:
        \"\"\"Handle user logout.\"\"\"
        return True
"""
        (src_dir / "auth.py").write_text(auth_code)

        # db.py
        db_code = """
class DatabasePool:
    \"\"\"Database connection pool for managing connections.\"\"\"

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._pool = []

    def get_connection(self):
        \"\"\"Get a connection from the pool.\"\"\"
        return None

    def release_connection(self, conn) -> None:
        \"\"\"Release a connection back to the pool.\"\"\"
        pass

def query_optimizer(query: str) -> str:
    \"\"\"Optimize a database query for better performance.\"\"\"
    return query
"""
        (src_dir / "db.py").write_text(db_code)

        # middleware.py
        middleware_code = """
class RateLimiter:
    \"\"\"Rate limiting middleware for API requests.\"\"\"

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute

    def is_allowed(self, client_id: str) -> bool:
        \"\"\"Check if request is within rate limit.\"\"\"
        return True

class LoggingMiddleware:
    \"\"\"Middleware for logging requests.\"\"\"

    def log_request(self, request: dict) -> None:
        \"\"\"Log an incoming request.\"\"\"
        pass
"""
        (src_dir / "middleware.py").write_text(middleware_code)

        # validation.py
        validation_code = """
def validate_email(email: str) -> bool:
    \"\"\"Validate email format.\"\"\"
    return "@" in email

def validate_password(password: str) -> bool:
    \"\"\"Validate password strength.\"\"\"
    return len(password) >= 8

class EmailValidator:
    \"\"\"Validator for email addresses.\"\"\"

    def validate(self, email: str) -> bool:
        \"\"\"Validate an email address.\"\"\"
        return validate_email(email)
"""
        (src_dir / "validation.py").write_text(validation_code)

        # cache.py
        cache_code = """
class Cache:
    \"\"\"Simple in-memory cache implementation.\"\"\"

    def __init__(self):
        self._data = {}

    def get(self, key: str):
        \"\"\"Get value from cache.\"\"\"
        return self._data.get(key)

    def set(self, key: str, value) -> None:
        \"\"\"Set value in cache.\"\"\"
        self._data[key] = value

    def clear(self) -> None:
        \"\"\"Clear all cached values.\"\"\"
        self._data.clear()
"""
        (src_dir / "cache.py").write_text(cache_code)

    async def run(self, dataset: Dataset | None = None) -> BenchmarkResult:
        """Run the code retrieval benchmark.

        Args:
            dataset: Optional dataset (uses self._dataset if not provided)

        Returns:
            BenchmarkResult with retrieval metrics
        """
        self.ensure_setup()

        # Use provided dataset or the one created during setup
        if dataset is None:
            dataset = self._dataset

        if dataset is None or len(dataset) == 0:
            return BenchmarkResult(
                task_name=self.name,
                metrics={"error": 1.0, "message": "No dataset available"},
            )

        # Initialize memory (async)
        await self._memory._initialize()

        # Index codebase
        print("[CodeRetrievalTask] Indexing codebase...")
        index_result = await self._memory.index_codebase(incremental=False)
        print(f"[CodeRetrievalTask] Indexed {index_result['symbols_indexed']} symbols")

        # Run queries and collect results
        print(f"[CodeRetrievalTask] Running {len(dataset.queries)} queries...")
        query_results = []

        for query_data in dataset.queries:
            query = query_data["query"]
            expected = query_data["expected"]

            # Search code
            code_results = await self._memory.search_code(query, limit=max(self.k_values))

            # Extract retrieved symbol IDs (file_path:symbol_name)
            retrieved = []
            for r in code_results:
                metadata = r.metadata or {}
                file_path = metadata.get("file_path", "")
                symbol_name = metadata.get("symbol_name", "")
                if file_path and symbol_name:
                    # Normalize path
                    symbol_id = f"{Path(file_path).name}:{symbol_name}"
                    retrieved.append(symbol_id)

            # Compute metrics for this query
            metrics = compute_metrics_at_k(expected, retrieved, self.k_values)
            ranking_metrics = compute_ranking_metrics(expected, retrieved, self.k_values)
            metrics.update(ranking_metrics)

            query_results.append(
                {
                    "query": query,
                    "expected": expected,
                    "retrieved": retrieved,
                    "metrics": metrics,
                }
            )

        # Aggregate metrics across all queries
        aggregated_metrics = self._aggregate_metrics(query_results)
        aggregated_metrics["num_queries"] = len(query_results)
        aggregated_metrics["symbols_indexed"] = index_result["symbols_indexed"]

        return BenchmarkResult(
            task_name=self.name,
            metrics=aggregated_metrics,
            raw_results=query_results,
            metadata={
                "k_values": self.k_values,
                "dataset_size": len(dataset),
            },
        )

    def _aggregate_metrics(self, query_results: list[dict]) -> dict[str, float]:
        """Aggregate metrics across all queries."""
        if not query_results:
            return {}

        # Collect all metric names
        metric_names = set()
        for qr in query_results:
            metric_names.update(qr["metrics"].keys())

        # Compute averages
        aggregated = {}
        for metric_name in metric_names:
            values = [
                qr["metrics"][metric_name] for qr in query_results if metric_name in qr["metrics"]
            ]
            if values:
                aggregated[metric_name] = sum(values) / len(values)

        return aggregated

    def teardown(self) -> None:
        """Cleanup resources."""
        import shutil

        if self._temp_dir and Path(self._temp_dir).exists():
            print("[CodeRetrievalTask] Cleaning up temporary directory...")
            shutil.rmtree(self._temp_dir, ignore_errors=True)

        if self._memory:
            # Close memory if needed
            pass
