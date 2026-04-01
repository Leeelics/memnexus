"""Git retrieval benchmark task.

Evaluates the quality of Git commit history search.

Example:
    >>> task = GitRetrievalTask("git_retrieval", project_path="./my-project")
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
from benchmark.datasets.synthetic import GitBenchmarkDataset, SyntheticRepoGenerator
from benchmark.metrics.ranking import compute_ranking_metrics
from benchmark.metrics.retrieval import compute_metrics_at_k


class GitRetrievalTask(BenchmarkTask):
    """Benchmark task for Git commit retrieval.

    Measures how well the system can retrieve relevant Git commits
    based on semantic queries.

    Metrics:
        - Recall@K: Can we find the relevant commits?
        - Precision@K: Are the top results relevant?
        - NDCG@K: Are relevant commits ranked highly?
        - MRR: How early is the first relevant commit?
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
        """Setup: Create synthetic repo and initialize CodeMemory."""
        from memnexus import CodeMemory

        print("[GitRetrievalTask] Setting up...")

        # Create temporary directory for synthetic repo
        self._temp_dir = tempfile.mkdtemp(prefix="memnexus_benchmark_")
        repo_path = Path(self._temp_dir) / "repo"

        # Create synthetic repository
        print("[GitRetrievalTask] Creating synthetic repository...")
        generator = SyntheticRepoGenerator(str(repo_path))
        generator.create_repo()
        generator.add_feature_commits()
        generator.add_bugfix_commits()
        generator.add_refactor_commits()

        # Create dataset from generator
        self._dataset = GitBenchmarkDataset.create_from_generator(generator)
        print(f"[GitRetrievalTask] Dataset: {len(self._dataset)} queries")

        # Initialize CodeMemory
        print("[GitRetrievalTask] Initializing CodeMemory...")
        memnexus_dir = repo_path / ".memnexus"
        memnexus_dir.mkdir(exist_ok=True)

        # Create minimal config
        config_path = memnexus_dir / "config.yaml"
        config_path.write_text("embedding:\n  method: tfidf\n  dim: 384\n")

        self._memory = CodeMemory(str(repo_path))

    async def run(self, dataset: Dataset | None = None) -> BenchmarkResult:
        """Run the Git retrieval benchmark.

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

        # Index Git history
        print("[GitRetrievalTask] Indexing Git history...")
        index_result = await self._memory.index_git_history(limit=100, incremental=False)
        print(f"[GitRetrievalTask] Indexed {index_result['commits_indexed']} commits")

        # Run queries and collect results
        print(f"[GitRetrievalTask] Running {len(dataset.queries)} queries...")
        query_results = []

        for query_data in dataset.queries:
            query = query_data["query"]
            expected = query_data["expected"]

            # Search Git history
            git_results = await self._memory.query_git_history(query, limit=max(self.k_values))

            # Extract retrieved commit hashes
            retrieved = [r.commit_hash for r in git_results]

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
        aggregated_metrics["commits_indexed"] = index_result["commits_indexed"]

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
            print("[GitRetrievalTask] Cleaning up temporary directory...")
            shutil.rmtree(self._temp_dir, ignore_errors=True)

        if self._memory:
            # Close memory if needed
            pass
