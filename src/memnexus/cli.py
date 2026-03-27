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
    code: bool = typer.Option(False, "--code/--no-code", help="Index codebase"),
    limit: int = typer.Option(1000, "--limit", "-l", help="Max Git commits to index"),
    language: Optional[str] = typer.Option(None, "--lang", help="Language to index (python, javascript, typescript)"),
):
    """Index project into memory.
    
    Examples:
        memnexus index              # Index Git history
        memnexus index --git        # Same as above
        memnexus index --code       # Index code (Python by default)
        memnexus index --code --lang python
        memnexus index --git --code  # Index both
    """
    project_path = _get_project_path(path)
    
    console.print(Panel.fit(
        f"Indexing project: [bold]{project_path.name}[/bold]\n"
        f"Git: {'[green]Yes[/green]' if git else '[yellow]No[/yellow]'}\n"
        f"Code: {'[green]Yes[/green]' if code else '[yellow]No[/yellow]'}",
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
                languages = [language] if language else None
                
                def progress(current, total, file):
                    if current % 10 == 0 or current == total:
                        console.print(f"  [{current}/{total}] {file}")
                
                result = await memory.index_codebase(
                    languages=languages,
                    progress_callback=progress
                )
                
                indexed = result.get('symbols_indexed', 0)
                files = result.get('files_processed', 0)
                console.print(f"[green]✓[/green] Indexed {indexed} symbols from {files} files")
                
                errors = result.get('errors', [])
                if errors:
                    console.print(f"[yellow]⚠[/yellow] {len(errors)} errors during indexing")
            
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
    code_only: bool = typer.Option(False, "--code", help="Search code only"),
    symbol_type: Optional[str] = typer.Option(None, "--type", help="Filter by symbol type (function, class, method)"),
):
    """Search project memory.
    
    Examples:
        memnexus search "login authentication"
        memnexus search "auth changes" --git
        memnexus search "user model" --limit 10
        memnexus search "def authenticate" --code --type function
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
            
            elif code_only:
                results = await memory.search_code(
                    query, 
                    limit=limit,
                    symbol_type=symbol_type
                )
                
                if not results:
                    console.print("[yellow]No code results found.[/yellow]")
                    console.print("Try running: [cyan]memnexus index --code[/cyan]")
                    return
                
                # Display code results
                console.print(f"\n[bold]Code Search Results:[/bold] '{query}'\n")
                for r in results:
                    meta = r.metadata or {}
                    symbol_name = meta.get('symbol_name', 'Unknown')
                    symbol_type = meta.get('symbol_type', 'unknown')
                    file_path = meta.get('file_path', 'unknown')
                    line = meta.get('start_line', 0)
                    
                    # Get signature if available
                    signature = meta.get('signature', '')
                    docstring = meta.get('docstring', '')
                    
                    content_parts = []
                    if signature:
                        content_parts.append(f"[cyan]{signature}[/cyan]")
                    if docstring:
                        doc_preview = docstring[:100] + "..." if len(docstring) > 100 else docstring
                        content_parts.append(f"[dim]{doc_preview}[/dim]")
                    
                    content = "\n".join(content_parts) if content_parts else r.content[:200]
                    
                    console.print(Panel(
                        f"[bold]{symbol_name}[/bold] [yellow]({symbol_type})[/yellow]\n"
                        f"[dim]{file_path}:{line}[/dim]\n\n"
                        f"{content}",
                        border_style="green",
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


@app.command()
def install_plugin(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing plugin"),
):
    """Install Kimi CLI plugin.
    
    Copies the MemNexus plugin files to ~/.kimi/plugins/memnexus/
    After installation, you can use /memory commands in Kimi CLI.
    """
    import shutil
    
    # Source: plugin files bundled with the package
    src_dir = Path(__file__).parent / "kimi_plugin"
    
    if not src_dir.exists():
        console.print(Panel.fit(
            "[bold red]Plugin files not found![/bold red]\n\n"
            "The kimI_plugin directory is missing from the package.\n"
            "Please install from source or report this issue.",
            title="Installation Failed",
            border_style="red",
        ))
        raise typer.Exit(1)
    
    # Destination: Kimi CLI plugins directory
    kimi_dir = Path.home() / ".kimi" / "plugins"
    dst_dir = kimi_dir / "memnexus"
    
    # Create parent directory if needed
    kimi_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already installed
    if dst_dir.exists() and not force:
        console.print(Panel.fit(
            f"Plugin already installed at:\n"
            f"[yellow]{dst_dir}[/yellow]\n\n"
            f"Use [bold]--force[/bold] to reinstall.",
            title="Already Installed",
            border_style="yellow",
        ))
        raise typer.Exit(0)
    
    # Backup existing installation
    if dst_dir.exists():
        backup_dir = dst_dir.with_suffix(".backup")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(dst_dir, backup_dir)
        shutil.rmtree(dst_dir)
        console.print(f"[dim]Backed up existing plugin to {backup_dir}[/dim]")
    
    # Copy plugin files
    try:
        shutil.copytree(src_dir, dst_dir)
        
        console.print(Panel.fit(
            f"[bold green]✅ MemNexus Kimi plugin installed![/bold green]\n\n"
            f"Location: [cyan]{dst_dir}[/cyan]\n\n"
            f"[bold]Available commands:[/bold]\n"
            f"  /memory search <query>     - Search project memory\n"
            f"  /memory store <content>    - Store important info\n"
            f"  /memory status             - Check indexing status\n"
            f"  /memory index              - Index project\n"
            f"  /memory find <symbol>      - Find code symbol\n"
            f"  /memory history <file>     - Get file history\n\n"
            f"[dim]Next steps:[/dim]\n"
            f"1. cd your-project\n"
            f"2. memnexus init\n"
            f"3. memnexus index --git --code\n"
            f"4. Start Kimi CLI and use /memory commands",
            title="Installation Complete",
            border_style="green",
        ))
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]Installation failed:[/bold red]\n{str(e)}",
            title="Error",
            border_style="red",
        ))
        raise typer.Exit(1)


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
