"""Task Scheduler and Dependency Management."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from memnexus.core.session import AgentRole, ExecutionStrategy
from memnexus.orchestrator.engine import OrchestrationTask, TaskState


@dataclass
class DependencyGraph:
    """Task dependency graph.
    
    Manages task dependencies and calculates execution order.
    """
    
    def __init__(self):
        self._tasks: Dict[str, OrchestrationTask] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._dependents: Dict[str, Set[str]] = {}
    
    def add_task(self, task: OrchestrationTask) -> None:
        """Add a task to the graph."""
        self._tasks[task.id] = task
        self._dependencies[task.id] = set(task.dependencies)
        
        # Update dependents
        for dep_id in task.dependencies:
            if dep_id not in self._dependents:
                self._dependents[dep_id] = set()
            self._dependents[dep_id].add(task.id)
    
    def remove_task(self, task_id: str) -> None:
        """Remove a task from the graph."""
        if task_id in self._tasks:
            del self._tasks[task_id]
        
        # Remove from dependencies
        if task_id in self._dependencies:
            del self._dependencies[task_id]
        
        # Remove from dependents
        if task_id in self._dependents:
            del self._dependents[task_id]
        
        # Remove from other tasks' dependencies
        for deps in self._dependencies.values():
            deps.discard(task_id)
    
    def get_dependencies(self, task_id: str) -> Set[str]:
        """Get direct dependencies of a task."""
        return self._dependencies.get(task_id, set()).copy()
    
    def get_all_dependencies(self, task_id: str) -> Set[str]:
        """Get all transitive dependencies."""
        all_deps = set()
        to_visit = list(self.get_dependencies(task_id))
        
        while to_visit:
            dep_id = to_visit.pop()
            if dep_id not in all_deps:
                all_deps.add(dep_id)
                to_visit.extend(self.get_dependencies(dep_id))
        
        return all_deps
    
    def get_dependents(self, task_id: str) -> Set[str]:
        """Get tasks that depend on this task."""
        return self._dependents.get(task_id, set()).copy()
    
    def get_ready_tasks(self) -> List[str]:
        """Get tasks with all dependencies satisfied."""
        ready = []
        for task_id, deps in self._dependencies.items():
            task = self._tasks.get(task_id)
            if task and task.state == TaskState.PENDING:
                all_complete = all(
                    self._tasks.get(d) and self._tasks[d].state == TaskState.COMPLETED
                    for d in deps
                )
                if all_complete:
                    ready.append(task_id)
        return ready
    
    def detect_cycles(self) -> Optional[List[str]]:
        """Detect cycles in the dependency graph.
        
        Returns:
            List of task IDs forming a cycle, or None if no cycles.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {tid: WHITE for tid in self._tasks}
        path = []
        
        def dfs(task_id: str) -> Optional[List[str]]:
            color[task_id] = GRAY
            path.append(task_id)
            
            for dep_id in self._dependencies.get(task_id, set()):
                if dep_id not in color:
                    continue
                if color[dep_id] == GRAY:
                    # Found cycle
                    cycle_start = path.index(dep_id)
                    return path[cycle_start:] + [dep_id]
                if color[dep_id] == WHITE:
                    result = dfs(dep_id)
                    if result:
                        return result
            
            path.pop()
            color[task_id] = BLACK
            return None
        
        for task_id in self._tasks:
            if color[task_id] == WHITE:
                cycle = dfs(task_id)
                if cycle:
                    return cycle
        
        return None
    
    def topological_sort(self) -> List[str]:
        """Return tasks in topological order."""
        # Kahn's algorithm
        in_degree = {tid: 0 for tid in self._tasks}
        
        for task_id, deps in self._dependencies.items():
            in_degree[task_id] = len(deps)
        
        # Start with tasks having no dependencies
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            task_id = queue.pop(0)
            result.append(task_id)
            
            # Reduce in-degree of dependents
            for dependent in self._dependents.get(task_id, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check if all tasks were processed
        if len(result) != len(self._tasks):
            raise ValueError("Cycle detected in dependency graph")
        
        return result
    
    def get_critical_path(self) -> List[str]:
        """Calculate the critical path (longest dependency chain)."""
        # Calculate longest path to each task
        longest_path: Dict[str, List[str]] = {}
        
        def get_longest_path(task_id: str) -> List[str]:
            if task_id in longest_path:
                return longest_path[task_id]
            
            deps = self._dependencies.get(task_id, set())
            if not deps:
                longest_path[task_id] = [task_id]
                return [task_id]
            
            # Find longest path through dependencies
            longest = []
            for dep_id in deps:
                path = get_longest_path(dep_id)
                if len(path) > len(longest):
                    longest = path
            
            result = longest + [task_id]
            longest_path[task_id] = result
            return result
        
        # Find longest path overall
        critical_path = []
        for task_id in self._tasks:
            path = get_longest_path(task_id)
            if len(path) > len(critical_path):
                critical_path = path
        
        return critical_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "tasks": list(self._tasks.keys()),
            "dependencies": {
                tid: list(deps) for tid, deps in self._dependencies.items()
            },
            "cycle": self.detect_cycles(),
            "critical_path": self.get_critical_path(),
        }


