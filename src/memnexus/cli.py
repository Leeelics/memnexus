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


# Phase 2: ACP Protocol Commands

@app.command()
def acp_connect(
    session_id: str = typer.Argument(..., help="Session ID"),
    cli: str = typer.Option("claude", "--cli", "-c", help="CLI tool to connect"),
    name: str = typer.Option(None, "--name", "-n", help="Agent name"),
    working_dir: str = typer.Option(".", "--dir", "-d", help="Working directory"),
):
    """Connect an agent via ACP protocol.
    
    Establishes a native ACP connection to Claude Code, Kimi CLI, etc.
    
    Examples:
        memnexus acp-connect sess_abc123 --cli claude
        memnexus acp-connect sess_abc123 -c kimi -n kimi-agent -d ./project
    """
    name = name or cli
    asyncio.run(_acp_connect(session_id, cli, name, working_dir))


async def _acp_connect(
    session_id: str,
    cli: str,
    name: str,
    working_dir: str,
):
    """Connect agent via ACP."""
    from memnexus.protocols.acp import ACPProtocolServer
    
    console.print(Panel.fit(
        f"Connecting via ACP protocol...\n\n"
        f"Session: [cyan]{session_id}[/cyan]\n"
        f"Agent: [magenta]{name}[/magenta]\n"
        f"CLI: [green]{cli}[/green]\n"
        f"Working Dir: [yellow]{working_dir}[/yellow]",
        title="ACP Connection",
        border_style="blue",
    ))
    
    manager = SessionManager()
    acp_server = ACPProtocolServer(manager)
    await acp_server.start()
    
    try:
        conn = await acp_server.connect_agent(
            cli=cli,
            session_id=session_id,
            working_dir=working_dir,
        )
        
        if conn:
            console.print("[green]✓[/green] ACP connection established")
            
            # Send a test prompt
            console.print("\nSending test prompt...")
            async for event in conn.send_prompt("Hello, please introduce yourself briefly."):
                if event.type.value == "message":
                    msg = event.data.get("message", "")
                    console.print(f"[blue]{name}:[/blue] {msg}")
                elif event.type.value == "error":
                    console.print(f"[red]Error:[/red] {event.data}")
                    
            await conn.close()
        else:
            console.print("[red]✗ Failed to establish ACP connection[/red]")
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
    finally:
        await acp_server.stop()


# Phase 2: RAG Commands

@app.command()
def rag_ingest(
    session_id: str = typer.Argument(..., help="Session ID"),
    file_path: str = typer.Argument(..., help="File path to ingest"),
):
    """Ingest a file into RAG pipeline.
    
    Examples:
        memnexus rag-ingest sess_abc123 README.md
        memnexus rag-ingest sess_abc123 src/main.py
    """
    asyncio.run(_rag_ingest(session_id, file_path))


async def _rag_ingest(session_id: str, file_path: str):
    """Ingest file into RAG."""
    from memnexus.memory.rag import RAGPipeline
    from pathlib import Path
    
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        return
    
    console.print(f"Ingesting [cyan]{file_path}[/cyan]...")
    
    pipeline = RAGPipeline(session_id=session_id)
    await pipeline.initialize()
    
    try:
        chunk_ids = await pipeline.ingest_file(file_path)
        console.print(f"[green]✓[/green] Ingested {len(chunk_ids)} chunks")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


