"""Human Intervention System for MemNexus.

Allows human operators to pause, review, and control agent execution
at critical points.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import uuid


class InterventionType(str, Enum):
    """Types of intervention points."""
    APPROVAL = "approval"           # Require approval before proceeding
    REVIEW = "review"               # Review task output
    DECISION = "decision"           # Make a decision (multiple choice)
    MODIFICATION = "modification"   # Modify task parameters
    PAUSE = "pause"                 # Pause for manual intervention
    CHECKPOINT = "checkpoint"       # Progress checkpoint
    ERROR = "error"                 # Error requires attention


class InterventionStatus(str, Enum):
    """Status of intervention."""
    PENDING = "pending"
    WAITING_FOR_HUMAN = "waiting_for_human"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    OVERRIDDEN = "overridden"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class InterventionPoint:
    """Point where human intervention is required.
    
    Attributes:
        id: Unique identifier
        type: Type of intervention
        task_id: Associated task ID
        session_id: Session ID
        title: Human-readable title
        description: Detailed description
        context: Additional context data
        options: For decision interventions
        deadline: Optional timeout
        status: Current status
        created_at: Creation timestamp
        resolved_at: Resolution timestamp
        resolved_by: Who resolved it
        resolution: Resolution data
    """
    type: InterventionType
    task_id: str
    session_id: str
    title: str
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    options: List[Dict[str, Any]] = field(default_factory=list)
    deadline: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: InterventionStatus = InterventionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "options": self.options,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution": self.resolution,
        }
    
    def is_expired(self) -> bool:
        """Check if intervention has expired."""
        if self.deadline is None:
            return False
        return datetime.utcnow() > self.deadline
    
    def time_remaining(self) -> Optional[float]:
        """Get time remaining in seconds."""
        if self.deadline is None:
            return None
        remaining = (self.deadline - datetime.utcnow()).total_seconds()
        return max(0, remaining)


@dataclass
class InterventionPolicy:
    """Policy for automatic interventions.
    
    Defines when and how interventions should be triggered.
    """
    name: str
    trigger_conditions: List[Dict[str, Any]] = field(default_factory=list)
    auto_approve_after: Optional[float] = None  # Seconds
    require_approval_for: List[str] = field(default_factory=list)
    notify_channels: List[str] = field(default_factory=lambda: ["web", "log"])
    escalation_timeout: Optional[float] = None
    
    def should_intervene(self, context: Dict[str, Any]) -> bool:
        """Check if intervention should be triggered."""
        for condition in self.trigger_conditions:
            if self._check_condition(condition, context):
                return True
        return False
    
    def _check_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check a single condition."""
        field = condition.get("field")
        operator = condition.get("operator", "equals")
        value = condition.get("value")
        
        context_value = context.get(field)
        
        if operator == "equals":
            return context_value == value
        elif operator == "not_equals":
            return context_value != value
        elif operator == "contains":
            return value in str(context_value)
        elif operator == "greater_than":
            return context_value is not None and context_value > value
        elif operator == "less_than":
            return context_value is not None and context_value < value
        
        return False


