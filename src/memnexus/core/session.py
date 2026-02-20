"""Session management for MemNexus."""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from memnexus.agents.wrapper import CLILauncher
    from memnexus.memory.context import ContextManager


class SessionStatus(str, Enum):
    """Session status."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class AgentRole(str, Enum):
    """Agent roles."""
    ARCHITECT = "architect"
    BACKEND = "backend"
    FRONTEND = "frontend"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DEVOPS = "devops"


class AgentStatus(str, Enum):
    """Agent status."""
    IDLE = "idle"
    PLANNING = "planning"
    CODING = "coding"
    REVIEWING = "reviewing"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


class AgentConfig(BaseModel):
    """Agent configuration."""
    role: AgentRole
    cli: str  # claude, kimi, codex, etc.
    protocol: str = "acp"  # acp, mcp
    model: Optional[str] = None
    working_dir: str = "."
    env: Dict[str, str] = Field(default_factory=dict)
    timeout: int = 300


class Agent(BaseModel):
    """Agent instance."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str
    config: AgentConfig
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    pid: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.config.role.value,
            "cli": self.config.cli,
            "status": self.status.value,
            "current_task": self.current_task,
            "created_at": self.created_at.isoformat(),
        }


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Task(BaseModel):
    """Task definition."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    agent_id: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    prompt: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionStrategy(str, Enum):
    """Execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    REVIEW = "review"
    AUTO = "auto"


class Session(BaseModel):
    """Session definition."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    description: str = ""
    status: SessionStatus = SessionStatus.CREATED
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    working_dir: str = "."
    agents: List[Agent] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Runtime components (not serialized)
    context_manager: Optional[Any] = Field(default=None, exclude=True)
    cli_launcher: Optional[Any] = Field(default=None, exclude=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "strategy": self.strategy.value,
            "working_dir": self.working_dir,
            "agent_count": len(self.agents),
            "task_count": len(self.tasks),
            "created_at": self.created_at.isoformat(),
        }


class SessionManager:
    """Manager for sessions with memory integration."""
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._context_managers: Dict[str, "ContextManager"] = {}
        self._cli_launchers: Dict[str, "CLILauncher"] = {}
    
    async def create(
        self,
        name: str,
        description: str = "",
        strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL,
        working_dir: str = ".",
    ) -> Session:
        """Create a new session."""
        session = Session(
            name=name,
            description=description,
            strategy=strategy,
            working_dir=working_dir,
        )
        self._sessions[session.id] = session
        
        # Initialize context manager
        await self._init_context_manager(session)
        
        return session
    
    async def _init_context_manager(self, session: Session) -> None:
        """Initialize context manager for a session."""
        from memnexus.memory.context import ContextManager
        
        context = ContextManager(session_id=session.id)
        await context.initialize()
        
        self._context_managers[session.id] = context
        session.context_manager = context
    
    async def _init_cli_launcher(self, session: Session) -> None:
        """Initialize CLI launcher for a session."""
        from memnexus.agents.wrapper import CLILauncher
        
        launcher = CLILauncher(session_id=session.id)
        self._cli_launchers[session.id] = launcher
        session.cli_launcher = launcher
    
    async def get(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self._sessions.get(session_id)
    
    async def list_all(self) -> List[Session]:
        """List all sessions."""
        return list(self._sessions.values())
    
    async def add_agent(self, session_id: str, config: AgentConfig) -> Optional[Agent]:
        """Add agent to session."""
        session = await self.get(session_id)
        if not session:
            return None
        
        agent = Agent(
            session_id=session_id,
            config=config,
        )
        session.agents.append(agent)
        return agent
    
    async def add_task(self, session_id: str, task: Task) -> Optional[Task]:
        """Add task to session."""
        session = await self.get(session_id)
        if not session:
            return None
        
        task.session_id = session_id
        session.tasks.append(task)
        return task
    
    async def update_status(
        self,
        session_id: str,
        status: SessionStatus,
    ) -> bool:
        """Update session status."""
        session = await self.get(session_id)
        if not session:
            return False
        
        session.status = status
        session.updated_at = datetime.utcnow()
        return True
    
    async def delete(self, session_id: str) -> bool:
        """Delete session and cleanup resources."""
        if session_id not in self._sessions:
            return False
        
        # Cleanup CLI launchers
        if session_id in self._cli_launchers:
            launcher = self._cli_launchers[session_id]
            await launcher.stop_all()
            del self._cli_launchers[session_id]
        
        # Cleanup context manager (keep memories for history)
        if session_id in self._context_managers:
            del self._context_managers[session_id]
        
        del self._sessions[session_id]
        return True
    
    async def launch_agent(
        self,
        session_id: str,
        cli: str,
        name: str,
        working_dir: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Launch an agent in wrapper mode.
        
        Args:
            session_id: Session ID
            cli: CLI tool to wrap (claude, kimi, codex)
            name: Agent name
            working_dir: Working directory (defaults to session's)
            
        Returns:
            Agent info if successful
        """
        session = await self.get(session_id)
        if not session:
            return None
        
        # Initialize launcher if needed
        if session_id not in self._cli_launchers:
            await self._init_cli_launcher(session)
        
        launcher = self._cli_launchers[session_id]
        work_dir = working_dir or session.working_dir
        
        try:
            wrapper = await launcher.launch(
                cli=cli,
                name=name,
                working_dir=work_dir,
            )
            
            # Register output to context manager
            if session.context_manager:
                wrapper.on_output(
                    lambda msg: asyncio.create_task(
                        session.context_manager.store_agent_output(
                            agent=name,
                            content=msg,
                            memory_type="agent_output",
                        )
                    )
                )
            
            return {
                "name": name,
                "cli": cli,
                "status": "running",
                "pid": wrapper.process.pid if wrapper.process else None,
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_context_manager(self, session_id: str) -> Optional["ContextManager"]:
        """Get context manager for a session."""
        return self._context_managers.get(session_id)
    
    async def search_context(
        self,
        session_id: str,
        query: str,
        limit: int = 10,
    ) -> Optional[List[Dict[str, Any]]]:
        """Search session context.
        
        Args:
            session_id: Session ID
            query: Search query
            limit: Maximum results
            
        Returns:
            List of relevant memories
        """
        context = self._context_managers.get(session_id)
        if not context:
            return None
        
        snapshot = await context.get_context(query, limit)
        
        return [
            {
                "id": m.id,
                "content": m.content[:200],  # Truncate for brevity
                "source": m.source,
                "type": m.memory_type,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in snapshot.relevant_memories
        ]


