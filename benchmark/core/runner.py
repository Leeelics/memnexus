"""Benchmark runner - main entry point."""

from pathlib import Path
from typing import Any

import yaml

from benchmark.core.base import BenchmarkResult
from benchmark.core.pipeline import BenchmarkPipeline
from benchmark.core.reporter import BenchmarkReporter


class BenchmarkRunner:
    """Main runner for all benchmark tasks.

    Example:
        >>> runner = BenchmarkRunner()
        >>> results = await runner.run_all()
        >>>
        >>> # Run specific task
        >>> results = await runner.run_task("git_retrieval")
    """

    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self.pipeline = BenchmarkPipeline(self.config)
        self.reporter = BenchmarkReporter(self.config)
        self._tasks: dict[str, Any] = {}
        self._datasets: dict[str, Any] = {}

    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Load configuration from file."""
        if config_path is None:
            # Try default location
            config_path = Path(__file__).parent.parent / "config" / "benchmark.yaml"

        if Path(config_path).exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        return {}

    def register_task(self, name: str, task_class: type, **kwargs: Any) -> None:
        """Register a benchmark task."""
        self._tasks[name] = (task_class, kwargs)

    def register_dataset(self, name: str, dataset: Any) -> None:
        """Register a dataset."""
        self._datasets[name] = dataset

    def _create_task(self, name: str) -> Any:
        """Create a task instance."""
        if name not in self._tasks:
            raise ValueError(f"Task {name} not registered")

        task_class, kwargs = self._tasks[name]
        return task_class(name, **kwargs)

    async def run_task(self, name: str) -> BenchmarkResult:
        """Run a specific task."""
        task = self._create_task(name)
        dataset = self._datasets.get(name)
        return await self.pipeline.run_task(task, dataset)

    async def run_all(self) -> list[BenchmarkResult]:
        """Run all registered tasks."""
        tasks = [self._create_task(name) for name in self._tasks]
        datasets = {name: self._datasets.get(name) for name in self._tasks}
        return await self.pipeline.run_tasks(tasks, datasets)

    def generate_report(
        self,
        results: list[BenchmarkResult],
        output_format: str = "json",
        output_path: str | None = None,
    ) -> str:
        """Generate report from results."""
        if output_format == "json":
            return self.reporter.to_json(results, output_path)
        elif output_format == "html":
            return self.reporter.to_html(results, output_path)
        elif output_format == "markdown":
            return self.reporter.to_markdown(results, output_path)
        else:
            raise ValueError(f"Unknown format: {output_format}")

    def get_available_tasks(self) -> list[str]:
        """Get list of available task names."""
        return list(self._tasks.keys())
