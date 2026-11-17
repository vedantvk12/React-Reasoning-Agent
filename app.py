"""
Streamlit Web Dashboard for the ReAct Travel Planning Agent.
Provides an interactive visualization of the Thought-Action-Observation loop,
dynamic replanning events, and financial audits.
"""

import streamlit as st
import json
from models import TaskStatus
from planner import GoalAnalyzer
from agent import ReActAgent

# Page configuration
st.set_page_config(
    page_title="ReAct Travel Planning Agent | CO-2",
    page_icon="✈️",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .step-card {
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 6px solid #3B82F6;
        background-color: #F8FAFC;
    }
    .step-card-failed {
        border-left-color: #EF4444;
        background-color: #FEF2F2;
    }
    .step-card-replanned {
        border-left-color: #10B981;
        background-color: #ECFDF5;
    }
    .thought-label {
        font-weight: 700;
        color: #6B7280;
        font-size: 0.85rem;
        text-transform: uppercase;
    }
    .action-label {
        font-weight: 700;
        color: #2563EB;
        font-size: 0.85rem;
        text-transform: uppercase;
    }
    .obs-label {
        font-weight: 700;
        color: #059669;
        font-size: 0.85rem;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">✈️ ReAct Intelligent Travel Planning Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Unit 2: Reasoning, Planning and Decision-Making (CO-2) | '
    '<b>Vedant Sattejkumar Kirange</b> (Roll No: 55 | PRN: ADT23SOCB1294)</div>',
    unsafe_allow_html=True
)

# Sidebar
st.sidebar.header("🎯 Travel Goal Configuration")
default_goal = (
    "Plan a 2-day trip to Goa for 2 people within a budget of ₹10,000, "
    "including transportation, accommodation, food, and sightseeing."
)
goal_input = st.sidebar.text_area("Input Travel Objective:", value=default_goal, height=120)

simulate_fail = st.sidebar.checkbox(
    "Simulate Hotel Booking Failure (Trigger Replanning)",
    value=True,
    help="When enabled, the primary hotel will report fully booked, testing autonomous replanning."
)

run_button = st.sidebar.button("🚀 Run ReAct Agent", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Academic Submission Specs")
st.sidebar.info(
    "• **Course:** Reasoning, Planning and Decision Making\n"
    "• **Framework:** ReAct (Reason + Act)\n"
    "• **Replanning:** Dynamic plan queue insertion\n"
    "• **Dependencies:** 100% Offline Python"
)

# Execute agent
goal = GoalAnalyzer.parse_goal(goal_input)

# Top Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Destination", goal.destination)
col2.metric("Duration", f"{goal.duration_days} Days")
col3.metric("Party Size", f"{goal.num_people} Persons")
col4.metric("Budget Ceiling", f"₹{goal.budget_ceiling:,.0f}")

st.markdown("---")

if run_button or "plan" not in st.session_state:
    agent = ReActAgent(goal=goal, simulate_failure=simulate_fail)
    plan = agent.run()
    st.session_state["plan"] = plan
    st.session_state["recorded_costs"] = agent.recorded_costs
else:
    plan = st.session_state["plan"]
    recorded_costs = st.session_state["recorded_costs"]

# Layout: Trace on Left, Summary on Right
col_trace, col_summary = st.columns([1.6, 1.0])

with col_trace:
    st.subheader("🔄 ReAct Reasoning Trace (Thought ➔ Action ➔ Observation)")

    for step in plan.trace_history:
        card_class = "step-card"
        badge = "✅ SUCCESS"
        if step.status == "FAILED":
            card_class = "step-card step-card-failed"
            badge = "❌ FAILED"
        elif "replan" in step.action:
            card_class = "step-card step-card-replanned"
            badge = "🔄 REPLANNED"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                <span style="font-weight:700; font-size:1rem;">Step {step.step_number}</span>
                <span style="font-weight:600; font-size:0.85rem;">{badge}</span>
            </div>
            <div class="thought-label">Thought:</div>
            <div style="margin-bottom:8px; font-style:italic;">"{step.thought}"</div>
            <div class="action-label">Action:</div>
            <div style="margin-bottom:8px; font-family:monospace; background:#e2e8f0; padding:3px 6px; border-radius:4px; display:inline-block;">{step.action}</div>
            <div class="obs-label">Observation:</div>
            <div>{step.observation}</div>
        </div>
        """, unsafe_allow_html=True)

with col_summary:
    st.subheader("📊 Financial Audit & Replanning")

    # Financial status card
    compliance_color = "#10B981" if plan.is_within_budget else "#EF4444"
    status_text = "WITHIN BUDGET" if plan.is_within_budget else "OVER BUDGET"

    st.markdown(f"""
    <div style="padding:15px; border-radius:8px; background:#F1F5F9; border-top:4px solid {compliance_color}; margin-bottom:15px;">
        <h4 style="margin:0 0 10px 0; color:#1E293B;">Budget Status: <span style="color:{compliance_color};">{status_text}</span></h4>
        <p style="margin:4px 0;"><b>Total Trip Cost:</b> ₹{plan.total_cost:,.0f}</p>
        <p style="margin:4px 0;"><b>Budget Ceiling:</b> ₹{goal.budget_ceiling:,.0f}</p>
        <p style="margin:4px 0;"><b>Remaining Savings Buffer:</b> ₹{plan.remaining_savings:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

    # Cost breakdown table
    st.markdown("#### Cost Breakdown by Category")
    cost_data = {
        "Category": ["Transportation", "Accommodation", "Food & Dining", "Sightseeing", "TOTAL"],
        "Amount (₹)": [
            f"₹{agent.recorded_costs.get('transportation', 0):,.0f}",
            f"₹{agent.recorded_costs.get('accommodation', 0):,.0f}",
            f"₹{agent.recorded_costs.get('food', 0):,.0f}",
            f"₹{agent.recorded_costs.get('sightseeing', 0):,.0f}",
            f"₹{plan.total_cost:,.0f}"
        ]
    }
    st.table(cost_data)

    # Replanning spotlight
    if plan.replanning_occurred:
        st.markdown("#### ⚡ Dynamic Replanning Event")
        st.warning(
            f"**What Went Wrong?** Initial hotel '{plan.failed_task.params.get('hotel_name', 'Sunset Beach Resort')}' "
            f"was fully booked.\n\n"
            f"**How Agent Noticed:** Tool returned `success=False` with observation: *'{plan.replanning_reason}'*.\n\n"
            f"**What Changed:** Injected replacement subtask `{plan.replanned_task.action}()` to book "
            f"verified alternative *Palm Breeze Budget Guesthouse* for ₹2,000 (saving ₹1,000)."
        )

    st.markdown("#### 📝 Evaluation: Where ReAct Helped & Struggled")
    st.markdown(
        "1. **Helped:** Decomposed complex travel goal into 6 sequential, verifiable subtasks.\n"
        "2. **Helped:** Detected runtime booking failure and autonomously replanned without crashing.\n"
        "3. **Struggled:** Limited to local simulated catalogs rather than open live external web data."
    )

    # Download Trace Button
    trace_text = "\n\n".join([
        f"THOUGHT:\n{s.thought}\nACTION:\n{s.action}\nOBSERVATION:\n{s.observation}"
        for s in plan.trace_history
    ])
    st.download_button(
        "📥 Download Full Execution Trace (.txt)",
        data=trace_text,
        file_name="execution_trace.txt",
        mime="text/plain",
        use_container_width=True
    )
