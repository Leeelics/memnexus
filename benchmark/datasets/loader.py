"""Dataset loader utilities."""

import json
from pathlib import Path
from typing import Any

from benchmark.core.base import Dataset
from benchmark.datasets.synthetic import (
    CodeBenchmarkDataset,
    GitBenchmarkDataset,
    SyntheticRepoGenerator,
)


class DatasetLoader:
    """Load and manage benchmark datasets.

    Example:
        >>> loader = DatasetLoader()
        >>> git_dataset = loader.load_git_dataset("synthetic")
        >>> code_dataset = loader.load_code_dataset("synthetic")
    """

    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            data_dir = Path(__file__).parent
        self.data_dir = Path(data_dir)

    def load_git_dataset(self, name: str = "synthetic", **kwargs: Any) -> Dataset:
        """Load a Git retrieval dataset.

        Args:
            name: Dataset name ("synthetic" or path to dataset file)
            **kwargs: Additional arguments for dataset creation

        Returns:
            Dataset for Git retrieval benchmarking
        """
        if name == "synthetic":
            # Create synthetic dataset
            repo_path = kwargs.get("repo_path", self.data_dir / "synthetic_repos" / "git_repo")
            generator = SyntheticRepoGenerator(str(repo_path))

            # Create repo if it doesn't exist
            git_dir = Path(repo_path) / ".git"
            if not git_dir.exists():
                print(f"[DatasetLoader] Creating synthetic Git repo at {repo_path}")
                generator.create_repo()
                generator.add_feature_commits()
                generator.add_bugfix_commits()
                generator.add_refactor_commits()

            git_dataset = GitBenchmarkDataset.create_from_generator(generator)

            # Convert to generic Dataset
            return Dataset(
                name="git_synthetic",
                queries=git_dataset.queries,
                metadata=git_dataset.metadata,
            )

        elif name.endswith(".json"):
            # Load from JSON file
            with open(name) as f:
                data = json.load(f)
            return Dataset(
                name=Path(name).stem,
                queries=data["queries"],
                metadata=data.get("metadata", {}),
            )

        else:
            raise ValueError(f"Unknown dataset: {name}")

    def load_code_dataset(self, name: str = "synthetic", **kwargs: Any) -> Dataset:
        """Load a code retrieval dataset.

        Args:
            name: Dataset name ("synthetic" or path to dataset file)
            **kwargs: Additional arguments for dataset creation

        Returns:
            Dataset for code retrieval benchmarking
        """
        if name == "synthetic":
            code_dataset = CodeBenchmarkDataset.create_synthetic()
            return Dataset(
                name="code_synthetic",
                queries=code_dataset.queries,
                metadata=code_dataset.metadata,
            )

        elif name.endswith(".json"):
            with open(name) as f:
                data = json.load(f)
            return Dataset(
                name=Path(name).stem,
                queries=data["queries"],
                metadata=data.get("metadata", {}),
            )

        else:
            raise ValueError(f"Unknown dataset: {name}")

    def save_dataset(self, dataset: Dataset, output_path: str) -> None:
        """Save a dataset to JSON file.

        Args:
            dataset: Dataset to save
            output_path: Output file path
        """
        data = {
            "name": dataset.name,
            "queries": dataset.queries,
            "metadata": dataset.metadata,
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"[DatasetLoader] Saved dataset to {output_path}")
