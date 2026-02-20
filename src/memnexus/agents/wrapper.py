"""CLI Wrapper for MemNexus - Wraps existing CLI tools (claude, kimi, codex)."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from memnexus.agents.base import AgentConfig, AgentStatus, BaseAgent
from memnexus.core.config import settings


class CLIWrapper(BaseAgent):
    """Wrapper for CLI-based AI agents (claude, kimi, codex).
    
    This wrapper intercepts the CLI process and adds MemNexus integration:
    - Syncs context/memory with MemNexus
    - Captures output for real-time monitoring
    - Allows MemNexus to inject messages/commands
    
    Example:
        wrapper = CLIWrapper(AgentConfig(
            name="claude-backend",
            cli="claude",
            working_dir="/path/to/project"
        ))
        await wrapper.start()
    """
    
    def __init__(self, config: AgentConfig, session_id: Optional[str] = None):
        super().__init__(config)
        self.session_id = session_id
        self._output_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
    
    async def start(self) -> bool:
        """Start the CLI process with MemNexus integration."""
        if self.status == AgentStatus.RUNNING:
            return True
        
        self.status = AgentStatus.STARTING
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.env)
            
            # Add MemNexus context to environment
            if self.session_id:
                env["MEMNEXUS_SESSION_ID"] = self.session_id
                env["MEMNEXUS_AGENT_NAME"] = self.config.name
                env["MEMNEXUS_ENABLED"] = "1"
            
            # Build command
            cmd = self._build_command()
            
            # Start process
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.config.working_dir,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            self.status = AgentStatus.RUNNING
            
            # Start output readers
            self._output_task = asyncio.create_task(
                self._read_stdout(),
                name=f"{self.config.name}-stdout"
            )
            self._stderr_task = asyncio.create_task(
                self._read_stderr(),
                name=f"{self.config.name}-stderr"
            )
            
            # Notify start
            self._notify(f"[MemNexus] Agent '{self.config.name}' started (PID: {self.process.pid})")
            
            return True
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self._notify(f"[MemNexus] Failed to start agent: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the CLI process."""
        if self.process is None:
            return True
        
        self.status = AgentStatus.STOPPED
        
        try:
            # Terminate process
            self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    self.process.wait(),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                # Force kill if needed
                self.process.kill()
                await self.process.wait()
            
            # Cancel output tasks
            if self._output_task:
                self._output_task.cancel()
                try:
                    await self._output_task
                except asyncio.CancelledError:
                    pass
            
            if self._stderr_task:
                self._stderr_task.cancel()
                try:
                    await self._stderr_task
                except asyncio.CancelledError:
                    pass
            
            self._notify(f"[MemNexus] Agent '{self.config.name}' stopped")
            return True
            
        except Exception as e:
            self._notify(f"[MemNexus] Error stopping agent: {e}")
            return False
    
    async def send_message(self, message: str) -> bool:
        """Send a message/command to the CLI process."""
        if self.process is None or self.process.stdin is None:
            return False
        
        try:
            self.process.stdin.write(f"{message}\n".encode())
            await self.process.stdin.drain()
            return True
        except Exception as e:
            self._notify(f"[MemNexus] Error sending message: {e}")
            return False
    
    def _build_command(self) -> list:
        """Build the command to execute."""
        cli = self.config.cli
        
        # Check if it's a known CLI tool
        if cli in ["claude", "kimi", "codex"]:
            # Use which to find full path
            import shutil
            cli_path = shutil.which(cli)
            if cli_path:
                return [cli_path]
        
        # Default: use as-is
        return cli.split() if " " in cli else [cli]
    
    async def _read_stdout(self) -> None:
        """Read stdout from the process."""
        if self.process is None or self.process.stdout is None:
            return
        
        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                output = line.decode().rstrip()
                self._notify(f"[{self.config.name}] {output}")
                
                # TODO: Sync to memory store if auto_sync enabled
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._notify(f"[MemNexus] Error reading stdout: {e}")
    
    async def _read_stderr(self) -> None:
        """Read stderr from the process."""
        if self.process is None or self.process.stderr is None:
            return
        
        try:
            while True:
                line = await self.process.stderr.readline()
                if not line:
                    break
                
                output = line.decode().rstrip()
                self._notify(f"[{self.config.name}:stderr] {output}")
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._notify(f"[MemNexus] Error reading stderr: {e}")


class CLILauncher:
    """Launcher for CLI agents in wrapper mode.
    
    Usage:
        launcher = CLILauncher("sess_123")
        await launcher.launch("claude", "backend-agent", "/path/to/project")
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self._wrappers: dict[str, CLIWrapper] = {}
    
    async def launch(
        self,
        cli: str,
        name: str,
        working_dir: str = ".",
        env: Optional[dict] = None,
    ) -> CLIWrapper:
        """Launch a CLI agent in wrapper mode."""
        config = AgentConfig(
            name=name,
            cli=cli,
            working_dir=working_dir,
            env=env or {},
        )
        
        wrapper = CLIWrapper(config, session_id=self.session_id)
        
        # Register callback to forward to memory store
        wrapper.on_output(lambda msg: self._on_output(name, msg))
        
        success = await wrapper.start()
        if not success:
            raise RuntimeError(f"Failed to start agent: {name}")
        
        self._wrappers[name] = wrapper
        return wrapper
    
    async def stop_all(self) -> None:
        """Stop all running wrappers."""
        for wrapper in self._wrappers.values():
            await wrapper.stop()
        self._wrappers.clear()
    
    def get_wrapper(self, name: str) -> Optional[CLIWrapper]:
        """Get a wrapper by name."""
        return self._wrappers.get(name)
    
    def _on_output(self, agent_name: str, message: str) -> None:
        """Handle output from agent."""
        # TODO: Store in memory
        pass
