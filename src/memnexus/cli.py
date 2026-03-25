"""CLI entry point for MemNexus Code Memory."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from memnexus import __version__
from memnexus.code_memory import CodeMemory

app = typer.Typer(
    name="memnexus",
    help="MemNexus - Code Memory for AI Programming Tools",
    no_args_is_help=True,
)
console = Console()


def _get_project_path(path: Optional[str] = None) -> Path:
    """Get project path, defaulting to current directory."""
    return Path(path or ".").resolve()


@app.callback()
def callback():
    """MemNexus CLI - Persistent memory for AI coding assistants."""
    pass


@app.command()
def version():
    """Show version information."""
    console.print(Panel.fit(
        f"[bold cyan]MemNexus Code Memory[/bold cyan]\n"
        f"Version: {__version__}\n"
        f"\n"
        f"Let your AI assistants remember your project.",
        title="About",
        border_style="cyan",
    ))


@app.command()
def init(
    path: Optional[str] = typer.Option(".", "--path", "-p", help="Project path"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
):
    """Initialize MemNexus for a project.
    
    Creates .memnexus/ directory with configuration.
    """
    project_path = _get_project_path(path)
    memnexus_dir = project_path / ".memnexus"
    
    # Check if already initialized
    if memnexus_dir.exists() and not force:
        console.print(Panel.fit(
            f"Project already initialized at:\n"
            f"[yellow]{memnexus_dir}[/yellow]\n\n"
            f"Use [bold]--force[/bold] to reinitialize.",
            title="Already Initialized",
            border_style="yellow",
        ))
        raise typer.Exit(0)
    
    # Create directory structure
    try:
        memnexus_dir.mkdir(exist_ok=True)
        (memnexus_dir / "logs").mkdir(exist_ok=True)
        
        # Create config file
        import datetime
        config_file = memnexus_dir / "config.yaml"
        config_content = f'''version: "1.0"
project:
  name: "{project_path.name}"
  root: "{project_path}"
  initialized_at: "{datetime.datetime.now().isoformat()}"

memory:
  backend: "lancedb"
  path: ".memnexus/memory.lance"

git:
  enabled: true
  max_history: 1000

code:
  languages: ["python", "javascript", "typescript", "rust", "go"]
  exclude_patterns:
    - "*.pyc"
    - "__pycache__/"
    - "node_modules/"
    - ".git/"
    - ".venv/"
    - ".memnexus/"
'''
        config_file.write_text(config_content)
        
        # Check for git
        git_dir = project_path / ".git"
        git_status = "[green]✓ Detected[/green]" if git_dir.exists() else "[yellow]✗ Not found[/yellow]"
        
        console.print(Panel.fit(
            f"[green]✓[/green] Created .memnexus/ directory\n"
            f"[green]✓[/green] Generated config.yaml\n"
            f"[green]✓[/green] Initialized logs directory\n"
            f"{git_status} Git repository\n\n"
            f"[bold]Next steps:[/bold]\n"
            f'  1. Run [cyan]memnexus index[/cyan] to index your codebase\n'
            f'  2. Run [cyan]memnexus search "your query"[/cyan] to search\n'
            f'  3. Run [cyan]memnexus server[/cyan] to start API server',
            title="Initialized Successfully",
            border_style="green",
        ))
        
    except Exception as e:
        console.print(Panel.fit(
            f"Failed to initialize project:\n"
            f"[red]{e}[/red]",
            title="Error",
            border_style="red",
        ))
        raise typer.Exit(1)


@app.command()
def status(
    path: Optional[str] = typer.Option(".", "--path", "-p", help="Project path"),
):
    """Show project status."""
    project_path = _get_project_path(path)
    memnexus_dir = project_path / ".memnexus"
    
    # Check if initialized
    if not memnexus_dir.exists():
        console.print(Panel.fit(
            f"Project not initialized at:\n"
            f"[yellow]{project_path}[/yellow]\n\n"
            f"Run [cyan]memnexus init[/cyan] to initialize.",
            title="Not Initialized",
            border_style="yellow",
        ))
        raise typer.Exit(0)
    
    # Try to get stats from CodeMemory
    try:
        memory = asyncio.run(CodeMemory.init(project_path))
        stats = memory.get_stats()
        
        # Check for git
        git_dir = project_path / ".git"
        git_status = "[green]✓[/green] Yes" if git_dir.exists() else "[yellow]✗[/yellow] No"
        
        console.print(Panel.fit(
            f"[bold]Project:[/bold] {project_path.name}\n"
            f"[bold]Path:[/bold] {project_path}\n"
            f"[bold]Git:[/bold] {git_status}\n"
            f"[bold]Git commits indexed:[/bold] {stats.get('git_commits_indexed', 0)}\n"
            f"[bold]Code symbols indexed:[/bold] {stats.get('code_symbols_indexed', 0)}\n"
            f"[bold]Total memories:[/bold] {stats.get('total_memories', 0)}\n\n"
            f"[bold]Commands:[/bold]\n"
            f'  [cyan]memnexus index[/cyan] - Index your codebase\n'
            f'  [cyan]memnexus search "query"[/cyan] - Search memories\n'
            f'  [cyan]memnexus server[/cyan] - Start API server',
            title="Project Status",
            border_style="cyan",
        ))
        
    except Exception as e:
        # Fallback to basic status
        console.print(Panel.fit(
            f"[bold]Project:[/bold] {project_path.name}\n"
            f"[bold]Path:[/bold] {project_path}\n"
            f"[bold]Status:[/bold] Initialized (memory not loaded)\n\n"
            f"[yellow]Note:[/yellow] {e}\n\n"
            f"[bold]Commands:[/bold]\n"
            f'  [cyan]memnexus index[/cyan] - Index your codebase\n'
            f'  [cyan]memnexus server[/cyan] - Start API server',
            title="Project Status",
            border_style="cyan",
        ))


@app.command()
def index(
    path: Optional[str] = typer.Option(".", "--path", "-p", help="Project path"),
    git: bool = typer.Option(True, "--git/--no-git", help="Index Git history"),
    code: bool = typer.Option(False, "--code/--no-code", help="Index codebase (Week 3)"),
    limit: int = typer.Option(1000, "--limit", "-l", help="Max Git commits to index"),
):
    """Index project into memory.
    
    Examples:
        memnexus index              # Index Git history
        memnexus index --git        # Same as above
        memnexus index --code       # Also index code (Week 3)
    """
    project_path = _get_project_path(path)
    
    console.print(Panel.fit(
        f"Indexing project: [bold]{project_path.name}[/bold]\n"
        f"Git: {'[green]Yes[/green]' if git else '[yellow]No[/yellow]'}\n"
        f"Code: {'[green]Yes[/green]' if code else '[yellow]No[/yellow]'} (Week 3)",
        title="Indexing",
        border_style="blue",
    ))
    
    async def do_index():
        try:
            memory = await CodeMemory.init(project_path)
            
            if git:
                console.print("Indexing Git history...")
                result = await memory.index_git_history(limit=limit)
                indexed = result.get('commits_indexed', 0)
                total = result.get('total_commits', 0)
                console.print(f"[green]✓[/green] Indexed {indexed} commits (from {total} total)")
                
                errors = result.get('errors', [])
                if errors:
                    console.print(f"[yellow]⚠[/yellow] {len(errors)} errors during indexing")
            
            if code:
                console.print("Indexing codebase...")
                count = await memory.index_codebase()
                console.print(f"[green]✓[/green] Indexed {count} symbols")
                if count == 0:
                    console.print("[yellow]Note:[/yellow] Code indexing is Week 3 feature")
            
            stats = memory.get_stats()
            console.print(Panel.fit(
                f"Total memories: [bold]{stats['total_memories']}[/bold]\n"
                f"Git commits: [bold]{stats['git_commits_indexed']}[/bold]\n"
                f"Code symbols: [bold]{stats['code_symbols_indexed']}[/bold]",
                title="Indexing Complete",
                border_style="green",
            ))
            
        except Exception as e:
            console.print(Panel.fit(
                f"Indexing failed:\n[red]{e}[/red]",
                title="Error",
                border_style="red",
            ))
            raise typer.Exit(1)
    
    asyncio.run(do_index())


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    path: Optional[str] = typer.Option(".", "--path", "-p", help="Project path"),
    limit: int = typer.Option(5, "--limit", "-n", help="Max results"),
    git_only: bool = typer.Option(False, "--git", help="Search Git history only"),
):
    """Search project memory.
    
    Examples:
        memnexus search "login authentication"
        memnexus search "auth changes" --git
        memnexus search "user model" --limit 10
    """
    project_path = _get_project_path(path)
    
    async def do_search():
        try:
            memory = await CodeMemory.init(project_path)
            
            if git_only:
                from memnexus.code_memory import GitSearchResult
                results = await memory.query_git_history(query, limit=limit)
                
                if not results:
                    console.print("[yellow]No Git history results found.[/yellow]")
                    console.print("Try running: [cyan]memnexus index --git[/cyan]")
                    return
                
                # Display Git results in a special format
                console.print(f"\n[bold]Git History Results:[/bold] '{query}'\n")
                for r in results:
                    date_str = r.date.strftime("%Y-%m-%d %H:%M")
                    files_str = ", ".join(r.files_changed[:3])
                    if len(r.files_changed) > 3:
                        files_str += f" (+{len(r.files_changed) - 3} more)"
                    
                    console.print(Panel(
                        f"[bold cyan]{r.commit_hash}[/bold cyan] "
                        f"[green]{date_str}[/green] "
                        f"[yellow]{r.author.split('<')[0].strip()}[/yellow]\n\n"
                        f"{r.message}\n\n"
                        f"[dim]Files: {files_str}[/dim]",
                        border_style="blue",
                    ))
            else:
                results = await memory.search(query, limit=limit)
                
                if not results:
                    console.print("[yellow]No results found.[/yellow]")
                    console.print("Try running: [cyan]memnexus index[/cyan]")
                    return
                
                # Display general results
                table = Table(title=f"Search Results: '{query}'")
                table.add_column("Source", style="cyan")
                table.add_column("Content", style="white")
                table.add_column("Score", style="green", justify="right")
                
                for r in results:
                    content = r.content[:100] + "..." if len(r.content) > 100 else r.content
                    content = content.replace("\n", " ")
                    table.add_row(r.source, content, f"{r.score:.3f}")
                
                console.print(table)
            
            console.print(f"\n[dim]Found {len(results)} results[/dim]")
            
        except Exception as e:
            console.print(Panel.fit(
                f"Search failed:\n[red]{e}[/red]",
                title="Error",
                border_style="red",
            ))
            raise typer.Exit(1)
    
    asyncio.run(do_search())


@app.command()
def server(
    path: Optional[str] = typer.Option(".", "--path", "-p", help="Project path"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8080, "--port", "-p", help="Port to bind to"),
):
    """Start MemNexus API server.
    
    The server provides HTTP API for other tools to access memory.
    
    Examples:
        memnexus server                    # Start on default port
        memnexus server --port 3000        # Start on port 3000
        memnexus server --path ./project   # Serve specific project
    """
    from memnexus.server import start_server
    
    project_path = _get_project_path(path)
    
    console.print(Panel.fit(
        f"Starting MemNexus Code Memory Server\n"
        f"Project: [cyan]{project_path}[/cyan]\n"
        f"URL: [green]http://{host}:{port}[/green]\n\n"
        f"API Endpoints:\n"
        f"  GET  /health          - Health check\n"
        f"  GET  /stats           - Project stats\n"
        f"  GET  /api/v1/search   - Search memories\n"
        f"  POST /api/v1/memory   - Add memory\n"
        f"  POST /api/v1/git/index - Index Git history",
        title="Server",
        border_style="green",
    ))
    
    start_server(project_path=str(project_path), host=host, port=port)


# Legacy commands (marked as deprecated)
@app.command(hidden=True)
def session_list():
    """[Deprecated] Use API or library directly."""
    console.print("[yellow]Deprecated:[/yellow] Session management moved to library API.")
    console.print("Use: from memnexus import CodeMemory")


if __name__ == "__main__":
    app()
