"""CLI entry point for MemNexus."""

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

from memnexus.core.config import settings
from memnexus.core.session import (
    AgentConfig,
    ExecutionStrategy,
    SessionManager,
)

app = typer.Typer(
    name="memnexus",
    help="MemNexus - Multi-Agent Collaboration Orchestration System",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def callback():
    """MemNexus CLI."""
    pass


@app.command()
def version():
    """Show version information."""
    console.print(Panel.fit(
        f"[bold cyan]MemNexus[/bold cyan]\n"
        f"Version: {settings.APP_VERSION}\n"
        f"Data directory: {settings.DATA_DIR}",
        title="About",
        border_style="cyan",
    ))


@app.command()
def server(
    host: str = typer.Option(settings.HOST, "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(settings.PORT, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
    debug: bool = typer.Option(settings.DEBUG, "--debug", "-d", help="Enable debug mode"),
):
    """Start MemNexus server."""
    import uvicorn
    
    console.print(Panel.fit(
        f"Starting MemNexus server...\n"
        f"Host: [green]{host}[/green]\n"
        f"Port: [green]{port}[/green]\n"
        f"Debug: [yellow]{debug}[/yellow]",
        title="Server",
        border_style="green",
    ))
    
    uvicorn.run(
        "memnexus.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if debug else "info",
    )


@app.command()
def web(
    port: int = typer.Option(8501, "--port", "-p", help="Port for Streamlit"),
):
    """Start MemNexus web dashboard (Streamlit)."""
    import subprocess
    
    console.print(Panel.fit(
        f"Starting MemNexus Web Dashboard...\n"
        f"Port: [green]{port}[/green]",
        title="Web Dashboard",
        border_style="blue",
    ))
    
    # TODO: Implement Streamlit dashboard
    console.print("[yellow]Web dashboard coming soon![/yellow]")


@app.command()
def session_list():
    """List all sessions."""
    manager = SessionManager()
    
    table = Table(title="Sessions")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Agents", justify="right")
    table.add_column("Tasks", justify="right")
    table.add_column("Created", style="dim")
    
    # Mock data for now
    table.add_row(
        "sess_001",
        "User Auth System",
        "[green]running[/green]",
        "4",
        "12",
        "2026-02-20",
    )
    table.add_row(
        "sess_002",
        "API Migration",
        "[yellow]paused[/yellow]",
        "2",
        "5",
        "2026-02-19",
    )
    
    console.print(table)


@app.command()
def session_create(
    name: str = typer.Argument(..., help="Session name"),
    description: str = typer.Option("", "--description", "-d", help="Session description"),
    strategy: ExecutionStrategy = typer.Option(
        ExecutionStrategy.SEQUENTIAL,
        "--strategy",
        "-s",
        help="Execution strategy",
    ),
    agents: Optional[str] = typer.Option(
        None,
        "--agents",
        "-a",
        help="Comma-separated list of agents (e.g., claude,kimi)",
    ),
):
    """Create a new session."""
    asyncio.run(_create_session(name, description, strategy, agents))


async def _create_session(
    name: str,
    description: str,
    strategy: ExecutionStrategy,
    agents_str: Optional[str],
):
    """Create session async."""
    manager = SessionManager()
    
    session = await manager.create(
        name=name,
        description=description,
        strategy=strategy,
    )
    
    # Add agents if specified
    if agents_str:
        agent_names = [a.strip() for a in agents_str.split(",")]
        for name in agent_names:
            await manager.add_agent(
                session.id,
                AgentConfig(role="backend", cli=name),
            )
    
    console.print(Panel.fit(
        f"Session created successfully!\n\n"
        f"ID: [cyan]{session.id}[/cyan]\n"
        f"Name: [magenta]{session.name}[/magenta]\n"
        f"Strategy: [green]{session.strategy.value}[/green]\n"
        f"Agents: [yellow]{len(session.agents)}[/yellow]",
        title="Session Created",
        border_style="green",
    ))


@app.command()
def session_start(
    session_id: str = typer.Argument(..., help="Session ID"),
):
    """Start a session."""
    console.print(f"Starting session [cyan]{session_id}[/cyan]...")
    # TODO: Implement session start
    console.print("[yellow]Session start coming soon![/yellow]")


@app.command()
def session_stop(
    session_id: str = typer.Argument(..., help="Session ID"),
):
    """Stop a session."""
    console.print(f"Stopping session [cyan]{session_id}[/cyan]...")
    # TODO: Implement session stop
    console.print("[yellow]Session stop coming soon![/yellow]")


@app.command()
def agent_list(
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Filter by session ID"),
):
    """List all agents."""
    table = Table(title="Agents")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Session", style="magenta")
    table.add_column("Role", style="green")
    table.add_column("CLI", style="blue")
    table.add_column("Status", style="yellow")
    
    # Mock data
    table.add_row("ag_001", "sess_001", "architect", "claude", "[green]idle[/green]")
    table.add_row("ag_002", "sess_001", "backend", "kimi", "[green]coding[/green]")
    table.add_row("ag_003", "sess_001", "frontend", "codex", "[yellow]waiting[/yellow]")
    
    console.print(table)


@app.command()
def agent_launch(
    session_id: str = typer.Argument(..., help="Session ID"),
    cli: str = typer.Argument(..., help="CLI tool to wrap (claude, kimi, codex)"),
    name: str = typer.Option(None, "--name", "-n", help="Agent name (defaults to cli)"),
    working_dir: str = typer.Option(".", "--dir", "-d", help="Working directory"),
):
    """Launch an agent in CLI wrapper mode.
    
    This wraps an existing CLI tool (claude, kimi, codex) with MemNexus
    integration, allowing it to share context with other agents.
    
    Examples:
        memnexus agent-launch sess_abc123 claude --name claude-backend
        memnexus agent-launch sess_abc123 kimi -n kimi-frontend -d ./frontend
    """
    name = name or cli
    asyncio.run(_launch_agent(session_id, cli, name, working_dir))


async def _launch_agent(
    session_id: str,
    cli: str,
    name: str,
    working_dir: str,
):
    """Launch agent async."""
    manager = SessionManager()
    
    # Create session if it doesn't exist
    session = await manager.get(session_id)
    if not session:
        console.print(f"[yellow]Session {session_id} not found, creating...[/yellow]")
        session = await manager.create(
            name=f"Session {session_id[:8]}",
            working_dir=working_dir,
        )
        # Update session_id to the new one
        session_id = session.id
    
    console.print(Panel.fit(
        f"Launching agent in wrapper mode...\n\n"
        f"Session: [cyan]{session_id}[/cyan]\n"
        f"Agent: [magenta]{name}[/magenta]\n"
        f"CLI: [green]{cli}[/green]\n"
        f"Working Dir: [yellow]{working_dir}[/yellow]",
        title="Agent Launch",
        border_style="blue",
    ))
    
    result = await manager.launch_agent(
        session_id=session_id,
        cli=cli,
        name=name,
        working_dir=working_dir,
    )
    
    if result and "error" not in result:
        console.print(f"[green]Agent started successfully![/green]")
        console.print(f"PID: {result.get('pid')}")
        
        # Keep running and show output
        launcher = manager._cli_launchers.get(session_id)
        if launcher:
            wrapper = launcher.get_wrapper(name)
            if wrapper:
                console.print("\n[dim]Agent output (Ctrl+C to stop):[/dim]\n")
                try:
                    while wrapper.status.value == "running":
                        # Show recent logs
                        logs = wrapper.logs[-5:]
                        for log in logs:
                            console.print(log)
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopping agent...[/yellow]")
                    await wrapper.stop()
    else:
        error = result.get("error", "Unknown error") if result else "Failed to start"
        console.print(f"[red]Failed to start agent: {error}[/red]")


@app.command()
def memory_search(
    session_id: str = typer.Argument(..., help="Session ID"),
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
):
    """Search session memory/context.
    
    Performs semantic search over the session's shared memory.
    
    Example:
        memnexus memory-search sess_abc123 "API endpoints"
        memnexus memory-search sess_abc123 "authentication" -l 5
    """
    asyncio.run(_search_memory(session_id, query, limit))


async def _search_memory(session_id: str, query: str, limit: int):
    """Search memory async."""
    manager = SessionManager()
    
    results = await manager.search_context(session_id, query, limit)
    
    if results is None:
        console.print(f"[red]Session {session_id} not found[/red]")
        return
    
    if not results:
        console.print(f"[yellow]No memories found for query: '{query}'[/yellow]")
        return
    
    table = Table(title=f"Memory Search: '{query}'")
    table.add_column("Source", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Content", style="green")
    table.add_column("Time", style="dim")
    
    for r in results:
        # Truncate content for display
        content = r["content"][:80] + "..." if len(r["content"]) > 80 else r["content"]
        table.add_row(
            r["source"],
            r["type"],
            content,
            r["timestamp"][:19],  # Just date-time, no timezone
        )
    
    console.print(table)
    console.print(f"\n[dim]Found {len(results)} results[/dim]")


@app.command()
def memory_stats(
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID"),
):
    """Show memory store statistics."""
    asyncio.run(_memory_stats(session_id))


async def _memory_stats(session_id: Optional[str]):
    """Get memory stats async."""
    from memnexus.memory.store import MemoryStore
    
    store = MemoryStore()
    await store.initialize()
    
    stats = await store.get_stats()
    
    console.print(Panel.fit(
        f"Total Entries: [cyan]{stats.get('total_entries', 0)}[/cyan]\n"
        f"Sessions: [magenta]{stats.get('sessions', 0)}[/magenta]\n"
        f"Types: [green]{stats.get('memory_types', {})}[/green]",
        title="Memory Statistics",
        border_style="blue",
    ))
    
    if session_id:
        # Show session-specific stats
        from memnexus.memory.context import ContextManager
        
        context = ContextManager(session_id=session_id, store=store)
        await context.initialize()
        
        memories = await context.get_conversation_history(limit=1000)
        console.print(f"\nSession [cyan]{session_id}[/cyan] has [yellow]{len(memories)}[/yellow] memories")


@app.command()
def wrapper_mode(
    session_id: str = typer.Argument(..., help="Session ID"),
    cli: str = typer.Argument(..., help="CLI command to wrap"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Agent name"),
):
    """Start CLI in wrapper mode (attach to existing session).
    
    This is the main Phase 1 feature - it wraps an existing CLI tool
    and connects it to a MemNexus session for context sharing.
    
    Examples:
        memnexus wrapper sess_abc123 claude
        memnexus wrapper sess_abc123 kimi -n my-agent
        memnexus wrapper sess_abc123 "claude --debug" -n debug-claude
    """
    name = name or cli.split()[0]
    asyncio.run(_wrapper_mode(session_id, cli, name))


async def _wrapper_mode(session_id: str, cli: str, name: str):
    """Run in wrapper mode."""
    manager = SessionManager()
    
    # Get or create session
    session = await manager.get(session_id)
    if not session:
        console.print(f"[yellow]Creating new session: {session_id}[/yellow]")
        session = await manager.create(
            name=f"Wrapper Session {session_id[:8]}",
        )
        session_id = session.id
    
    console.print(Panel.fit(
        f"Session: [cyan]{session_id}[/cyan]\n"
        f"Agent: [magenta]{name}[/magenta]\n"
        f"CLI: [green]{cli}[/green]\n\n"
        f"This CLI is now wrapped with MemNexus.\n"
        f"All output will be synced to shared memory.",
        title="Wrapper Mode",
        border_style="green",
    ))
    
    # Launch the agent
    result = await manager.launch_agent(
        session_id=session_id,
        cli=cli,
        name=name,
    )
    
    if result and "error" not in result:
        console.print("[green]✓[/green] Agent connected to MemNexus")
        
        # Monitor the agent
        launcher = manager._cli_launchers.get(session_id)
        if launcher:
            wrapper = launcher.get_wrapper(name)
            if wrapper:
                console.print("\n[dim]Monitoring output (Ctrl+C to detach):[/dim]\n")
                
                last_log_count = 0
                try:
                    while wrapper.status.value in ["running", "starting"]:
                        logs = wrapper.logs
                        if len(logs) > last_log_count:
                            for log in logs[last_log_count:]:
                                # Colorize based on content
                                if "[MemNexus]" in log:
                                    console.print(f"[blue]{log}[/blue]")
                                elif ":stderr]" in log:
                                    console.print(f"[red]{log}[/red]")
                                else:
                                    console.print(log)
                            last_log_count = len(logs)
                        await asyncio.sleep(0.1)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Detaching from agent...[/yellow]")
                    console.print("[dim]Agent continues running in background[/dim]")
    else:
        error = result.get("error", "Unknown error") if result else "Failed to start"
        console.print(f"[red]✗ Failed to start wrapper: {error}[/red]")


@app.command()
def config_show():
    """Show current configuration."""
    table = Table(title="Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("APP_NAME", settings.APP_NAME)
    table.add_row("APP_VERSION", settings.APP_VERSION)
    table.add_row("DEBUG", str(settings.DEBUG))
    table.add_row("ENV", settings.ENV)
    table.add_row("DATA_DIR", str(settings.DATA_DIR))
    table.add_row("HOST", settings.HOST)
    table.add_row("PORT", str(settings.PORT))
    table.add_row("DATABASE_URL", settings.DATABASE_URL)
    table.add_row("REDIS_URL", settings.REDIS_URL)
    table.add_row("LANCEDB_URI", settings.LANCEDB_URI)
    
    console.print(table)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
