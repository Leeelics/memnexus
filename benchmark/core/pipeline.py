"""Benchmark execution pipeline."""

import time
from typing import Any

from benchmark.core.base import BenchmarkResult, BenchmarkTask, Dataset


class BenchmarkPipeline:
    """Pipeline for executing benchmark tasks.

    Manages the flow of:
    1. Task setup
    2. Dataset loading
    3. Task execution
    4. Result collection
    5. Cleanup

    Example:
        >>> pipeline = BenchmarkPipeline()
        >>> result = await pipeline.run_task(task, dataset)
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.results: list[BenchmarkResult] = []

    async def run_task(
        self, task: BenchmarkTask, dataset: Dataset | None = None
    ) -> BenchmarkResult:
        """Run a single benchmark task.

        Args:
            task: The benchmark task to run
            dataset: Optional dataset to use

        Returns:
            BenchmarkResult with metrics
        """
        print(f"[Pipeline] Setting up task: {task.name}")
        start_time = time.perf_counter()

        try:
            # Setup
            task.ensure_setup()

            # Run
            print(f"[Pipeline] Running task: {task.name}")
            result = await task.run(dataset)

            # Record duration
            result.duration_seconds = time.perf_counter() - start_time

            print(f"[Pipeline] Task {task.name} completed in {result.duration_seconds:.2f}s")
            return result

        except Exception as e:
            print(f"[Pipeline] Task {task.name} failed: {e}")
            # Return failed result
            return BenchmarkResult(
                task_name=task.name,
                metrics={"error": 1.0},
                metadata={"error_message": str(e)},
                duration_seconds=time.perf_counter() - start_time,
            )

    async def run_tasks(
        self, tasks: list[BenchmarkTask], datasets: dict[str, Dataset] | None = None
    ) -> list[BenchmarkResult]:
        """Run multiple tasks.

        Args:
            tasks: List of tasks to run
            datasets: Mapping of task name to dataset

        Returns:
            List of results
        """
        results = []
        datasets = datasets or {}

        for task in tasks:
            dataset = datasets.get(task.name)
            result = await self.run_task(task, dataset)
            results.append(result)

        self.results.extend(results)
        return results

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all results."""
        return {
            "total_tasks": len(self.results),
            "successful": sum(1 for r in self.results if "error" not in r.metrics),
            "failed": sum(1 for r in self.results if "error" in r.metrics),
            "total_duration": sum(r.duration_seconds for r in self.results),
            "results": [r.to_dict() for r in self.results],
        }
