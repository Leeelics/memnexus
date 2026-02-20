"""Multi-Agent Orchestration Engine.

Coordinates multiple agents working together on complex tasks,
manages task flow, and handles agent collaboration.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from memnexus.core.session import AgentRole, ExecutionStrategy


class TaskState(str, Enum):
    """Task execution state."""
    PENDING = "pending"
    WAITING_FOR_DEPENDENCIES = "waiting_deps"
    READY = "ready"
    ASSIGNED = "assigned"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class OrchestrationTask:
    """Enhanced task for orchestration."""
    id: str
    name: str
    description: str
    role: AgentRole
    prompt: str
    dependencies: List[str] = field(default_factory=list)
    state: TaskState = TaskState.PENDING
    assigned_agent: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "role": self.role.value,
            "state": self.state.value,
            "assigned_agent": self.assigned_agent,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
        }


@dataclass
class ExecutionPlan:
    """Execution plan for a session."""
    session_id: str
    strategy: ExecutionStrategy
    tasks: List[OrchestrationTask] = field(default_factory=list)
    phases: List[List[str]] = field(default_factory=list)  # Task IDs by phase
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_task(self, task_id: str) -> Optional[OrchestrationTask]:
        """Get task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_ready_tasks(self) -> List[OrchestrationTask]:
        """Get tasks that are ready to execute."""
        return [t for t in self.tasks if t.state == TaskState.READY]
    
    def get_completed_tasks(self) -> List[OrchestrationTask]:
        """Get completed tasks."""
        return [t for t in self.tasks if t.state == TaskState.COMPLETED]
    
    def calculate_progress(self) -> float:
        """Calculate execution progress (0.0 - 1.0)."""
        if not self.tasks:
            return 0.0
        completed = len([t for t in self.tasks 
                        if t.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]])
        return completed / len(self.tasks)


class TaskExecutor:
    """Executes individual tasks with agents."""
    
    def __init__(
        self,
        on_progress: Optional[Callable[[str, Dict], None]] = None,
    ):
        self.on_progress = on_progress
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute(
        self,
        task: OrchestrationTask,
        agent_connection: Any,
        context: Dict[str, Any],
    ) -> bool:
        """Execute a task with an agent."""
        task.state = TaskState.RUNNING
        task.started_at = datetime.utcnow()
        
        try:
            prompt = self._build_prompt(task, context)
            self._notify_progress(task.id, "started", {"prompt": prompt[:200]})
            
            # Execute with agent
            if hasattr(agent_connection, 'send_prompt'):
                result_parts = []
                async for event in agent_connection.send_prompt(prompt):
                    if event.type.value == "message":
                        result_parts.append(event.data.get("message", ""))
                
                result = "\n".join(result_parts)
            else:
                result = await self._execute_wrapper(agent_connection, prompt)
            
            task.result = result
            task.state = TaskState.COMPLETED
            task.completed_at = datetime.utcnow()
            
            self._notify_progress(task.id, "completed", {"result": result[:500]})
            return True
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                task.state = TaskState.RETRYING
                return False
            else:
                task.state = TaskState.FAILED
                task.completed_at = datetime.utcnow()
                self._notify_progress(task.id, "failed", {"error": str(e)})
                return False
    
    def _build_prompt(self, task: OrchestrationTask, context: Dict[str, Any]) -> str:
        """Build execution prompt with context."""
        parts = [f"# Task: {task.name}\n"]
        
        if task.description:
            parts.append(f"## Description\n{task.description}\n")
        
        if context.get("previous_results"):
            parts.append("\n## Context from Previous Tasks\n")
            for prev_task_id, result in context["previous_results"].items():
                parts.append(f"### {prev_task_id}\n{result[:500]}...\n")
        
        parts.append(f"\n## Instructions\n{task.prompt}\n")
        
        return "\n".join(parts)
    
    async def _execute_wrapper(self, agent_connection: Any, prompt: str) -> str:
        """Execute via wrapper mode."""
        return f"[Wrapper execution] Prompt: {prompt[:100]}..."
    
    def _notify_progress(self, task_id: str, status: str, data: Dict) -> None:
        """Notify progress callback."""
        if self.on_progress:
            self.on_progress(task_id, {"status": status, **data})
    
    async def cancel(self, task_id: str) -> None:
        """Cancel a running task."""
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            try:
                await self._running_tasks[task_id]
            except asyncio.CancelledError:
                pass
            del self._running_tasks[task_id]


