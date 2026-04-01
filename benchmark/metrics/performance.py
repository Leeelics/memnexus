"""Performance metrics for measuring speed and resource usage.

Metrics:
    - Latency: Response time (p50, p95, p99)
    - Throughput: Operations per second
    - Memory: Peak memory usage

Example:
    >>> import asyncio
    >>> async def search():
    ...     return await memory.search("query")
    >>> latency = await measure_latency(search, runs=10)
    >>> print(f"p50: {latency['p50']:.3f}s")
"""

import gc
import time
import tracemalloc
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


async def measure_latency[T](
    func: Callable[[], Coroutine[Any, Any, T]],
    runs: int = 10,
    warmup_runs: int = 2,
) -> dict[str, float]:
    """Measure latency percentiles of an async function.

    Args:
        func: Async function to measure
        runs: Number of measurement runs
        warmup_runs: Number of warmup runs (not counted)

    Returns:
        Dictionary with p50, p95, p99, mean, min, max latency in seconds
    """
    # Warmup runs
    for _ in range(warmup_runs):
        await func()

    # Actual measurements
    latencies = []
    for _ in range(runs):
        start = time.perf_counter()
        await func()
        end = time.perf_counter()
        latencies.append(end - start)

    latencies.sort()

    n = len(latencies)
    return {
        "p50": latencies[n // 2],
        "p95": latencies[int(n * 0.95)],
        "p99": latencies[int(n * 0.99)] if n >= 100 else latencies[-1],
        "mean": sum(latencies) / n,
        "min": latencies[0],
        "max": latencies[-1],
        "runs": n,
    }


def measure_latency_sync[T](
    func: Callable[[], T],
    runs: int = 10,
    warmup_runs: int = 2,
) -> dict[str, float]:
    """Measure latency percentiles of a sync function.

    Args:
        func: Function to measure
        runs: Number of measurement runs
        warmup_runs: Number of warmup runs (not counted)

    Returns:
        Dictionary with p50, p95, p99, mean, min, max latency in seconds
    """
    # Warmup runs
    for _ in range(warmup_runs):
        func()

    # Actual measurements
    latencies = []
    for _ in range(runs):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        latencies.append(end - start)

    latencies.sort()

    n = len(latencies)
    return {
        "p50": latencies[n // 2],
        "p95": latencies[int(n * 0.95)],
        "p99": latencies[int(n * 0.99)] if n >= 100 else latencies[-1],
        "mean": sum(latencies) / n,
        "min": latencies[0],
        "max": latencies[-1],
        "runs": n,
    }


async def measure_throughput[T](
    func: Callable[[], Coroutine[Any, Any, T]],
    duration_seconds: float = 5.0,
) -> dict[str, float]:
    """Measure throughput of an async function.

    Args:
        func: Async function to measure
        duration_seconds: Duration of the measurement

    Returns:
        Dictionary with operations per second
    """
    count = 0
    start = time.perf_counter()

    while time.perf_counter() - start < duration_seconds:
        await func()
        count += 1

    elapsed = time.perf_counter() - start

    return {
        "operations": count,
        "duration_seconds": elapsed,
        "ops_per_second": count / elapsed,
    }


async def measure_memory[T](
    func: Callable[[], Coroutine[Any, Any, T]],
) -> dict[str, float]:
    """Measure peak memory usage of an async function.

    Args:
        func: Async function to measure

    Returns:
        Dictionary with memory usage in MB
    """
    # Force garbage collection before measurement
    gc.collect()

    # Start tracking
    tracemalloc.start()
    tracemalloc.reset_peak()

    # Run function
    await func()

    # Get peak memory
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "peak_mb": peak / (1024 * 1024),
        "peak_bytes": peak,
    }


def measure_memory_sync[T](
    func: Callable[[], T],
) -> dict[str, float]:
    """Measure peak memory usage of a sync function.

    Args:
        func: Function to measure

    Returns:
        Dictionary with memory usage in MB
    """
    # Force garbage collection before measurement
    gc.collect()

    # Start tracking
    tracemalloc.start()
    tracemalloc.reset_peak()

    # Run function
    func()

    # Get peak memory
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "peak_mb": peak / (1024 * 1024),
        "peak_bytes": peak,
    }


class PerformanceBenchmark:
    """Helper class for comprehensive performance benchmarking.

    Example:
        >>> benchmark = PerformanceBenchmark()
        >>>
        >>> async def search_op():
        ...     return await memory.search("query")
        >>>
        >>> results = await benchmark.run(search_op, runs=100)
        >>> print(f"Latency p50: {results['latency']['p50']:.3f}s")
        >>> print(f"Throughput: {results['throughput']['ops_per_second']:.1f} ops/s")
    """

    def __init__(self):
        self.results: dict[str, Any] = {}

    async def run(
        self,
        func: Callable[[], Coroutine[Any, Any, T]],
        runs: int = 100,
        warmup_runs: int = 5,
    ) -> dict[str, Any]:
        """Run comprehensive performance benchmark.

        Args:
            func: Async function to benchmark
            runs: Number of measurement runs
            warmup_runs: Number of warmup runs

        Returns:
            Dictionary with latency, throughput, and memory results
        """
        print(f"[Performance] Running warmup ({warmup_runs} runs)...")
        for _ in range(warmup_runs):
            await func()

        print(f"[Performance] Measuring latency ({runs} runs)...")
        self.results["latency"] = await measure_latency(func, runs, warmup_runs=0)

        print("[Performance] Measuring throughput...")
        self.results["throughput"] = await measure_throughput(func, duration_seconds=2.0)

        print("[Performance] Measuring memory...")
        self.results["memory"] = await measure_memory(func)

        return self.results
