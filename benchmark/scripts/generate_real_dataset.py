#!/usr/bin/env python3
"""Generate real-world benchmark datasets from repositories."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.git_adapter import GitAdapter
from adapters.code_adapter import CodeAdapter


def main():
    parser = argparse.ArgumentParser(description="Generate real benchmark datasets")
    parser.add_argument("--repo", required=True, help="Path to repository")
    parser.add_argument("--output", default="datasets/real", help="Output directory")
    parser.add_argument("--max-commits", type=int, default=100, help="Max commits to extract")
    args = parser.parse_args()

    repo_path = Path(args.repo)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating Real Benchmark Datasets")
    print(f"Repository: {repo_path}")
    print(f"Output: {output_dir}")
    print("=" * 60)

    # Generate Git history dataset
    print("\n📊 Generating Git History Dataset...")
    git_adapter = GitAdapter(repo_path, max_commits=args.max_commits)
    git_output = output_dir / "git_history.json"
    git_adapter.export_to_json(str(git_output))

    # Generate Code dataset
    print("\n📊 Generating Code Repository Dataset...")
    code_adapter = CodeAdapter(repo_path)
    code_output = output_dir / "code_repository.json"
    code_adapter.export_to_json(str(code_output))

    print("\n" + "=" * 60)
    print("✅ Dataset generation complete!")
    print(f"Output files:")
    print(f"  - {git_output}")
    print(f"  - {code_output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
