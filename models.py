"""
Data models for the ReAct-based Travel Planning Agent.
Defines entities for Goals, Tasks, Tool execution results, and ReAct trace steps.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    """Execution status of an individual task."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REPLANNED = "REPLANNED"


@dataclass
class ActionResult:
    """Result returned by every Action Executor function."""
    success: bool
    action_name: str
    message: str
    cost: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Task:
    """Represents an atomic subtask within the execution plan."""
    task_id: str
    name: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    cost: float = 0.0
    result: Optional[ActionResult] = None
    is_replanned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class ExecutionStep:
    """Single step in the ReAct (Thought -> Action -> Observation) trace."""
    step_number: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str
    status: str
    cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TravelGoal:
    """Structured entity representing the parsed travel objective and constraints."""
    destination: str
    duration_days: int
    num_people: int
    budget_ceiling: float
    raw_goal: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TravelPlan:
    """Complete travel execution plan containing goals, tasks, and ReAct trace."""
    goal: TravelGoal
    initial_tasks: List[Task] = field(default_factory=list)
    current_tasks: List[Task] = field(default_factory=list)
    trace_history: List[ExecutionStep] = field(default_factory=list)
    replanning_occurred: bool = False
    failed_task: Optional[Task] = None
    replanning_reason: Optional[str] = None
    replanned_task: Optional[Task] = None
    total_cost: float = 0.0
    is_within_budget: bool = False
    remaining_savings: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal.to_dict(),
            "initial_tasks": [t.to_dict() for t in self.initial_tasks],
            "current_tasks": [t.to_dict() for t in self.current_tasks],
            "trace_history": [s.to_dict() for s in self.trace_history],
            "replanning_occurred": self.replanning_occurred,
            "failed_task": self.failed_task.to_dict() if self.failed_task else None,
            "replanning_reason": self.replanning_reason,
            "replanned_task": self.replanned_task.to_dict() if self.replanned_task else None,
            "total_cost": self.total_cost,
            "is_within_budget": self.is_within_budget,
            "remaining_savings": self.remaining_savings
        }
