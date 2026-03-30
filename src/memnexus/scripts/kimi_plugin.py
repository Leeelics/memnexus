#!/usr/bin/env python3
"""Kimi CLI plugin for MemNexus.

This script provides the interface between Kimi CLI and MemNexus.
It handles tool calls from the plugin system and returns formatted results.

Usage:
    python -m memnexus.scripts.kimi_plugin <command> [args]
"""

import argparse
import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def get_project_path() -> Path:
    """Get the current project path from environment or default."""
    if "KIMI_WORKING_DIR" in os.environ:
        return Path(os.environ["KIMI_WORKING_DIR"])
    return Path.cwd()


def run_memnexus_cli(args: list[str]) -> dict[str, Any]:
    """Run memnexus CLI command and parse output."""
    try:
        result = subprocess.run(
            ["memnexus"] + args, capture_output=True, text=True, cwd=get_project_path()
        )

        if result.returncode == 0:
            # Try to parse as JSON if possible
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"status": "success", "output": result.stdout}
        else:
            return {"status": "error", "error": result.stderr or result.stdout}
    except FileNotFoundError:
        return {
            "status": "error",
            "error": "memnexus CLI not found. Install with: pip install memnexus",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def format_search_results(output: str, source: str) -> dict[str, Any]:
    """Format search results for Kimi CLI."""
    # For now, return raw output
    # TODO: Parse structured output from memnexus CLI
    return {
        "status": "success",
        "results": output,
        "source": source,
    }


async def cmd_search(args: argparse.Namespace) -> None:
    """Search project memory."""
    project_path = get_project_path()

    # Check if project is initialized
    if not (project_path / ".memnexus").exists():
        print(
            json.dumps(
                {
                    "status": "not_initialized",
                    "message": "Project not indexed. Run: memnexus init && memnexus index",
                    "project_path": str(project_path),
                }
            )
        )
        return

    # Use memnexus CLI for search
    cli_args = ["search", args.query, "--limit", str(args.limit)]

    if args.source == "git":
        cli_args.append("--git")
    elif args.source == "code":
        cli_args.append("--code")

    result = run_memnexus_cli(cli_args)
    print(json.dumps(result))


async def cmd_store(args: argparse.Namespace) -> None:
    """Store a memory."""
    project_path = get_project_path()

    # Check if project is initialized
    if not (project_path / ".memnexus").exists():
        print(
            json.dumps(
                {
                    "status": "not_initialized",
                    "message": "Project not initialized. Run: memnexus init",
                }
            )
        )
        return

    # For now, store as a simple memory entry
    # This would need a memnexus CLI command for adding memories
    # For now, we'll create a simple file-based storage

    mem_dir = project_path / ".memnexus" / "user_memories"
    mem_dir.mkdir(exist_ok=True)

    import datetime
    import hashlib

    memory_id = hashlib.md5(args.content.encode()).hexdigest()[:8]
    timestamp = datetime.datetime.now().isoformat()

    memory_data = {
        "id": memory_id,
        "content": args.content,
        "category": args.category or "finding",
        "tags": args.tags or [],
        "timestamp": timestamp,
        "source": "kimi_cli",
    }

    mem_file = mem_dir / f"{memory_id}.json"
    with open(mem_file, "w") as f:
        json.dump(memory_data, f, indent=2)

    print(
        json.dumps(
            {
                "status": "success",
                "memory_id": memory_id,
                "category": args.category or "finding",
            }
        )
    )


async def cmd_status(args: argparse.Namespace) -> None:
    """Get memory status."""
    result = run_memnexus_cli(["status"])
    print(json.dumps(result))


async def cmd_index(args: argparse.Namespace) -> None:
    """Index project."""
    cli_args = ["index"]

    if args.git:
        cli_args.append("--git")
    if args.code:
        cli_args.append("--code")

    result = run_memnexus_cli(cli_args)
    print(json.dumps(result))


async def cmd_find_symbol(args: argparse.Namespace) -> None:
    """Find a specific symbol."""
    # Use code search for now
    result = run_memnexus_cli(["search", args.name, "--code", "--limit", "5"])
    print(json.dumps(result))


async def cmd_file_history(args: argparse.Namespace) -> None:
    """Get file history."""
    # For now, return a placeholder
    # This would need a memnexus CLI command
    print(
        json.dumps(
            {
                "status": "success",
                "file": args.file_path,
                "message": f"File history for {args.file_path}. Use: memnexus git log {args.file_path}",
            }
        )
    )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MemNexus Kimi CLI Plugin")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search memory")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--source", choices=["all", "git", "code"], default="all")
    search_parser.add_argument("--limit", type=int, default=5)

    # Store command
    store_parser = subparsers.add_parser("store", help="Store memory")
    store_parser.add_argument("content", help="Content to store")
    store_parser.add_argument("--category", default="finding")
    store_parser.add_argument("--tags", nargs="*", default=[])

    # Status command
    status_parser = subparsers.add_parser("status", help="Get status")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index project")
    index_parser.add_argument("--git", action="store_true", default=True)
    index_parser.add_argument("--code", action="store_true", default=True)

    # Find symbol command
    symbol_parser = subparsers.add_parser("find_symbol", help="Find symbol")
    symbol_parser.add_argument("name", help="Symbol name")

    # File history command
    history_parser = subparsers.add_parser("file_history", help="Get file history")
    history_parser.add_argument("file_path", help="File path")
    history_parser.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if args.command == "search":
        await cmd_search(args)
    elif args.command == "store":
        await cmd_store(args)
    elif args.command == "status":
        await cmd_status(args)
    elif args.command == "index":
        await cmd_index(args)
    elif args.command == "find_symbol":
        await cmd_find_symbol(args)
    elif args.command == "file_history":
        await cmd_file_history(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
