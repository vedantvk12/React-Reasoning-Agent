"""
Unit test suite for the ReAct Travel Planning Agent.
Verifies GoalAnalyzer, Planner, Tool execution, ReAct loop, and dynamic replanning.
"""

import unittest
from models import TaskStatus, TravelGoal
from planner import GoalAnalyzer, Planner
import tools
from agent import ReActAgent


class TestReActTravelAgent(unittest.TestCase):

    def setUp(self):
        self.goal_text = (
            "Plan a 2-day trip to Goa for 2 people within a budget of ₹10,000, "
            "including transportation, accommodation, food, and sightseeing."
        )

    def test_goal_analyzer_extraction(self):
        """Test extraction of structured parameters from natural language goal."""
        goal = GoalAnalyzer.parse_goal(self.goal_text)
        self.assertEqual(goal.destination, "Goa")
        self.assertEqual(goal.duration_days, 2)
        self.assertEqual(goal.num_people, 2)
        self.assertEqual(goal.budget_ceiling, 10000.0)

    def test_planner_subtask_decomposition(self):
        """Test that the planner generates 6 ordered subtasks."""
        goal = GoalAnalyzer.parse_goal(self.goal_text)
        tasks = Planner.create_initial_plan(goal)
        self.assertEqual(len(tasks), 6)
        expected_actions = [
            "calculate_transport",
            "search_accommodation",
            "estimate_food_cost",
            "select_sightseeing",
            "calculate_total_budget",
            "verify_budget"
        ]
        self.assertEqual([t.action for t in tasks], expected_actions)

    def test_tools_transport(self):
        """Test transportation cost calculation."""
        res = tools.calculate_transport(destination="Goa", num_people=2)
        self.assertTrue(res.success)
        self.assertEqual(res.cost, 2000.0)
        self.assertIn("Konkan Express", res.message)

    def test_tools_search_accommodation_failure(self):
        """Test simulated accommodation booking failure."""
        res = tools.search_accommodation(hotel_name="Sunset Beach Resort", simulate_failure=True)
        self.assertFalse(res.success)
        self.assertIn("unavailable", res.message)
        self.assertIsNotNone(res.failure_reason)

    def test_tools_replan_accommodation(self):
        """Test alternative accommodation booking."""
        res = tools.replan_accommodation()
        self.assertTrue(res.success)
        self.assertEqual(res.cost, 2000.0)
        self.assertIn("Palm Breeze Budget Guesthouse", res.message)

    def test_react_agent_full_run_with_replanning(self):
        """Test full ReAct loop execution with dynamic replanning."""
        goal = GoalAnalyzer.parse_goal(self.goal_text)
        agent = ReActAgent(goal=goal, simulate_failure=True)
        plan = agent.run()

        # Check that replanning took place
        self.assertTrue(plan.replanning_occurred)
        self.assertIsNotNone(plan.failed_task)
        self.assertEqual(plan.failed_task.action, "search_accommodation")
        self.assertIsNotNone(plan.replanned_task)
        self.assertEqual(plan.replanned_task.action, "replan_accommodation")

        # Check total steps: 6 initial + 1 replan = 7 execution steps
        self.assertEqual(len(plan.trace_history), 7)

        # Check financial totals
        self.assertEqual(plan.total_cost, 8200.0)
        self.assertEqual(plan.remaining_savings, 1800.0)
        self.assertTrue(plan.is_within_budget)

        # Check that each step has non-empty Thought, Action, Observation
        for step in plan.trace_history:
            self.assertTrue(len(step.thought) > 0)
            self.assertTrue(len(step.action) > 0)
            self.assertTrue(len(step.observation) > 0)


if __name__ == "__main__":
    unittest.main()
