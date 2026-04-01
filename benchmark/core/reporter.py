"""Benchmark reporting utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from benchmark.core.base import BenchmarkResult


class BenchmarkReporter:
    """Generate reports from benchmark results.

    Supports multiple output formats:
    - JSON: Machine-readable, detailed
    - HTML: Human-readable with charts
    - Markdown: Documentation-friendly

    Example:
        >>> reporter = BenchmarkReporter()
        >>> reporter.to_html(results, "report.html")
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def to_json(self, results: list[BenchmarkResult], output_path: str | None = None) -> str:
        """Export results to JSON.

        Args:
            results: List of benchmark results
            output_path: Optional output file path

        Returns:
            JSON string
        """
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(results),
            "summary": self._compute_summary(results),
            "results": [r.to_dict() for r in results],
        }

        json_str = json.dumps(data, indent=2, default=str)

        if output_path:
            Path(output_path).write_text(json_str)
            print(f"[Reporter] JSON report saved to: {output_path}")

        return json_str

    def to_markdown(self, results: list[BenchmarkResult], output_path: str | None = None) -> str:
        """Export results to Markdown.

        Args:
            results: List of benchmark results
            output_path: Optional output file path

        Returns:
            Markdown string
        """
        lines = [
            "# MemNexus Benchmark Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total Tasks:** {len(results)}",
            "",
            "## Summary",
            "",
        ]

        summary = self._compute_summary(results)
        for key, value in summary.items():
            lines.append(f"- **{key}:** {value}")

        lines.extend(["", "## Results by Task", ""])

        for result in results:
            lines.append(f"### {result.task_name}")
            lines.append(f"- **Duration:** {result.duration_seconds:.2f}s")
            lines.append("")
            lines.append("**Metrics:**")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for metric_name, metric_value in result.metrics.items():
                if isinstance(metric_value, float):
                    lines.append(f"| {metric_name} | {metric_value:.4f} |")
                else:
                    lines.append(f"| {metric_name} | {metric_value} |")
            lines.append("")

        md_str = "\n".join(lines)

        if output_path:
            Path(output_path).write_text(md_str)
            print(f"[Reporter] Markdown report saved to: {output_path}")

        return md_str

    def to_html(self, results: list[BenchmarkResult], output_path: str | None = None) -> str:
        """Export results to HTML.

        Args:
            results: List of benchmark results
            output_path: Optional output file path

        Returns:
            HTML string
        """
        summary = self._compute_summary(results)

        # Build metrics table rows
        table_rows = []
        for result in results:
            metrics_html = "<ul>"
            for k, v in result.metrics.items():
                if isinstance(v, float):
                    metrics_html += f"<li><strong>{k}:</strong> {v:.4f}</li>"
                else:
                    metrics_html += f"<li><strong>{k}:</strong> {v}</li>"
            metrics_html += "</ul>"

            row = f"""
            <tr>
                <td><strong>{result.task_name}</strong></td>
                <td>{result.duration_seconds:.2f}s</td>
                <td>{metrics_html}</td>
            </tr>
            """
            table_rows.append(row)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>MemNexus Benchmark Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .results {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .timestamp {{
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 MemNexus Benchmark Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>

    <div class="summary">
        <h2>📊 Summary</h2>
        <p><strong>Total Tasks:</strong> {len(results)}</p>
        <p><strong>Successful:</strong> {summary.get("successful", 0)}</p>
        <p><strong>Failed:</strong> {summary.get("failed", 0)}</p>
        <p><strong>Total Duration:</strong> {summary.get("total_duration", 0):.2f}s</p>
    </div>

    <div class="results">
        <h2>📈 Results by Task</h2>
        <table>
            <thead>
                <tr>
                    <th>Task</th>
                    <th>Duration</th>
                    <th>Metrics</th>
                </tr>
            </thead>
            <tbody>
                {"".join(table_rows)}
            </tbody>
        </table>
    </div>
</body>
</html>"""

        if output_path:
            Path(output_path).write_text(html)
            print(f"[Reporter] HTML report saved to: {output_path}")

        return html

    def _compute_summary(self, results: list[BenchmarkResult]) -> dict[str, Any]:
        """Compute summary statistics."""
        successful = sum(1 for r in results if "error" not in r.metrics)
        failed = len(results) - successful
        total_duration = sum(r.duration_seconds for r in results)

        return {
            "successful": successful,
            "failed": failed,
            "total_duration": total_duration,
            "avg_duration": total_duration / len(results) if results else 0,
        }
