"""
ReAct Reasoning Engine with Dynamic Replanning.
Coordinates the THOUGHT -> ACTION -> OBSERVATION loop, failure detection, and replanning.
"""

from typing import Any, Callable, Dict, List, Optional
import tools
from models import (
    ActionResult,
    ExecutionStep,
    Task,
    TaskStatus,
    TravelGoal,
    TravelPlan
)
from planner import Planner


class ReActAgent:
    """
    Executes the ReAct (Reason + Act) loop to fulfill travel planning objectives.
    Dynamically catches tool failures and dynamically revises the execution plan.
    """

    def __init__(self, goal: TravelGoal, simulate_failure: bool = True):
        self.goal = goal
        self.simulate_failure = simulate_failure
        self.tools: Dict[str, Callable[..., ActionResult]] = {
            "calculate_transport": tools.calculate_transport,
            "search_accommodation": tools.search_accommodation,
            "replan_accommodation": tools.replan_accommodation,
            "estimate_food_cost": tools.estimate_food_cost,
            "select_sightseeing": tools.select_sightseeing,
            "calculate_total_budget": tools.calculate_total_budget,
            "verify_budget": tools.verify_budget
        }
        self.trace_history: List[ExecutionStep] = []
        self.recorded_costs: Dict[str, float] = {
            "transportation": 0.0,
            "accommodation": 0.0,
            "food": 0.0,
            "sightseeing": 0.0
        }

    def _generate_thought(self, task: Task) -> str:
        """Formulates contextual reasoning rationale (THOUGHT) for the impending action."""
        if task.action == "calculate_transport":
            return "I need to arrange transportation before selecting accommodation."
        elif task.action == "search_accommodation":
            return "I will now check accommodation availability."
        elif task.action == "replan_accommodation":
            return "The original accommodation assumption is incorrect. I need to revise the plan."
        elif task.action == "estimate_food_cost":
            return "Accommodation is secured. Now I should estimate food expenses."
        elif task.action == "select_sightseeing":
            return "Food costs are estimated. Next, I will select sightseeing activities."
        elif task.action == "calculate_total_budget":
            return "All individual trip components have been calculated. I will now aggregate the total trip expenses."
        elif task.action == "verify_budget":
            formatted_ceiling = f"₹{self.goal.budget_ceiling:,.0f}"
            return f"I must now verify whether the total calculated expenses fit within the user's budget limit of {formatted_ceiling}."
        return f"Executing next necessary subtask: {task.name}."

    def _execute_action(self, action_name: str, params: Dict[str, Any]) -> ActionResult:
        """Dispatches action execution to the designated tool function with appropriate parameters."""
        tool_fn = self.tools.get(action_name)
        if not tool_fn:
            return ActionResult(
                success=False,
                action_name=action_name,
                message=f"Tool function '{action_name}' is not registered in the agent's tool catalog.",
                failure_reason="Unregistered tool"
            )

        kwargs = dict(params)
        if action_name == "search_accommodation":
            kwargs["simulate_failure"] = self.simulate_failure
        elif action_name == "calculate_total_budget":
            kwargs["recorded_costs"] = self.recorded_costs
        elif action_name == "verify_budget":
            kwargs["total_cost"] = sum(self.recorded_costs.values())
            kwargs["budget_ceiling"] = self.goal.budget_ceiling

        return tool_fn(**kwargs)

    def run(self) -> TravelPlan:
        """
        Executes the primary ReAct reasoning loop.
        Monitors environment observations and dynamically modifies the task sequence on failure.
        """
        initial_tasks = Planner.create_initial_plan(self.goal)
        current_tasks = [t for t in initial_tasks]
        plan = TravelPlan(
            goal=self.goal,
            initial_tasks=initial_tasks,
            current_tasks=current_tasks
        )

        task_index = 0
        while task_index < len(current_tasks):
            task = current_tasks[task_index]
            task.status = TaskStatus.IN_PROGRESS

            # 1. THOUGHT: Generate rationale for next action
            thought = self._generate_thought(task)

            # 2. ACTION: Invoke concrete tool function
            result = self._execute_action(task.action, task.params)
            task.result = result
            task.cost = result.cost

            # 3. OBSERVATION: Capture runtime environment feedback
            observation = result.message

            self.trace_history.append(
                ExecutionStep(
                    step_number=len(self.trace_history) + 1,
                    thought=thought,
                    action=f"{task.action}()",
                    action_input=task.params,
                    observation=observation,
                    status="SUCCESS" if result.success else "FAILED",
                    cost=result.cost
                )
            )

            # 4. FAILURE DETECTION & DYNAMIC REPLANNING
            if not result.success:
                task.status = TaskStatus.FAILED
                if task.action == "search_accommodation":
                    plan.replanning_occurred = True
                    plan.failed_task = task
                    plan.replanning_reason = result.failure_reason

                    # Generate replacement task dynamically
                    replanned_task = Planner.create_replanned_accommodation_task(task, self.goal)
                    plan.replanned_task = replanned_task

                    # Insert replanned task immediately after the failed step
                    current_tasks.insert(task_index + 1, replanned_task)
                    task_index += 1
                    continue
                else:
                    # Unhandled failure terminates sequence safely
                    break

            # Task succeeded: record cost and advance
            task.status = TaskStatus.SUCCESS
            if task.action == "calculate_transport":
                self.recorded_costs["transportation"] = result.cost
            elif task.action in ("search_accommodation", "replan_accommodation"):
                self.recorded_costs["accommodation"] = result.cost
            elif task.action == "estimate_food_cost":
                self.recorded_costs["food"] = result.cost
            elif task.action == "select_sightseeing":
                self.recorded_costs["sightseeing"] = result.cost
            elif task.action == "calculate_total_budget":
                plan.total_cost = result.cost
            elif task.action == "verify_budget":
                plan.is_within_budget = result.data.get("is_within_budget", False)
                plan.remaining_savings = result.data.get("remaining_savings", 0.0)

            task_index += 1

        plan.trace_history = self.trace_history
        plan.total_cost = sum(self.recorded_costs.values())
        plan.remaining_savings = self.goal.budget_ceiling - plan.total_cost
        plan.is_within_budget = plan.total_cost <= self.goal.budget_ceiling

        return plan
