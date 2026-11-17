"""
Action Executor Tools for the ReAct Travel Planning Agent.
Provides local deterministic catalogs and verification logic for travel operations.
No remote external APIs or keys required.
"""

from typing import Any, Dict, Optional
from models import ActionResult

# Local accommodation inventory database
ACCOMMODATION_CATALOG: Dict[str, Dict[str, Any]] = {
    "Sunset Beach Resort": {
        "type": "3-Star Beachfront Resort",
        "total_cost": 3000.0,
        "available": False,  # Programmatic inventory check simulates fully booked
        "reason": "Fully booked for the selected dates due to peak weekend season.",
        "location": "Baga Beach, North Goa"
    },
    "Palm Breeze Budget Guesthouse": {
        "type": "Cozy AC Budget Guesthouse",
        "total_cost": 2000.0,
        "available": True,
        "reason": None,
        "location": "Near Calangute Beach, North Goa"
    },
    "Grand Heritage Villa": {
        "type": "Luxury Heritage Resort",
        "total_cost": 7500.0,
        "available": True,
        "reason": None,
        "location": "Panaji, Central Goa"
    }
}

# Local transport catalog
TRANSPORT_CATALOG: Dict[str, Dict[str, Any]] = {
    "Konkan Express (AC 3-Tier Sleeper)": {
        "cost_per_person": 1000.0,
        "mode": "Train",
        "round_trip": True
    },
    "Goa Express (Sleeper Class)": {
        "cost_per_person": 600.0,
        "mode": "Train",
        "round_trip": True
    },
    "Intercity Flight": {
        "cost_per_person": 3500.0,
        "mode": "Flight",
        "round_trip": True
    }
}


def calculate_transport(
    destination: str = "Goa",
    num_people: int = 2,
    mode: str = "Konkan Express (AC 3-Tier Sleeper)",
    **kwargs: Any
) -> ActionResult:
    """Calculates round-trip transportation expenses for the travel group."""
    info = TRANSPORT_CATALOG.get(mode, TRANSPORT_CATALOG["Konkan Express (AC 3-Tier Sleeper)"])
    rate = info["cost_per_person"]
    total_cost = rate * num_people

    formatted_cost = f"₹{total_cost:,.0f}"
    formatted_rate = f"₹{rate:,.0f}"

    return ActionResult(
        success=True,
        action_name="calculate_transport",
        message=(
            f"Transportation estimated at {formatted_cost} "
            f"({mode} round-trip for {num_people} people at {formatted_rate} each)."
        ),
        cost=total_cost,
        data={
            "mode": mode,
            "cost_per_person": rate,
            "num_people": num_people,
            "total_cost": total_cost,
            "destination": destination
        }
    )


def search_accommodation(
    destination: str = "Goa",
    duration_days: int = 2,
    num_people: int = 2,
    hotel_name: str = "Sunset Beach Resort",
    simulate_failure: bool = True,
    **kwargs: Any
) -> ActionResult:
    """Queries hotel inventory for the destination and checks room availability."""
    hotel_info = ACCOMMODATION_CATALOG.get(hotel_name)

    if not hotel_info or not hotel_info["available"] or simulate_failure:
        reason = (
            hotel_info["reason"]
            if hotel_info and hotel_info.get("reason")
            else "Fully booked for the selected dates due to peak weekend season."
        )
        return ActionResult(
            success=False,
            action_name="search_accommodation",
            message=f"Selected hotel '{hotel_name}' is unavailable. ({reason})",
            cost=0.0,
            failure_reason=reason,
            data={"attempted_hotel": hotel_name, "available": False}
        )

    cost = hotel_info["total_cost"]
    return ActionResult(
        success=True,
        action_name="search_accommodation",
        message=f"Confirmed reservation at '{hotel_name}' for ₹{cost:,.0f}.",
        cost=cost,
        data={"name": hotel_name, "cost": cost, "type": hotel_info["type"]}
    )


def replan_accommodation(
    destination: str = "Goa",
    duration_days: int = 2,
    num_people: int = 2,
    preferred_type: str = "budget_guesthouse",
    hotel_name: str = "Palm Breeze Budget Guesthouse",
    **kwargs: Any
) -> ActionResult:
    """Autonomous recovery tool: selects an available budget alternative guesthouse."""
    alt_info = ACCOMMODATION_CATALOG.get(
        hotel_name, ACCOMMODATION_CATALOG["Palm Breeze Budget Guesthouse"]
    )
    cost = alt_info["total_cost"]

    return ActionResult(
        success=True,
        action_name="replan_accommodation",
        message=(
            f"Alternative guesthouse '{hotel_name}' successfully selected for ₹{cost:,.0f}. "
            f"Includes AC Double Room near beach with verified availability."
        ),
        cost=cost,
        data={
            "name": hotel_name,
            "cost": cost,
            "type": alt_info["type"],
            "location": alt_info.get("location", "Goa")
        }
    )