class OrchestratorEngine:
    """Multi-Agent Orchestration Engine."""
    
    def __init__(self, session_manager: Any):
        self.session_manager = session_manager
        self._plans: Dict[str, ExecutionPlan] = {}
        self._executors: Dict[str, TaskExecutor] = {}
        self._running: bool = False
        self._callbacks: List[Callable[[str, Any], None]] = []
    
    async def initialize(self, session_id: str) -> None:
        """Initialize orchestrator for a session."""
        executor = TaskExecutor(
            on_progress=lambda tid, data: self._on_task_progress(session_id, tid, data)
        )
        
        self._executors[session_id] = executor
        self._running = True
    
    async def create_plan(
        self,
        session_id: str,
        strategy: ExecutionStrategy,
        tasks: List[OrchestrationTask],
    ) -> ExecutionPlan:
        """Create an execution plan."""
        plan = ExecutionPlan(
            session_id=session_id,
            strategy=strategy,
            tasks=tasks,
        )
        
        plan.phases = self._calculate_phases(tasks)
        
        for task in tasks:
            if not task.dependencies:
                task.state = TaskState.READY
            else:
                task.state = TaskState.WAITING_FOR_DEPENDENCIES
        
        self._plans[session_id] = plan
        return plan
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        on_event: Optional[Callable[[str, Any], None]] = None,
    ) -> bool:
        """Execute an execution plan."""
        if on_event:
            self._callbacks.append(on_event)
        
        session_id = plan.session_id
        executor = self._executors.get(session_id)
        if not executor:
            raise RuntimeError(f"Orchestrator not initialized for session {session_id}")
        
        try:
            if plan.strategy == ExecutionStrategy.SEQUENTIAL:
                return await self._execute_sequential(plan, executor)
            elif plan.strategy == ExecutionStrategy.PARALLEL:
                return await self._execute_parallel(plan, executor)
            elif plan.strategy == ExecutionStrategy.REVIEW:
                return await self._execute_with_review(plan, executor)
            elif plan.strategy == ExecutionStrategy.AUTO:
                return await self._execute_auto(plan, executor)
            else:
                raise ValueError(f"Unknown strategy: {plan.strategy}")
        finally:
            if on_event:
                self._callbacks.remove(on_event)
    
    async def _execute_sequential(
        self,
        plan: ExecutionPlan,
        executor: TaskExecutor,
    ) -> bool:
        """Execute tasks sequentially."""
        for task in plan.tasks:
            if not await self._wait_for_dependencies(plan, task):
                return False
            
            agent = await self._get_agent_for_task(plan.session_id, task)
            if not agent:
                task.state = TaskState.FAILED
                task.error = f"No agent available for role: {task.role}"
                return False
            
            context = self._build_context(plan, task)
            success = await executor.execute(task, agent, context)
            
            if not success and task.state == TaskState.FAILED:
                return False
            
            await self._update_dependent_tasks(plan, task)
        
        return True
    
    async def _execute_parallel(
        self,
        plan: ExecutionPlan,
        executor: TaskExecutor,
    ) -> bool:
        """Execute tasks in parallel where possible."""
        completed_tasks = set()
        failed = False
        
        while len(completed_tasks) < len(plan.tasks) and not failed:
            ready_tasks = [
                t for t in plan.tasks
                if t.state == TaskState.READY and t.id not in completed_tasks
            ]
            
            if not ready_tasks:
                await asyncio.sleep(0.1)
                continue
            
            async def execute_task(task: OrchestrationTask) -> bool:
                agent = await self._get_agent_for_task(plan.session_id, task)
                if not agent:
                    task.state = TaskState.FAILED
                    return False
                
                context = self._build_context(plan, task)
                success = await executor.execute(task, agent, context)
                
                if success:
                    completed_tasks.add(task.id)
                    await self._update_dependent_tasks(plan, task)
                
                return success or task.state != TaskState.FAILED
            
            results = await asyncio.gather(*[
                execute_task(t) for t in ready_tasks
            ])
            
            if not all(results):
                failed = True
        
        return not failed
    
    async def _execute_with_review(
        self,
        plan: ExecutionPlan,
        executor: TaskExecutor,
    ) -> bool:
        """Execute with review cycles."""
        if not await self._execute_sequential(plan, executor):
            return False
        
        review_tasks = []
        for task in plan.tasks:
            if task.state == TaskState.COMPLETED:
                review_task = OrchestrationTask(
                    id=f"review_{task.id}",
                    name=f"Review: {task.name}",
                    description=f"Review task {task.name}",
                    role=AgentRole.REVIEWER,
                    prompt=f"Review the following work:\n{task.result}",
                )
                review_tasks.append((task, review_task))
        
        for original_task, review_task in review_tasks:
            agent = await self._get_agent_for_task(plan.session_id, review_task)
            if agent:
                context = {"original_result": original_task.result}
                await executor.execute(review_task, agent, context)
        
        return True
    
    async def _execute_auto(
        self,
        plan: ExecutionPlan,
        executor: TaskExecutor,
    ) -> bool:
        """Auto-select execution strategy."""
        has_deps = any(t.dependencies for t in plan.tasks)
        
        if has_deps:
            return await self._execute_parallel(plan, executor)
        else:
            return await self._execute_sequential(plan, executor)
    
    async def _wait_for_dependencies(
        self,
        plan: ExecutionPlan,
        task: OrchestrationTask,
        timeout: float = 300.0,
    ) -> bool:
        """Wait for task dependencies to complete."""
        if not task.dependencies:
            return True
        
        start = datetime.utcnow()
        
        while True:
            all_completed = True
            for dep_id in task.dependencies:
                dep_task = plan.get_task(dep_id)
                if not dep_task:
                    return False
                if dep_task.state != TaskState.COMPLETED:
                    all_completed = False
                    break
                if dep_task.state == TaskState.FAILED:
                    task.state = TaskState.CANCELLED
                    task.error = f"Dependency failed: {dep_id}"
                    return False
            
            if all_completed:
                return True
            
            elapsed = (datetime.utcnow() - start).total_seconds()
            if elapsed > timeout:
                task.state = TaskState.FAILED
                task.error = "Timeout waiting for dependencies"
                return False
            
            await asyncio.sleep(0.1)
    
    async def _update_dependent_tasks(self, plan: ExecutionPlan, completed_task: OrchestrationTask) -> None:
        """Update tasks that depend on the completed task."""
        for task in plan.tasks:
            if completed_task.id in task.dependencies:
                all_complete = all(
                    plan.get_task(dep_id) and plan.get_task(dep_id).state == TaskState.COMPLETED
                    for dep_id in task.dependencies
                )
                if all_complete and task.state == TaskState.WAITING_FOR_DEPENDENCIES:
                    task.state = TaskState.READY
    
    def _calculate_phases(self, tasks: List[OrchestrationTask]) -> List[List[str]]:
        """Calculate execution phases based on dependencies."""
        if not tasks:
            return []
        
        phases = []
        remaining = set(t.id for t in tasks)
        completed = set()
        
        while remaining:
            ready = []
            for task_id in remaining:
                task = next((t for t in tasks if t.id == task_id), None)
                if task:
                    deps_satisfied = all(
                        dep in completed for dep in task.dependencies
                    )
                    if deps_satisfied:
                        ready.append(task_id)
            
            if not ready:
                break
            
            phases.append(ready)
            completed.update(ready)
            remaining.difference_update(ready)
        
        return phases
    
    async def _get_agent_for_task(
        self,
        session_id: str,
        task: OrchestrationTask,
    ) -> Optional[Any]:
        """Get or create an agent connection for a task."""
        session = await self.session_manager.get(session_id)
        if not session:
            return None
        
        for agent in session.agents:
            if agent.config.role == task.role and agent.status.value == "idle":
                return {"role": task.role, "agent_id": agent.id}
        
        return None
    
    def _build_context(self, plan: ExecutionPlan, task: OrchestrationTask) -> Dict[str, Any]:
        """Build execution context for a task."""
        context = {
            "session_id": plan.session_id,
            "strategy": plan.strategy.value,
        }
        
        if task.dependencies:
            previous_results = {}
            for dep_id in task.dependencies:
                dep_task = plan.get_task(dep_id)
                if dep_task and dep_task.result:
                    previous_results[dep_id] = dep_task.result
            context["previous_results"] = previous_results
        
        return context
    
    def _on_task_progress(self, session_id: str, task_id: str, data: Dict) -> None:
        """Handle task progress updates."""
        event = {
            "type": "task_progress",
            "session_id": session_id,
            "task_id": task_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(event))
                else:
                    callback(event)
            except Exception:
                pass
    
    async def pause(self, session_id: str) -> None:
        """Pause execution for a session."""
        pass
    
    async def resume(self, session_id: str) -> None:
        """Resume execution for a session."""
        pass
    
    async def cancel(self, session_id: str) -> None:
        """Cancel all tasks for a session."""
        executor = self._executors.get(session_id)
        if executor:
            for task_id in list(executor._running_tasks.keys()):
                await executor.cancel(task_id)
    
    async def close(self, session_id: str) -> None:
        """Close orchestrator for a session."""
        await self.cancel(session_id)
        
        if session_id in self._executors:
            del self._executors[session_id]
        
        if session_id in self._plans:
            del self._plans[session_id]