@app.command()
def rag_query(
    session_id: str = typer.Argument(..., help="Session ID"),
    query: str = typer.Argument(..., help="Query text"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
):
    """Query the RAG pipeline.
    
    Performs semantic search over ingested documents.
    
    Examples:
        memnexus rag-query sess_abc123 "What is the architecture?"
        memnexus rag-query sess_abc123 "API endpoints" -k 10
    """
    asyncio.run(_rag_query(session_id, query, top_k))


async def _rag_query(session_id: str, query: str, top_k: int):
    """Query RAG pipeline."""
    from memnexus.memory.rag import RAGPipeline
    
    console.print(f"Querying: [cyan]'{query}'[/cyan]")
    
    pipeline = RAGPipeline(session_id=session_id)
    await pipeline.initialize()
    
    try:
        results = await pipeline.query_with_context(query, top_k)
        
        console.print(f"\n[green]Found {len(results['results'])} results:[/green]\n")
        
        for i, result in enumerate(results['results'], 1):
            console.print(Panel(
                f"{result['text'][:300]}...",
                title=f"[{i}] {result['source']} (score: {result['score']:.3f})",
                border_style="blue",
            ))
            
        if results['sources']:
            console.print(f"\n[dim]Sources: {', '.join(results['sources'])}[/dim]")
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


# Phase 2: Sync Commands

@app.command()
def sync_watch(
    session_id: str = typer.Argument(..., help="Session ID"),
):
    """Watch real-time memory sync for a session.
    
    Displays all memory changes in real-time.
    
    Example:
        memnexus sync-watch sess_abc123
    """
    asyncio.run(_sync_watch(session_id))


async def _sync_watch(session_id: str):
    """Watch memory sync."""
    from memnexus.memory.sync import MemorySyncManager
    
    console.print(Panel.fit(
        f"Watching memory sync for session [cyan]{session_id}[/cyan]\n"
        f"Press Ctrl+C to stop",
        title="Memory Sync",
        border_style="green",
    ))
    
    sync_manager = MemorySyncManager(session_id=session_id)
    await sync_manager.initialize()
    
    # Set up event handler
    async def on_event(event):
        console.print(
            f"[blue][{event.source}][/blue] "
            f"[yellow]{event.event_type}:[/yellow] "
            f"{event.memory.content[:80]}..."
        )
    
    sync_manager.add_handler(on_event)
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping sync watch...[/yellow]")
    finally:
        await sync_manager.close()


# Phase 3: Orchestration Commands

@app.command()
def orchestrate(
    session_id: str = typer.Argument(..., help="Session ID"),
    strategy: str = typer.Option("sequential", "--strategy", "-s", help="Execution strategy"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Task config file"),
):
    """Start orchestration for a session.
    
    Coordinates multiple agents to work on complex tasks.
    
    Examples:
        memnexus orchestrate sess_abc123 --strategy parallel
        memnexus orchestrate sess_abc123 -c tasks.yaml
    """
    asyncio.run(_orchestrate(session_id, strategy, config_file))


async def _orchestrate(session_id: str, strategy: str, config_file: Optional[str]):
    """Run orchestration."""
    from memnexus.orchestrator.engine import OrchestratorEngine, OrchestrationTask
    from memnexus.core.session import AgentRole, ExecutionStrategy
    
    console.print(Panel.fit(
        f"Starting orchestration...\n\n"
        f"Session: [cyan]{session_id}[/cyan]\n"
        f"Strategy: [green]{strategy}[/green]",
        title="Orchestration",
        border_style="blue",
    ))
    
    # Create orchestrator
    orchestrator = OrchestratorEngine(session_manager)
    await orchestrator.initialize(session_id)
    
    # Create sample tasks if no config file
    tasks = [
        OrchestrationTask(
            id="task_1",
            name="Design Architecture",
            description="Design system architecture",
            role=AgentRole.ARCHITECT,
            prompt="Design the system architecture for this project",
        ),
        OrchestrationTask(
            id="task_2",
            name="Implement Backend",
            description="Implement backend API",
            role=AgentRole.BACKEND,
            prompt="Implement the backend API based on the architecture",
            dependencies=["task_1"],
        ),
        OrchestrationTask(
            id="task_3",
            name="Implement Frontend",
            description="Implement frontend UI",
            role=AgentRole.FRONTEND,
            prompt="Implement the frontend UI",
            dependencies=["task_1"],
        ),
        OrchestrationTask(
            id="task_4",
            name="Write Tests",
            description="Write integration tests",
            role=AgentRole.TESTER,
            prompt="Write comprehensive tests for the system",
            dependencies=["task_2", "task_3"],
        ),
    ]
    
    # Create plan
    plan = await orchestrator.create_plan(
        session_id=session_id,
        strategy=ExecutionStrategy(strategy),
        tasks=tasks,
    )
    
    console.print(f"\n[green]✓[/green] Plan created with {len(tasks)} tasks")
    console.print(f"[dim]Phases: {len(plan.phases)}[/dim]")
    
    # Progress callback
    def on_progress(event):
        if event.get("type") == "task_progress":
            task_id = event.get("task_id")
            status = event.get("data", {}).get("status")
            console.print(f"Task {task_id}: {status}")
    
    # Execute
    console.print("\n[blue]Executing plan...[/blue]\n")
    success = await orchestrator.execute_plan(plan, on_event=on_progress)
    
    if success:
        console.print("\n[green]✓[/green] Orchestration completed successfully")
    else:
        console.print("\n[red]✗[/red] Orchestration failed")
    
    await orchestrator.close(session_id)


@app.command()
def plan_show(
    session_id: str = typer.Argument(..., help="Session ID"),
):
    """Show execution plan for a session."""
    asyncio.run(_plan_show(session_id))


async def _plan_show(session_id: str):
    """Show execution plan."""
    from memnexus.orchestrator.engine import OrchestratorEngine
    
    orchestrator = OrchestratorEngine(session_manager)
    plan = orchestrator._plans.get(session_id)
    
    if not plan:
        console.print(f"[yellow]No plan found for session {session_id}[/yellow]")
        return
    
    # Display plan
    table = Table(title=f"Execution Plan: {session_id}")
    table.add_column("Task", style="cyan")
    table.add_column("Role", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Dependencies", style="yellow")
    
    for task in plan.tasks:
        table.add_row(
            task.name,
            task.role.value,
            task.state.value,
            ", ".join(task.dependencies) if task.dependencies else "None",
        )
    
    console.print(table)
    console.print(f"\nStrategy: [blue]{plan.strategy.value}[/blue]")
    console.print(f"Progress: [green]{plan.calculate_progress() * 100:.1f}%[/green]")


# Phase 3: Intervention Commands

@app.command()
def intervention_list(
    session_id: str = typer.Argument(..., help="Session ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
):
    """List interventions for a session."""
    asyncio.run(_intervention_list(session_id, status))


async def _intervention_list(session_id: str, status: Optional[str]):
    """List interventions."""
    from memnexus.orchestrator.intervention import HumanInterventionSystem, InterventionStatus
    
    intervention_system = HumanInterventionSystem()
    await intervention_system.initialize()
    
    if status:
        interventions = intervention_system.get_session_interventions(
            session_id, InterventionStatus(status)
        )
    else:
        interventions = intervention_system.get_session_interventions(session_id)
    
    if not interventions:
        console.print("[dim]No interventions found[/dim]")
        return
    
    table = Table(title=f"Interventions: {session_id}")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Title", style="green")
    table.add_column("Status", style="yellow")
    
    for i in interventions:
        table.add_row(i.id, i.type.value, i.title, i.status.value)
    
    console.print(table)


@app.command()
def intervention_resolve(
    intervention_id: str = typer.Argument(..., help="Intervention ID"),
    action: str = typer.Option(..., "--action", "-a", help="Action: approve, reject, modify"),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Resolution message"),
):
    """Resolve an intervention.
    
    Examples:
        memnexus intervention-resolve int_abc123 -a approve
        memnexus intervention-resolve int_abc123 -a reject -m "Needs changes"
    """
    asyncio.run(_intervention_resolve(intervention_id, action, message))


async def _intervention_resolve(intervention_id: str, action: str, message: Optional[str]):
    """Resolve an intervention."""
    from memnexus.orchestrator.intervention import HumanInterventionSystem
    
    intervention_system = HumanInterventionSystem()
    await intervention_system.initialize()
    
    resolution = {"action": action}
    if message:
        resolution["message"] = message
    
    point = await intervention_system.resolve(
        intervention_id, resolution, resolved_by="human"
    )
    
    if point:
        console.print(f"[green]✓[/green] Intervention {intervention_id} resolved with action: {action}")
    else:
        console.print(f"[red]✗[/red] Intervention {intervention_id} not found")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