def estimate_food_cost(
    duration_days: int = 2,
    num_people: int = 2,
    cost_per_person_day: float = 750.0,
    cuisine_style: str = "Local Goan Beach Shacks & Authentic Thalis",
    **kwargs: Any
) -> ActionResult:
    """Estimates meal expenditures across all travelers for the entire trip."""
    total_cost = duration_days * num_people * cost_per_person_day
    formatted_total = f"₹{total_cost:,.0f}"
    formatted_daily = f"₹{cost_per_person_day:,.0f}"

    return ActionResult(
        success=True,
        action_name="estimate_food_cost",
        message=(
            f"Food expenses estimated at {formatted_total} "
            f"({duration_days} days x {num_people} people @ {formatted_daily}/person/day "
            f"for {cuisine_style})."
        ),
        cost=total_cost,
        data={
            "duration_days": duration_days,
            "num_people": num_people,
            "cost_per_person_day": cost_per_person_day,
            "total_cost": total_cost,
            "cuisine_style": cuisine_style
        }
    )


def select_sightseeing(
    destination: str = "Goa",
    duration_days: int = 2,
    num_people: int = 2,
    activities_description: str = "Fort Aguada, Calangute/Baga beaches, Old Goa churches & 2-day scooter rental",
    cost: float = 1200.0,
    **kwargs: Any
) -> ActionResult:
    """Curates landmark attractions and local transportation options."""
    formatted_cost = f"₹{cost:,.0f}"
    return ActionResult(
        success=True,
        action_name="select_sightseeing",
        message=(
            f"Sightseeing and local scooter rental estimated at {formatted_cost}. "
            f"Selected: {activities_description}."
        ),
        cost=cost,
        data={
            "destination": destination,
            "activities": activities_description,
            "total_cost": cost
        }
    )


def calculate_total_budget(
    recorded_costs: Optional[Dict[str, float]] = None,
    **kwargs: Any
) -> ActionResult:
    """Aggregates costs of all confirmed travel plan components."""
    if not recorded_costs:
        recorded_costs = {
            "transportation": 2000.0,
            "accommodation": 2000.0,
            "food": 3000.0,
            "sightseeing": 1200.0
        }

    total_cost = sum(recorded_costs.values())
    t_cost = recorded_costs.get("transportation", 0.0)
    a_cost = recorded_costs.get("accommodation", 0.0)
    f_cost = recorded_costs.get("food", 0.0)
    s_cost = recorded_costs.get("sightseeing", 0.0)

    msg = (
        f"Total expenses calculated at ₹{total_cost:,.0f} "
        f"(Transport: ₹{t_cost:,.0f}, Accommodation: ₹{a_cost:,.0f}, "
        f"Food: ₹{f_cost:,.0f}, Sightseeing: ₹{s_cost:,.0f})."
    )

    return ActionResult(
        success=True,
        action_name="calculate_total_budget",
        message=msg,
        cost=total_cost,
        data={"total_cost": total_cost, "breakdown": recorded_costs}
    )


def verify_budget(
    total_cost: float = 8200.0,
    budget_ceiling: float = 10000.0,
    **kwargs: Any
) -> ActionResult:
    """Verifies that final aggregated expenditures remain strictly within the budget ceiling."""
    is_within = total_cost <= budget_ceiling
    savings = budget_ceiling - total_cost

    if is_within:
        msg = (
            f"Plan is within budget. Total ₹{total_cost:,.0f} is within limit of "
            f"₹{budget_ceiling:,.0f}. Remaining savings buffer: ₹{savings:,.0f}."
        )
    else:
        overspend = total_cost - budget_ceiling
        msg = (
            f"Plan exceeds budget! Total ₹{total_cost:,.0f} exceeds ceiling of "
            f"₹{budget_ceiling:,.0f} by ₹{overspend:,.0f}."
        )

    return ActionResult(
        success=is_within,
        action_name="verify_budget",
        message=msg,
        cost=0.0,
        data={
            "is_within_budget": is_within,
            "total_cost": total_cost,
            "budget_ceiling": budget_ceiling,
            "remaining_savings": savings
        }
    )
