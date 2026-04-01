"""Indexing performance benchmark task.

Evaluates the performance of Git and code indexing operations.

Example:
    >>> task = IndexingPerformanceTask("indexing")
    >>> result = await task.run()
    >>> print(f"Index TPS: {result.metrics['git_index_tps']:.2f}")
"""

import sys
import tempfile
from pathlib import Path
from typing import Any

# Add src to path for importing memnexus
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from benchmark.core.base import BenchmarkResult, BenchmarkTask, Dataset
from benchmark.metrics.performance import PerformanceBenchmark


class IndexingPerformanceTask(BenchmarkTask):
    """Benchmark task for indexing performance.

    Measures:
        - Git indexing throughput (commits/second)
        - Code indexing throughput (symbols/second)
        - Memory usage during indexing
        - Search latency after indexing
    """

    def __init__(
        self,
        name: str,
        num_commits: int = 50,
        num_files: int = 10,
        **kwargs: Any,
    ):
        super().__init__(name, **kwargs)
        self.num_commits = num_commits
        self.num_files = num_files
        self._memory = None
        self._temp_dir = None

    def setup(self) -> None:
        """Setup: Create synthetic repository with commits and code."""
        from memnexus import CodeMemory

        print("[IndexingPerformanceTask] Setting up...")

        # Create temporary directory
        self._temp_dir = tempfile.mkdtemp(prefix="memnexus_benchmark_")
        repo_path = Path(self._temp_dir) / "repo"

        # Create synthetic repository
        self._create_repo(repo_path)

        # Initialize CodeMemory
        print("[IndexingPerformanceTask] Initializing CodeMemory...")
        memnexus_dir = repo_path / ".memnexus"
        memnexus_dir.mkdir(exist_ok=True)

        # Create minimal config
        config_path = memnexus_dir / "config.yaml"
        config_path.write_text("embedding:\n  method: tfidf\n  dim: 384\n")

        self._memory = CodeMemory(str(repo_path))

    def _create_repo(self, repo_path: Path) -> None:
        """Create a synthetic Git repository with commits and code."""
        import subprocess
        from datetime import datetime, timedelta

        repo_path.mkdir(parents=True, exist_ok=True)

        # Initialize Git repo
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

        # Create Python files
        src_dir = repo_path / "src"
        src_dir.mkdir(exist_ok=True)

        functions = [
            "authenticate_user",
            "validate_input",
            "process_data",
            "send_notification",
            "log_event",
        ]

        for i in range(self.num_files):
            code = f"""
def {functions[i % len(functions)]}_{i}(data: dict) -> dict:
    \"\"\"Process data for module {i}.\"\"\"
    result = {{"id": i, "data": data}}
    return result

class Processor{i}:
    \"\"\"Processor class for module {i}.\"\"\"

    def process(self, item: dict) -> dict:
        \"\"\"Process an item.\"\"\"
        return item
"""
            (src_dir / f"module_{i}.py").write_text(code)

        # Create commits
        base_date = datetime(2024, 1, 1)

        for i in range(self.num_commits):
            # Modify a file
            file_idx = i % self.num_files
            file_path = src_dir / f"module_{file_idx}.py"

            # Add a comment to create diff
            with open(file_path, "a") as f:
                f.write(f"\n# Update {i}\n")

            # Stage and commit
            subprocess.run(
                ["git", "add", "."],
                cwd=repo_path,
                capture_output=True,
                check=True,
            )

            env = {
                **subprocess.os.environ,
                "GIT_AUTHOR_DATE": (base_date + timedelta(hours=i)).isoformat(),
                "GIT_COMMITTER_DATE": (base_date + timedelta(hours=i)).isoformat(),
            }

            subprocess.run(
                ["git", "commit", "-m", f"Commit {i}: Update module {file_idx}"],
                cwd=repo_path,
                capture_output=True,
                env=env,
                check=True,
            )

    async def run(self, dataset: Dataset | None = None) -> BenchmarkResult:
        """Run the indexing performance benchmark.

        Returns:
            BenchmarkResult with performance metrics
        """
        import time

        self.ensure_setup()

        # Initialize memory
        await self._memory._initialize()

        metrics = {}

        # Benchmark Git indexing
        print(
            f"[IndexingPerformanceTask] Benchmarking Git indexing ({self.num_commits} commits)..."
        )
        start = time.perf_counter()
        git_result = await self._memory.index_git_history(limit=self.num_commits, incremental=False)
        git_duration = time.perf_counter() - start

        metrics["git_index_time"] = git_duration
        metrics["git_commits_indexed"] = git_result["commits_indexed"]
        metrics["git_index_tps"] = (
            git_result["commits_indexed"] / git_duration if git_duration > 0 else 0
        )

        # Benchmark Code indexing
        print("[IndexingPerformanceTask] Benchmarking code indexing...")
        start = time.perf_counter()
        code_result = await self._memory.index_codebase(incremental=False)
        code_duration = time.perf_counter() - start

        metrics["code_index_time"] = code_duration
        metrics["code_symbols_indexed"] = code_result["symbols_indexed"]
        metrics["code_index_tps"] = (
            code_result["symbols_indexed"] / code_duration if code_duration > 0 else 0
        )

        # Benchmark search latency
        print("[IndexingPerformanceTask] Benchmarking search latency...")

        async def search_git():
            return await self._memory.query_git_history("authentication", limit=5)

        async def search_code():
            return await self._memory.search_code("process data", limit=5)

        perf_benchmark = PerformanceBenchmark()

        # Measure Git search latency
        git_search_results = await perf_benchmark.run(search_git, runs=20, warmup_runs=2)
        for key, value in git_search_results["latency"].items():
            if isinstance(value, (int, float)):
                metrics[f"git_search_latency_{key}"] = value

        # Measure Code search latency
        perf_benchmark = PerformanceBenchmark()
        code_search_results = await perf_benchmark.run(search_code, runs=20, warmup_runs=2)
        for key, value in code_search_results["latency"].items():
            if isinstance(value, (int, float)):
                metrics[f"code_search_latency_{key}"] = value

        # Memory usage
        metrics["git_search_memory_mb"] = git_search_results["memory"]["peak_mb"]
        metrics["code_search_memory_mb"] = code_search_results["memory"]["peak_mb"]

        return BenchmarkResult(
            task_name=self.name,
            metrics=metrics,
            raw_results=[git_result, code_result],
            metadata={
                "num_commits": self.num_commits,
                "num_files": self.num_files,
            },
        )

    def teardown(self) -> None:
        """Cleanup resources."""
        import shutil

        if self._temp_dir and Path(self._temp_dir).exists():
            print("[IndexingPerformanceTask] Cleaning up temporary directory...")
            shutil.rmtree(self._temp_dir, ignore_errors=True)
