#!/usr/bin/env python3
"""MemNexus Benchmark Runner - Main entry point.

Usage:
    # Run all benchmarks
    python benchmark/run.py --all

    # Run specific benchmark
    python benchmark/run.py --task git_retrieval
    python benchmark/run.py --task code_retrieval
    python benchmark/run.py --task indexing

    # Generate reports
    python benchmark/run.py --all --format html --output ./results

    # List available tasks
    python benchmark/run.py --list
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from benchmark.core.runner import BenchmarkRunner
from benchmark.tasks import CodeRetrievalTask, GitRetrievalTask, IndexingPerformanceTask


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="MemNexus Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                                    # Run all benchmarks
  %(prog)s --task git_retrieval                     # Run Git retrieval benchmark
  %(prog)s --task code_retrieval --format html      # Run with HTML report
  %(prog)s --all --output ./my_results              # Save results to directory
  %(prog)s --list                                   # List available tasks
        """,
    )

    # Task selection
    task_group = parser.add_mutually_exclusive_group(required=True)
    task_group.add_argument(
        "--all",
        action="store_true",
        help="Run all benchmark tasks",
    )
    task_group.add_argument(
        "--task",
        type=str,
        choices=["git_retrieval", "code_retrieval", "indexing"],
        help="Run specific benchmark task",
    )
    task_group.add_argument(
        "--list",
        action="store_true",
        help="List available benchmark tasks",
    )

    # Output options
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "html", "markdown"],
        default="json",
        help="Report format (default: json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./benchmark/results",
        help="Output directory for reports (default: ./benchmark/results)",
    )

    # Benchmark configuration
    parser.add_argument(
        "--num-commits",
        type=int,
        default=50,
        help="Number of commits for indexing benchmark (default: 50)",
    )
    parser.add_argument(
        "--num-files",
        type=int,
        default=10,
        help="Number of files for indexing benchmark (default: 10)",
    )

    # Other options
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    return parser


def list_tasks() -> None:
    """Print available tasks."""
    print("Available Benchmark Tasks:")
    print()
    print("  git_retrieval     - Evaluate Git commit retrieval quality")
    print("                      Metrics: Recall@K, Precision@K, NDCG@K, MRR")
    print()
    print("  code_retrieval    - Evaluate code symbol retrieval quality")
    print("                      Metrics: Recall@K, Precision@K, NDCG@K, MRR")
    print()
    print("  indexing          - Evaluate indexing and search performance")
    print("                      Metrics: TPS, Latency (p50/p95/p99), Memory")
    print()


def register_tasks(runner: BenchmarkRunner, args: argparse.Namespace) -> None:
    """Register all benchmark tasks."""
    # Git retrieval task
    runner.register_task(
        "git_retrieval",
        GitRetrievalTask,
        k_values=[1, 3, 5, 10],
    )

    # Code retrieval task
    runner.register_task(
        "code_retrieval",
        CodeRetrievalTask,
        k_values=[1, 3, 5, 10],
    )

    # Indexing performance task
    runner.register_task(
        "indexing",
        IndexingPerformanceTask,
        num_commits=args.num_commits,
        num_files=args.num_files,
    )


async def run_benchmarks(args: argparse.Namespace) -> None:
    """Run benchmarks based on arguments."""
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create runner
    runner = BenchmarkRunner()

    # Register tasks
    register_tasks(runner, args)

    # Run benchmarks
    if args.all:
        print("=" * 60)
        print("MemNexus Benchmark Suite - Running All Tasks")
        print("=" * 60)
        print()
        results = await runner.run_all()
    else:
        print("=" * 60)
        print(f"MemNexus Benchmark Suite - Running: {args.task}")
        print("=" * 60)
        print()
        results = [await runner.run_task(args.task)]

    # Print summary
    print()
    print("=" * 60)
    print("Benchmark Summary")
    print("=" * 60)

    for result in results:
        print(f"\n{result.task_name}:")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        for metric_name, metric_value in result.metrics.items():
            if isinstance(metric_value, float):
                print(f"  {metric_name}: {metric_value:.4f}")
            else:
                print(f"  {metric_name}: {metric_value}")

    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"benchmark_{timestamp}.{args.format}"

    runner.generate_report(results, args.format, str(output_path))

    print()
    print("=" * 60)
    print(f"Report saved to: {output_path}")
    print("=" * 60)

    # Also save JSON for programmatic access
    json_path = output_dir / f"benchmark_{timestamp}.json"
    runner.generate_report(results, "json", str(json_path))
    print(f"JSON data saved to: {json_path}")


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.list:
        list_tasks()
        return 0

    try:
        asyncio.run(run_benchmarks(args))
        return 0
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nBenchmark failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