@dataclass
class Schedule:
    """Task execution schedule."""
    session_id: str
    strategy: ExecutionStrategy
    phases: List[List[str]]  # Task IDs grouped by execution phase
    estimated_duration: timedelta = field(default_factory=lambda: timedelta())
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def get_current_phase(self, completed_tasks: Set[str]) -> int:
        """Get the current execution phase."""
        for i, phase in enumerate(self.phases):
            if not all(tid in completed_tasks for tid in phase):
                return i
        return len(self.phases)
    
    def get_parallelization_factor(self) -> float:
        """Calculate how parallelizable the schedule is.
        
        Returns:
            Ratio between 0.0 (fully sequential) and 1.0 (fully parallel)
        """
        if not self.phases:
            return 0.0
        
        total_tasks = sum(len(phase) for phase in self.phases)
        avg_tasks_per_phase = total_tasks / len(self.phases)
        
        return (avg_tasks_per_phase - 1) / (total_tasks - 1) if total_tasks > 1 else 0.0


class TaskScheduler:
    """Task scheduler for multi-agent orchestration.
    
    Creates optimized execution schedules based on task dependencies
    and available agents.
    
    Example:
        scheduler = TaskScheduler()
        
        # Add tasks
        scheduler.add_task(task1)
        scheduler.add_task(task2, dependencies=[task1.id])
        
        # Create schedule
        schedule = scheduler.create_schedule(
            session_id="sess_123",
            strategy=ExecutionStrategy.PARALLEL
        )
    """
    
    def __init__(self):
        self.graph = DependencyGraph()
        self._tasks: Dict[str, OrchestrationTask] = {}
    
    def add_task(
        self,
        task: OrchestrationTask,
        dependencies: Optional[List[str]] = None,
    ) -> None:
        """Add a task to the scheduler."""
        if dependencies:
            task.dependencies = dependencies
        
        self._tasks[task.id] = task
        self.graph.add_task(task)
    
    def remove_task(self, task_id: str) -> None:
        """Remove a task from the scheduler."""
        self.graph.remove_task(task_id)
        if task_id in self._tasks:
            del self._tasks[task_id]
    
    def create_schedule(
        self,
        session_id: str,
        strategy: ExecutionStrategy,
        available_agents: Optional[Dict[AgentRole, int]] = None,
    ) -> Schedule:
        """Create an optimized execution schedule.
        
        Args:
            session_id: Session ID
            strategy: Execution strategy
            available_agents: Optional map of role to count
            
        Returns:
            Execution schedule
        """
        # Check for cycles
        cycle = self.graph.detect_cycles()
        if cycle:
            raise ValueError(f"Cycle detected in dependencies: {cycle}")
        
        # Calculate phases
        phases = self._calculate_phases(strategy, available_agents)
        
        # Estimate duration
        estimated_duration = self._estimate_duration(phases)
        
        return Schedule(
            session_id=session_id,
            strategy=strategy,
            phases=phases,
            estimated_duration=estimated_duration,
        )
    
    def _calculate_phases(
        self,
        strategy: ExecutionStrategy,
        available_agents: Optional[Dict[AgentRole, int]],
    ) -> List[List[str]]:
        """Calculate execution phases."""
        if strategy == ExecutionStrategy.SEQUENTIAL:
            # All tasks in sequence
            return [[tid] for tid in self.graph.topological_sort()]
        
        elif strategy == ExecutionStrategy.PARALLEL:
            # Maximize parallelism
            return self.graph._calculate_phases(list(self._tasks.values()))
        
        elif strategy == ExecutionStrategy.REVIEW:
            # Same as parallel, but with review phase
            phases = self.graph._calculate_phases(list(self._tasks.values()))
            # Add review phase at the end
            phases.append([f"review_{tid}" for tid in self._tasks.keys()])
            return phases
        
        elif strategy == ExecutionStrategy.AUTO:
            # Optimize based on available agents
            return self._optimize_phases(available_agents)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _optimize_phases(
        self,
        available_agents: Optional[Dict[AgentRole, int]],
    ) -> List[List[str]]:
        """Optimize phases based on available agents."""
        if not available_agents:
            # Default to parallel
            return self.graph._calculate_phases(list(self._tasks.values()))
        
        # Group tasks by role
        tasks_by_role: Dict[AgentRole, List[str]] = {}
        for tid, task in self._tasks.items():
            if task.role not in tasks_by_role:
                tasks_by_role[task.role] = []
            tasks_by_role[task.role].append(tid)
        
        # Calculate phases respecting agent limits
        phases = []
        remaining = set(self._tasks.keys())
        completed = set()
        
        while remaining:
            phase = []
            role_usage: Dict[AgentRole, int] = {}
            
            # Sort tasks by number of dependencies (fewer first)
            sorted_tasks = sorted(
                remaining,
                key=lambda tid: len(self.graph.get_dependencies(tid))
            )
            
            for task_id in sorted_tasks:
                task = self._tasks.get(task_id)
                if not task:
                    continue
                
                # Check if dependencies are satisfied
                deps_satisfied = all(
                    dep in completed for dep in self.graph.get_dependencies(task_id)
                )
                if not deps_satisfied:
                    continue
                
                # Check agent availability
                role = task.role
                available = available_agents.get(role, 1)
                used = role_usage.get(role, 0)
                
                if used < available:
                    phase.append(task_id)
                    role_usage[role] = used + 1
            
            if not phase:
                # No progress possible (cycle or error)
                break
            
            phases.append(phase)
            completed.update(phase)
            remaining.difference_update(phase)
        
        return phases
    
    def _estimate_duration(self, phases: List[List[str]]) -> timedelta:
        """Estimate total execution duration."""
        # Assume 2 minutes per task on average
        total_tasks = sum(len(phase) for phase in phases)
        return timedelta(minutes=total_tasks * 2)
    
    def get_task_order(self) -> List[str]:
        """Get tasks in execution order."""
        return self.graph.topological_sort()
    
    def get_parallel_groups(self) -> List[List[str]]:
        """Get tasks grouped by parallel execution groups."""
        return self.graph._calculate_phases(list(self._tasks.values()))
    
    def analyze_bottlenecks(self) -> List[Dict[str, Any]]:
        """Analyze schedule bottlenecks.
        
        Returns:
            List of bottleneck descriptions
        """
        bottlenecks = []
        
        # Find tasks with many dependents
        for task_id in self._tasks:
            dependents = self.graph.get_dependents(task_id)
            if len(dependents) > 3:
                bottlenecks.append({
                    "type": "high_fanout",
                    "task_id": task_id,
                    "dependents": len(dependents),
                    "description": f"Task {task_id} has {len(dependents)} dependent tasks",
                })
        
        # Find long dependency chains
        critical_path = self.graph.get_critical_path()
        if len(critical_path) > 5:
            bottlenecks.append({
                "type": "long_chain",
                "length": len(critical_path),
                "path": critical_path,
                "description": f"Critical path has {len(critical_path)} tasks",
            })
        
        return bottlenecks
    
    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """Suggest schedule optimizations."""
        suggestions = []
        
        # Check for sequential tasks that could be parallel
        phases = self.get_parallel_groups()
        if len(phases) > len(self._tasks) / 2:
            suggestions.append({
                "type": "increase_parallelism",
                "description": "Consider breaking down dependencies to increase parallelism",
            })
        
        # Check for tasks with same role in same phase
        for i, phase in enumerate(phases):
            roles = {}
            for tid in phase:
                task = self._tasks.get(tid)
                if task:
                    roles[task.role] = roles.get(task.role, 0) + 1
            
            for role, count in roles.items():
                if count > 2:
                    suggestions.append({
                        "type": "agent_scaling",
                        "role": role.value,
                        "count": count,
                        "description": f"Consider adding more {role.value} agents for phase {i}",
                    })
        
        return suggestions


@dataclass
class ResourceAllocation:
    """Resource allocation for task execution."""
    task_id: str
    agent_id: Optional[str]
    role: AgentRole
    estimated_start: datetime
    estimated_end: datetime
    priority: int = 0
