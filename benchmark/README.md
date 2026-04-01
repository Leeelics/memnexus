# MemNexus Benchmark Suite

A comprehensive benchmarking framework for evaluating Code Memory retrieval quality and performance.

## Overview

The benchmark suite evaluates three key aspects of MemNexus:

1. **Git Retrieval** - Quality of Git commit history search
2. **Code Retrieval** - Quality of code symbol (function/class/method) search
3. **Indexing Performance** - Speed and resource usage of indexing operations

## Quick Start

```bash
# Run all benchmarks
python benchmark/run.py --all

# Run specific benchmark
python benchmark/run.py --task git_retrieval
python benchmark/run.py --task code_retrieval
python benchmark/run.py --task indexing

# Generate HTML report
python benchmark/run.py --all --format html

# List available tasks
python benchmark/run.py --list
```

## Benchmark Tasks

### Git Retrieval (`git_retrieval`)

Evaluates how well MemNexus can retrieve relevant Git commits based on semantic queries.

**Dataset:** Synthetic Git repository with 13+ commits across different categories:
- Feature commits (authentication, database, rate limiting)
- Bug fix commits
- Refactoring commits

**Metrics:**
- Recall@K (K=1,3,5,10) - Proportion of relevant commits found
- Precision@K - Proportion of top results that are relevant
- F1@K - Harmonic mean of Precision and Recall
- NDCG@K - Quality of ranking
- MRR - Mean Reciprocal Rank (how early is first relevant result)

**Example Output:**
```
git_retrieval:
  Duration: 0.50s
  recall@5: 0.6111
  precision@5: 0.3556
  ndcg@5: 0.6402
  mrr: 0.8148
```

### Code Retrieval (`code_retrieval`)

Evaluates how well MemNexus can retrieve relevant code symbols (functions, classes, methods).

**Dataset:** 10 synthetic queries covering:
- Authentication functions
- Database operations
- Rate limiting
- Validation
- Caching

**Metrics:** Same as Git Retrieval

**Example Output:**
```
code_retrieval:
  Duration: 0.75s
  recall@5: 0.7500
  precision@5: 0.3200
  ndcg@5: 0.6976
  mrr: 0.7444
```

### Indexing Performance (`indexing`)

Measures indexing throughput, search latency, and memory usage.

**Configuration:**
- Default: 50 commits, 10 files
- Configurable via `--num-commits` and `--num-files`

**Metrics:**
- Git Index TPS - Commits indexed per second
- Code Index TPS - Symbols indexed per second
- Search Latency (p50, p95, p99) - Response time percentiles
- Memory Usage - Peak memory consumption in MB

**Example Output:**
```
indexing:
  Duration: 5.23s
  git_index_tps: 120.98
  code_index_tps: 230.02
  git_search_latency_p50: 0.0135
  git_search_latency_p95: 0.0276
  code_search_latency_p50: 0.0159
  git_search_memory_mb: 0.16
```

## Project Structure

```
benchmark/
├── core/                   # Core framework
│   ├── base.py            # Base classes (BenchmarkTask, Dataset, etc.)
│   ├── pipeline.py        # Execution pipeline
│   ├── runner.py          # Main runner
│   └── reporter.py        # Report generation
├── metrics/               # Evaluation metrics
│   ├── retrieval.py       # Recall, Precision, F1
│   ├── ranking.py         # NDCG, MRR, MAP
│   └── performance.py     # Latency, Throughput, Memory
├── datasets/              # Dataset management
│   ├── synthetic.py       # Synthetic repo/dataset generation
│   └── loader.py          # Dataset loading utilities
├── tasks/                 # Benchmark tasks
│   ├── git_retrieval.py   # Git retrieval benchmark
│   ├── code_retrieval.py  # Code retrieval benchmark
│   └── indexing.py        # Indexing performance benchmark
├── config/
│   └── benchmark.yaml     # Configuration file
├── results/               # Output directory (created at runtime)
├── run.py                 # Main entry point
└── README.md              # This file
```

## Adding Custom Benchmarks

### 1. Create a New Task

```python
from benchmark.core.base import BenchmarkTask, BenchmarkResult, Dataset

class MyBenchmarkTask(BenchmarkTask):
    def setup(self) -> None:
        # Initialize resources
        pass

    async def run(self, dataset: Dataset | None = None) -> BenchmarkResult:
        # Run benchmark
        return BenchmarkResult(
            task_name=self.name,
            metrics={"metric1": 0.95, "metric2": 0.87},
        )

    def teardown(self) -> None:
        # Cleanup
        pass
```

### 2. Register in run.py

```python
runner.register_task(
    "my_benchmark",
    MyBenchmarkTask,
    # Task-specific kwargs
)
```

### 3. Run

```bash
python benchmark/run.py --task my_benchmark
```

## Configuration

Edit `benchmark/config/benchmark.yaml` to customize:

```yaml
# K values for retrieval metrics
k_values: [1, 3, 5, 10]

# Performance benchmark settings
indexing:
  num_commits: 50
  num_files: 10

# Output settings
output:
  formats: ["json", "html", "markdown"]
```

## Interpreting Results

### Retrieval Quality

| Metric | Good | Excellent |
|--------|------|-----------|
| Recall@5 | > 0.5 | > 0.7 |
| Precision@5 | > 0.3 | > 0.5 |
| NDCG@5 | > 0.6 | > 0.8 |
| MRR | > 0.6 | > 0.8 |

### Performance

| Metric | Acceptable | Good | Excellent |
|--------|------------|------|-----------|
| Git Index TPS | > 50 | > 100 | > 200 |
| Code Index TPS | > 100 | > 200 | > 500 |
| Search Latency p95 | < 100ms | < 50ms | < 20ms |
| Memory Usage | < 500MB | < 200MB | < 100MB |

## CI/CD Integration

Run benchmarks in CI:

```yaml
# .github/workflows/benchmark.yml
- name: Run Benchmarks
  run: |
    python benchmark/run.py --all --format json --output ./benchmark-results

- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: benchmark-results
    path: ./benchmark-results/
```

## License

Same as MemNexus project (MIT).
