"""Base agent implementation."""

import asyncio
import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from memnexus.core.config import settings


class AgentStatus(str, Enum):
    """Agent execution status."""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Agent configuration."""
    name: str
    cli: str  # claude, kimi, codex, etc.
    working_dir: str = "."
    env: Dict[str, str] = field(default_factory=dict)
    timeout: int = 300
    auto_sync: bool = True  # Auto sync memory with MemNexus


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.process: Optional[subprocess.Process] = None
        self._logs: List[str] = []
        self._callbacks: List[callable] = []
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the agent."""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the agent."""
        pass
    
    @abstractmethod
    async def send_message(self, message: str) -> bool:
        """Send message to agent."""
        pass
    
    def on_output(self, callback: callable) -> None:
        """Register output callback."""
        self._callbacks.append(callback)
    
    def _notify(self, output: str) -> None:
        """Notify all callbacks."""
        self._logs.append(output)
        for callback in self._callbacks:
            try:
                callback(output)
            except Exception:
                pass
    
    @property
    def logs(self) -> List[str]:
        """Get agent logs."""
        return self._logs.copy()
