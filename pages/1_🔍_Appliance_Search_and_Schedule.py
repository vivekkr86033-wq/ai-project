"""
1_🔍_Appliance_Search_and_Schedule.py — State-Space Search & Scheduling Algorithms.

Compares Baseline (ASAP), Greedy Best-First, A* Search, and CSP Peak-Shaving
for optimal shiftable appliance start-times.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.energy_models import get_default_appliances, get_simulation_profile
from src.appliance_search import compare_search_algorithms, run_astar_search, build_gantt_dataframe
from src.ui_theme import (
    inject_custom_css,
    apply_plotly_theme,
    render_hero_banner,
    render_kpi_card,
    render_sidebar_header,
    render_sidebar_footer,
)


def render():
    inject_custom_css()

    with st.sidebar:
        render_sidebar_header()
        st.markdown("#### 🔍 Module Navigation")
        st.caption("Active Module: **Appliance Search & Schedule**")
        st.markdown("---")
        render_sidebar_footer()

    render_hero_banner(
        title="🔍 State-Space Search & Appliance Scheduling",
        subtitle="Formulates smart appliance scheduling as a formal state-space graph search problem. Minimizes peak TOU energy costs while guaranteeing zero breaker trip violations and meeting all user completion deadlines.",
        badges=[
            ("🎯 A* Heuristic Search", "ai"),
            ("⚙️ Admissible Lower Bounds", "battery"),
            ("📉 Peak Load Curtailment", "peak"),
            ("🚗 EV & BESS Coordination", "solar"),
        ],
    )

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        scenario = st.selectbox(
            "Evaluation Weather & Tariff Scenario",
            ["summer_peak", "winter_heating", "critical_event"],
            format_func=lambda x: {
                "summer_peak": "☀️ Summer Peak Day ($0.45/kWh peak, 6.2 kW solar)",
                "winter_heating": "❄️ Winter Heating Day (Low solar, heat pump peak)",
                "critical_event": "🚨 Critical Demand Response Emergency ($1.25/kWh peak)",
            }[x],
        )
    with col_ctrl2:
        breaker_limit = st.slider("Main Breaker Capacity (kW)", 6.0, 14.0, 10.0, 0.5)

    telemetry = get_simulation_profile(scenario)
    appliances = get_default_appliances()

    # Run side-by-side search algorithm comparison
    with st.spinner("Running State-Space Search Planners…"):
        results = compare_search_algorithms(appliances, telemetry)

    baseline_res = results[0]
    astar_res = next(r for r in results if "A*" in r.algorithm)
    savings_dollar = max(0.0, baseline_res.total_cost - astar_res.total_cost)
    savings_pct = (savings_dollar / max(baseline_res.total_cost, 0.01)) * 100.0
    peak_diff = max(0.0, baseline_res.peak_demand_kw - astar_res.peak_demand_kw)

    # ── Interactive Client KPI Row ────────────────────────────
    st.markdown("### 📊 Search Planner Optimality Metrics")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("A* Total Cost", f"${astar_res.total_cost:.2f}", f"Baseline: ${baseline_res.total_cost:.2f}", "positive")
    with k2:
        render_kpi_card("Net Cost Savings", f"${savings_dollar:.2f}", f"▼ {savings_pct:.1f}% reduction", "positive")
    with k3:
        render_kpi_card("Peak Demand Shaved", f"{peak_diff:.2f} kW", f"{baseline_res.peak_demand_kw:.1f} → {astar_res.peak_demand_kw:.1f} kW", "positive")
    with k4:
        render_kpi_card("A* Search Latency", f"{astar_res.execution_time_ms:.1f} ms", f"{astar_res.nodes_expanded} nodes expanded", "positive")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Comparison Summary Table ──────────────────────────────
    st.markdown("### 🏆 Comprehensive Algorithm Comparison")

    data = []
    for r in results:
        data.append({
            "Algorithm": r.algorithm,
            "Total Cost ($)": f"${r.total_cost:.2f}",
            "Peak Demand (kW)": f"{r.peak_demand_kw:.2f} kW",
            "Carbon (kg CO2)": f"{r.carbon_emissions_kg:.2f} kg",
            "Discomfort Penalty": f"{r.comfort_penalty:.1f}",
            "Nodes Expanded": r.nodes_expanded,
            "Runtime (ms)": f"{r.execution_time_ms:.2f} ms",
        })

    df_comp = pd.DataFrame(data)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

    # ── Interactive Gantt Schedule Chart ──────────────────────
    st.markdown("### 📅 Optimized Appliance Operating Windows (Gantt Chart)")
    st.caption("Visualizing optimal operational windows computed by A* Heuristic Search across time-of-use tariffs.")

    df_gantt = build_gantt_dataframe(astar_res.schedule, appliances)

    if not df_gantt.empty:
        fig_gantt = px.timeline(
            df_gantt,
            x_start="Start",
            x_end="Finish",
            y="Appliance",
            color="Appliance",
            hover_data=["Power (kW)", "Duration"],
            color_discrete_sequence=["#38bdf8", "#10b981", "#a855f7", "#f59e0b"],
        )
        fig_gantt.update_yaxes(autorange="reversed", tickfont=dict(color="#f8fafc", size=12))
        fig_gantt.update_xaxes(tickformat="%H:%M")
        apply_plotly_theme(fig_gantt, height=360, title="A* Optimal Shiftable Appliance Schedule")
        fig_gantt.update_layout(showlegend=False)
        st.plotly_chart(fig_gantt, use_container_width=True)
    else:
        st.info("No valid appliance schedule windows could be rendered.")

    # ── Load Profiles Overlay ─────────────────────────────────
    st.markdown("### 📈 Load Profiles Overlay: Unmanaged vs. A* Optimal Dispatch")
    hours_labels = [f"{h:02d}:00" for h in range(24)]

    fig_load = go.Figure()

    fig_load.add_trace(go.Scatter(
        x=hours_labels,
        y=baseline_res.hourly_appliance_load,
        name="🔴 Unmanaged Baseline (ASAP)",
        line=dict(color="#ef4444", width=2.5, dash="dot"),
    ))

    fig_load.add_trace(go.Scatter(
        x=hours_labels,
        y=astar_res.hourly_appliance_load,
        name="🟢 A* Search Optimized Schedule",
        line=dict(color="#10b981", width=3),
        fill="tozeroy",
        fillcolor="rgba(16, 185, 129, 0.15)",
    ))

    # Breaker line
    fig_load.add_trace(go.Scatter(
        x=hours_labels,
        y=[breaker_limit] * 24,
        name=f"⚠️ Breaker Limit ({breaker_limit} kW)",
        line=dict(color="#f87171", width=1.8, dash="dash"),
    ))

    apply_plotly_theme(fig_load, height=360, title="Hourly Appliance Demand Comparison (kW)")
    fig_load.update_layout(xaxis_title="Time of Day", yaxis_title="Appliance Load (kW)")
    st.plotly_chart(fig_load, use_container_width=True)

    # ── Interactive Appliance Specification Drawer ─────────────
    with st.expander("🔌 Inspect Appliance Power Ratings & Scheduling Deadlines", expanded=False):
        app_rows = []
        for a in appliances:
            app_rows.append({
                "Appliance": a.name,
                "Power Rating": f"{a.power_kw:.1f} kW",
                "Duration": f"{a.duration_hours}h",
                "Earliest Start": f"{a.earliest_start:02d}:00",
                "Deadline": f"{a.deadline:02d}:00",
                "Shiftable": "Yes" if a.category == "shiftable" else "No",
                "Priority Level": f"P{a.priority}",
            })
        st.dataframe(pd.DataFrame(app_rows), use_container_width=True, hide_index=True)

    # ── Theoretical Search Formulation Explanation ────────────
    with st.expander("🔬 Mathematical Specification & Admissibility Proof", expanded=False):
        st.markdown(r"""
        #### 1. State Representation
        Each search state $s$ represents an assignment of start-times for the first $k$ appliances:
        $$s = \{(a_1, t_1), (a_2, t_2), \dots, (a_k, t_k)\} \quad \text{where } t_i \in [\text{earliest}_i, \text{deadline}_i - d_i]$$

        #### 2. Evaluation Function
        $$f(s) = g(s) + h(s)$$
        - **$g(s)$ (Exact Cost Incurred So Far):**
          Sum of energy purchase costs and comfort penalties incurred by assigned appliances:
          $$g(s) = \sum_{t=0}^{23} \max\left(0, P_{\text{scheduled}}(t) + P_{\text{baseload}}(t) - P_{\text{solar}}(t)\right) \cdot \text{Tariff}(t) + \sum_{i=1}^k \text{Penalty}(a_i, t_i)$$

        - **$h(s)$ (Admissible Heuristic Lower Bound):**
          The remaining unscheduled appliances $a_{k+1}, \dots, a_N$ cannot possibly run at a price lower than the daily minimum tariff $T_{\min} = \min_{t} \text{Tariff}(t)$:
          $$h(s) = \sum_{j=k+1}^N \left( \text{Power}_j \times \text{Duration}_j \right) \cdot T_{\min}$$
          Since $h(s) \le h^*(s)$ everywhere, $h(s)$ is strictly **admissible and consistent**, guaranteeing that A* finds the globally optimal appliance schedule without overestimation.
        """)


render()