class HumanInterventionSystem:
    """System for managing human interventions.
    
    Provides:
    - Intervention point creation and tracking
    - Notification management
    - Resolution handling
    - Policy-based automatic interventions
    
    Example:
        intervention_system = HumanInterventionSystem()
        
        # Create intervention point
        point = await intervention_system.request_approval(
            session_id="sess_123",
            task_id="task_456",
            title="Review database schema",
            description="Please review the proposed schema changes",
        )
        
        # Wait for resolution
        resolution = await intervention_system.wait_for_resolution(point.id)
    """
    
    def __init__(self):
        self._interventions: Dict[str, InterventionPoint] = {}
        self._session_interventions: Dict[str, Set[str]] = {}
        self._callbacks: List[Callable[[InterventionPoint], None]] = []
        self._policies: Dict[str, InterventionPolicy] = {}
        self._waiting_futures: Dict[str, asyncio.Future] = {}
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize the intervention system."""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        # Add default policies
        self._add_default_policies()
    
    async def close(self) -> None:
        """Close the intervention system."""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all waiting futures
        for future in self._waiting_futures.values():
            if not future.done():
                future.cancel()
        self._waiting_futures.clear()
    
    def _add_default_policies(self) -> None:
        """Add default intervention policies."""
        # Policy: Require approval for destructive operations
        self._policies["destructive_ops"] = InterventionPolicy(
            name="destructive_ops",
            trigger_conditions=[
                {"field": "operation_type", "operator": "equals", "value": "delete"},
                {"field": "operation_type", "operator": "equals", "value": "drop"},
            ],
            require_approval_for=["delete", "drop", "remove"],
            notify_channels=["web", "log"],
        )
        
        # Policy: Check expensive operations
        self._policies["expensive_ops"] = InterventionPolicy(
            name="expensive_ops",
            trigger_conditions=[
                {"field": "estimated_cost", "operator": "greater_than", "value": 100},
            ],
            auto_approve_after=300,  # 5 minutes
            notify_channels=["web"],
        )
        
        # Policy: Error escalation
        self._policies["error_escalation"] = InterventionPolicy(
            name="error_escalation",
            trigger_conditions=[
                {"field": "error_count", "operator": "greater_than", "value": 3},
            ],
            escalation_timeout=600,  # 10 minutes
            notify_channels=["web", "log", "email"],
        )
    
    async def request_approval(
        self,
        session_id: str,
        task_id: str,
        title: str,
        description: str = "",
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> InterventionPoint:
        """Request human approval.
        
        Args:
            session_id: Session ID
            task_id: Task ID
            title: Short title
            description: Detailed description
            context: Additional context
            timeout: Timeout in seconds
            
        Returns:
            Intervention point
        """
        deadline = None
        if timeout:
            deadline = datetime.utcnow() + __import__('datetime').timedelta(seconds=timeout)
        
        point = InterventionPoint(
            type=InterventionType.APPROVAL,
            task_id=task_id,
            session_id=session_id,
            title=title,
            description=description,
            context=context or {},
            deadline=deadline,
        )
        
        await self._register_intervention(point)
        return point
    
    async def request_review(
        self,
        session_id: str,
        task_id: str,
        title: str,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> InterventionPoint:
        """Request human review of output.
        
        Args:
            session_id: Session ID
            task_id: Task ID
            title: Review title
            content: Content to review
            context: Additional context
            
        Returns:
            Intervention point
        """
        point = InterventionPoint(
            type=InterventionType.REVIEW,
            task_id=task_id,
            session_id=session_id,
            title=title,
            description=content,
            context=context or {},
            options=[
                {"id": "approve", "label": "Approve", "action": "approve"},
                {"id": "reject", "label": "Reject", "action": "reject"},
                {"id": "modify", "label": "Request Changes", "action": "modify"},
            ],
        )
        
        await self._register_intervention(point)
        return point
    
    async def request_decision(
        self,
        session_id: str,
        task_id: str,
        title: str,
        question: str,
        options: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> InterventionPoint:
        """Request a decision from human.
        
        Args:
            session_id: Session ID
            task_id: Task ID
            title: Decision title
            question: Question to answer
            options: List of options with id, label, action
            context: Additional context
            
        Returns:
            Intervention point
        """
        point = InterventionPoint(
            type=InterventionType.DECISION,
            task_id=task_id,
            session_id=session_id,
            title=title,
            description=question,
            context=context or {},
            options=options,
        )
        
        await self._register_intervention(point)
        return point
    
    async def create_checkpoint(
        self,
        session_id: str,
        task_id: str,
        title: str,
        progress: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> InterventionPoint:
        """Create a progress checkpoint.
        
        Args:
            session_id: Session ID
            task_id: Task ID
            title: Checkpoint title
            progress: Progress (0.0 - 1.0)
            context: Additional context
            
        Returns:
            Intervention point
        """
        point = InterventionPoint(
            type=InterventionType.CHECKPOINT,
            task_id=task_id,
            session_id=session_id,
            title=title,
            description=f"Progress: {progress * 100:.1f}%",
            context={"progress": progress, **(context or {})},
        )
        
        await self._register_intervention(point)
        return point
    
    async def report_error(
        self,
        session_id: str,
        task_id: str,
        error: str,
        severity: str = "error",
        context: Optional[Dict[str, Any]] = None,
    ) -> InterventionPoint:
        """Report an error requiring attention.
        
        Args:
            session_id: Session ID
            task_id: Task ID
            error: Error message
            severity: Error severity
            context: Additional context
            
        Returns:
            Intervention point
        """
        point = InterventionPoint(
            type=InterventionType.ERROR,
            task_id=task_id,
            session_id=session_id,
            title=f"Error: {error[:50]}",
            description=error,
            context={"severity": severity, **(context or {})},
        )
        
        await self._register_intervention(point)
        return point
    
    async def resolve(
        self,
        intervention_id: str,
        resolution: Dict[str, Any],
        resolved_by: str = "human",
    ) -> Optional[InterventionPoint]:
        """Resolve an intervention.
        
        Args:
            intervention_id: Intervention ID
            resolution: Resolution data
            resolved_by: Who resolved it
            
        Returns:
            Updated intervention point or None
        """
        point = self._interventions.get(intervention_id)
        if not point:
            return None
        
        if point.status in [InterventionStatus.RESOLVED, InterventionStatus.CANCELLED]:
            return point
        
        # Update status based on resolution
        action = resolution.get("action", "approve")
        if action == "approve":
            point.status = InterventionStatus.APPROVED
        elif action == "reject":
            point.status = InterventionStatus.REJECTED
        elif action == "modify":
            point.status = InterventionStatus.MODIFIED
        else:
            point.status = InterventionStatus.APPROVED
        
        point.resolved_at = datetime.utcnow()
        point.resolved_by = resolved_by
        point.resolution = resolution
        
        # Notify waiting futures
        future = self._waiting_futures.pop(intervention_id, None)
        if future and not future.done():
            future.set_result(point)
        
        # Notify callbacks
        self._notify_callbacks(point)
        
        return point
    
    async def wait_for_resolution(
        self,
        intervention_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[InterventionPoint]:
        """Wait for an intervention to be resolved.
        
        Args:
            intervention_id: Intervention ID
            timeout: Optional timeout in seconds
            
        Returns:
            Resolved intervention point or None if timeout
        """
        point = self._interventions.get(intervention_id)
        if not point:
            return None
        
        # Already resolved
        if point.status in [InterventionStatus.APPROVED, InterventionStatus.REJECTED, 
                           InterventionStatus.MODIFIED, InterventionStatus.OVERRIDDEN]:
            return point
        
        # Create future to wait on
        future: asyncio.Future[InterventionPoint] = asyncio.get_event_loop().create_future()
        self._waiting_futures[intervention_id] = future
        
        try:
            if timeout:
                return await asyncio.wait_for(future, timeout=timeout)
            else:
                return await future
        except asyncio.TimeoutError:
            return None
    
    def get_intervention(self, intervention_id: str) -> Optional[InterventionPoint]:
        """Get an intervention by ID."""
        return self._interventions.get(intervention_id)
    
    def get_session_interventions(
        self,
        session_id: str,
        status: Optional[InterventionStatus] = None,
    ) -> List[InterventionPoint]:
        """Get all interventions for a session."""
        intervention_ids = self._session_interventions.get(session_id, set())
        interventions = [self._interventions[iid] for iid in intervention_ids 
                        if iid in self._interventions]
        
        if status:
            interventions = [i for i in interventions if i.status == status]
        
        # Sort by created_at descending
        interventions.sort(key=lambda x: x.created_at, reverse=True)
        return interventions
    
    def get_pending_interventions(self) -> List[InterventionPoint]:
        """Get all pending interventions."""
        return [
            point for point in self._interventions.values()
            if point.status == InterventionStatus.PENDING
        ]
    
    def add_callback(self, callback: Callable[[InterventionPoint], None]) -> None:
        """Add a callback for intervention events."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[InterventionPoint], None]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    async def _register_intervention(self, point: InterventionPoint) -> None:
        """Register a new intervention."""
        self._interventions[point.id] = point
        
        # Track by session
        if point.session_id not in self._session_interventions:
            self._session_interventions[point.session_id] = set()
        self._session_interventions[point.session_id].add(point.id)
        
        # Update status
        point.status = InterventionStatus.WAITING_FOR_HUMAN
        
        # Notify
        self._notify_callbacks(point)
    
    def _notify_callbacks(self, point: InterventionPoint) -> None:
        """Notify all callbacks."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(point))
                else:
                    callback(point)
            except Exception as e:
                print(f"Error in intervention callback: {e}")
    
    async def _monitor_loop(self) -> None:
        """Monitor loop for intervention timeouts and auto-approvals."""
        while self._running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                now = datetime.utcnow()
                
                for point in list(self._interventions.values()):
                    # Check for expired interventions
                    if point.status == InterventionStatus.WAITING_FOR_HUMAN:
                        if point.is_expired():
                            await self._handle_expired(point)
                        
                        # Check for auto-approval
                        policy = self._policies.get("expensive_ops")
                        if policy and policy.auto_approve_after:
                            elapsed = (now - point.created_at).total_seconds()
                            if elapsed > policy.auto_approve_after:
                                await self.resolve(
                                    point.id,
                                    {"action": "auto_approve", "reason": "timeout"},
                                    resolved_by="system",
                                )
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in intervention monitor: {e}")
    
    async def _handle_expired(self, point: InterventionPoint) -> None:
        """Handle expired intervention."""
        point.status = InterventionStatus.EXPIRED
        
        # Notify waiting futures
        future = self._waiting_futures.pop(point.id, None)
        if future and not future.done():
            future.set_result(point)
        
        self._notify_callbacks(point)
    
    def add_policy(self, name: str, policy: InterventionPolicy) -> None:
        """Add an intervention policy."""
        self._policies[name] = policy
    
    def check_policy(
        self,
        policy_name: str,
        context: Dict[str, Any],
    ) -> bool:
        """Check if a policy triggers an intervention."""
        policy = self._policies.get(policy_name)
        if not policy:
            return False
        return policy.should_intervene(context)
