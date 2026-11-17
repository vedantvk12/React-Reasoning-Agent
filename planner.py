"""
Goal Analyzer and Task Decomposition Planner.
Analyzes user natural language goals and generates initial / replanned execution subtasks.
"""

import re
from typing import List
from models import Task, TaskStatus, TravelGoal


class GoalAnalyzer:
    """Parses natural language travel goal into structured parameters."""

    @staticmethod
    def parse_goal(goal_text: str) -> TravelGoal:
        """
        Extracts destination, duration, party size, and budget ceiling from goal text.
        Example: 'Plan a 2-day trip to Goa for 2 people within a budget of ₹10,000...'
        """
        # Destination extraction
        dest_match = re.search(r'\bto\s+([A-Za-z\s]+?)(?=\s+(?:for|within|with|in|under|\d|$))', goal_text, re.IGNORECASE)
        destination = dest_match.group(1).strip() if dest_match else "Goa"

        # Duration extraction
        dur_match = re.search(r'(\d+)\s*[- ]*(?:day|days|night|nights)', goal_text, re.IGNORECASE)
        duration_days = int(dur_match.group(1)) if dur_match else 2

        # People extraction
        ppl_match = re.search(r'(\d+)\s*(?:people|persons|travelers|adults|members)', goal_text, re.IGNORECASE)
        num_people = int(ppl_match.group(1)) if ppl_match else 2

        # Budget ceiling extraction (supports ₹10,000, 10000, Rs. 10000, INR 10000)
        budget_match = re.search(r'(?:₹|rs\.?|inr|budget\s*(?:of|is|:)?\s*(?:₹|rs\.?)?)\s*([\d,]+)', goal_text, re.IGNORECASE)
        if budget_match:
            raw_val = budget_match.group(1).replace(",", "")
            try:
                budget_ceiling = float(raw_val)
            except ValueError:
                budget_ceiling = 10000.0
        else:
            budget_ceiling = 10000.0

        return TravelGoal(
            destination=destination,
            duration_days=duration_days,
            num_people=num_people,
            budget_ceiling=budget_ceiling,
            raw_goal=goal_text
        )


class Planner:
    """Decomposes goals into structured subtasks and dynamically constructs replacement tasks."""

    @staticmethod
    def create_initial_plan(goal: TravelGoal) -> List[Task]:
        """
        Decomposes the travel goal into 6 ordered subtasks.
        Each subtask binds to a concrete Python tool action.
        """
        return [
            Task(
                task_id="step_1",
                name="Calculate transportation expenses",
                action="calculate_transport",
                params={
                    "destination": goal.destination,
                    "num_people": goal.num_people
                }
            ),
            Task(
                task_id="step_2",
                name="Find suitable accommodation",
                action="search_accommodation",
                params={
                    "destination": goal.destination,
                    "duration_days": goal.duration_days,
                    "num_people": goal.num_people,
                    "hotel_name": "Sunset Beach Resort"
                }
            ),
            Task(
                task_id="step_3",
                name="Estimate food expenses",
                action="estimate_food_cost",
                params={
                    "duration_days": goal.duration_days,
                    "num_people": goal.num_people
                }
            ),
            Task(
                task_id="step_4",
                name="Select sightseeing activities",
                action="select_sightseeing",
                params={
                    "destination": goal.destination,
                    "duration_days": goal.duration_days,
                    "num_people": goal.num_people
                }
            ),
            Task(
                task_id="step_5",
                name="Calculate total expenses",
                action="calculate_total_budget",
                params={}
            ),
            Task(
                task_id="step_6",
                name="Verify budget compliance",
                action="verify_budget",
                params={
                    "budget_ceiling": goal.budget_ceiling
                }
            ),
        ]

    @staticmethod
    def create_replanned_accommodation_task(failed_task: Task, goal: TravelGoal) -> Task:
        """
        Generates an autonomous alternative task when initial accommodation fails.
        Selects verified available budget guesthouse lodging.
        """
        return Task(
            task_id="step_2_replan",
            name="Book alternative accommodation (Budget Guesthouse)",
            action="replan_accommodation",
            params={
                "destination": goal.destination,
                "duration_days": goal.duration_days,
                "num_people": goal.num_people,
                "preferred_type": "budget_guesthouse",
                "hotel_name": "Palm Breeze Budget Guesthouse"
            },
            is_replanned=True
        )
