"""
3_🤖_Autonomous_and_Multi_Agent_Control.py — Multi-Agent System (MAS) Coordination.

Simulates 5 autonomous agents collaborating and negotiating under physical grid breaker constraints:
1. GridMonitorAgent
2. SolarStorageAgent
3. ClimateHVACAgent
4. FlexibleLoadAgent
5. CoordinatorAgent
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.energy_models import get_default_appliances, get_simulation_profile
from src.appliance_search import run_astar_search
from src.multi_agent import run_multi_agent_simulation
from src.ui_theme import (
    inject_custom_css,
    apply_plotly_theme,
    render_hero_banner,
    render_sidebar_header,
    render_sidebar_footer,
)


def render():
    inject_custom_css()

    with st.sidebar:
        render_sidebar_header()
        st.markdown("#### 🤖 Module Navigation")
        st.caption("Active Module: **Autonomous & Multi-Agent Control**")
        st.markdown("---")
        render_sidebar_footer()

    render_hero_banner(
        title="🤖 Autonomous & Multi-Agent System (MAS) Control",
        subtitle="Models smart home energy as a decentralized multi-agent system. Independent physical sub-agents communicate via standardized FIPA performatives (INFORM, REQUEST, PROPOSE, ACCEPT, REJECT, CONFIRM) and negotiate power shares under breaker constraints.",
        badges=[
            ("🤝 5-Agent Collaborative MAS", "agent"),
            ("📡 FIPA Performative Messaging", "ai"),
            ("⚖️ Breaker Capacity Auctioning", "peak"),
            ("🔋 Real-Time BESS Arbitrage", "battery"),
        ],
    )

    # ── Agent Architecture Diagram Cards ──────────────────────
    st.markdown("### 🏛️ Distributed Multi-Agent Architecture")
    a1, a2, a3, a4, a5 = st.columns(5)

    agents = [
        (a1, "🌐", "Grid Monitor", "Monitors TOU tariffs, carbon intensity, and emergency DR signals.", "#3b82f6"),
        (a2, "☀️🔋", "Solar & Storage", "Directs PV dispatch, BESS battery arbitrage, and reserve floor.", "#06b6d4"),
        (a3, "❄️🔥", "Climate HVAC", "Guarantees 18–26°C comfort via thermodynamic 1R-1C model.", "#10b981"),
        (a4, "🚗🧺", "Flexible Loads", "Bids for EV, laundry, and dishwasher runtime before deadlines.", "#f59e0b"),
        (a5, "⚖️", "Coordinator", "Executes priority auctions and arbitrates service breaker capacity.", "#8b5cf6"),
    ]

    for col, icon, name, desc, color in agents:
        with col:
            st.markdown(f"""
            <div class="node-box" style="border-top:3px solid {color}; padding:1.1rem 0.8rem; text-align:center;">
                <div style="font-size:1.8rem; margin-bottom:0.25rem;">{icon}</div>
                <div style="font-weight:700; font-size:0.92rem; color:#f8fafc; font-family:'Outfit',sans-serif;">{name}</div>
                <div style="font-size:0.76rem; color:#94a3b8; margin-top:5px; line-height:1.4;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Simulation Controls ───────────────────────────────────
    c_ctrl1, c_ctrl2 = st.columns([2, 1])
    with c_ctrl1:
        sim_scenario = st.selectbox(
            "Simulation Scenario",
            ["summer_peak", "winter_heating", "critical_event"],
            format_func=lambda x: {
                "summer_peak": "☀️ Summer Peak Day (High Solar + AC Cooling)",
                "winter_heating": "❄️ Winter Heating Day (Heat Pump Peak Demand)",
                "critical_event": "🚨 Critical Demand Response Emergency Day",
            }[x],
        )
    with c_ctrl2:
        max_breaker_kw = st.slider("Main Service Breaker Cap (kW)", 7.0, 14.0, 10.0, 0.5)

    telemetry = get_simulation_profile(sim_scenario)
    appliances = get_default_appliances()
    astar_res = run_astar_search(appliances, telemetry, max_grid_kw=max_breaker_kw)

    # Run MAS simulation
    simulation_steps = run_multi_agent_simulation(
        appliances=appliances,
        telemetry_profile=telemetry,
        schedule=astar_res.schedule,
        max_grid_kw=max_breaker_kw,
    )

    # ── 24h Coordinated Power Flow Chart ───────────────────────
    st.markdown("### 📊 24-Hour Coordinated Multi-Agent Power Dispatch")

    hours_x = [f"{s.hour:02d}:00" for s in simulation_steps]
    grid_imports = [s.grid_import_kw for s in simulation_steps]
    solar_gens = [s.telemetry.solar_generation_kw for s in simulation_steps]
    battery_powers = [s.battery_power_kw for s in simulation_steps]
    soc_pcts = [s.battery_soc * 100 for s in simulation_steps]

    fig_mas = go.Figure()

    fig_mas.add_trace(go.Bar(
        x=hours_x,
        y=grid_imports,
        name="Grid Import (kW)",
        marker=dict(color="#3b82f6", opacity=0.8),
    ))

    fig_mas.add_trace(go.Scatter(
        x=hours_x,
        y=solar_gens,
        mode="lines",
        name="Solar PV (kW)",
        line=dict(color="#f59e0b", width=2.5),
    ))

    fig_mas.add_trace(go.Scatter(
        x=hours_x,
        y=battery_powers,
        mode="lines+markers",
        name="Battery Power (kW) [>0 Discharge, <0 Charge]",
        line=dict(color="#10b981", width=2),
    ))

    fig_mas.add_trace(go.Scatter(
        x=hours_x,
        y=[max_breaker_kw] * 24,
        mode="lines",
        name=f"Breaker Limit ({max_breaker_kw} kW)",
        line=dict(color="#f87171", dash="dash", width=2),
    ))

    fig_mas.add_trace(go.Scatter(
        x=hours_x,
        y=soc_pcts,
        mode="lines",
        name="Battery SOC (%)",
        yaxis="y2",
        line=dict(color="#c084fc", width=2, dash="dot"),
    ))

    apply_plotly_theme(fig_mas, height=420, title="Coordinated Multi-Agent 24-Hour Power Allocations")
    fig_mas.update_layout(
        barmode="relative",
        xaxis_title="Hour of Day",
        yaxis_title="Power (kW)",
        yaxis2=dict(
            title="Battery SOC (%)",
            side="right",
            overlaying="y",
            showgrid=False,
            range=[0, 105],
            tickfont=dict(color="#c084fc"),
        ),
    )

    st.plotly_chart(fig_mas, use_container_width=True)

    # ── Inter-Agent Message Inspector ─────────────────────────
    st.markdown("### 💬 Inter-Agent Message Passing Protocol Log")
    st.caption("Inspect communicative performatives transmitted between autonomous agents according to FIPA agent interaction standards.")

    sel_step_hour = st.slider("⏱️ Select Hour to Inspect Agent Dialogue", 0, 23, 18, format="%02d:00")
    active_step = simulation_steps[sel_step_hour]

    col_msg, col_dec = st.columns([3, 2])

    with col_msg:
        st.markdown(f"#### 📨 Messages Exchanged at Hour {sel_step_hour:02d}:00 ({len(active_step.messages)} messages)")
        if active_step.messages:
            perf_colors = {
                "INFORM": ("#3b82f6", "rgba(59, 130, 246, 0.2)"),
                "REQUEST": ("#f59e0b", "rgba(245, 158, 11, 0.2)"),
                "PROPOSE": ("#10b981", "rgba(16, 185, 129, 0.2)"),
                "ACCEPT": ("#34d399", "rgba(52, 211, 153, 0.2)"),
                "REJECT": ("#f87171", "rgba(248, 113, 113, 0.2)"),
                "CONFIRM": ("#c084fc", "rgba(192, 132, 252, 0.2)"),
            }
            for m in active_step.messages:
                txt_c, bg_c = perf_colors.get(m.performative, ("#94a3b8", "rgba(148, 163, 184, 0.2)"))

                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 0.85rem 1.1rem; margin-bottom: 0.6rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; font-size:0.88rem; color:#f8fafc;">{m.sender} &rarr; {m.receiver}</span>
                        <span style="background:{bg_c}; color:{txt_c}; font-size:0.72rem; font-weight:700; padding:2px 9px; border-radius:9999px; border:1px solid {txt_c}40;">{m.performative}</span>
                    </div>
                    <div style="font-size:0.86rem; font-weight:600; color:#38bdf8; margin-top:5px;">Topic: {m.topic}</div>
                    <div style="font-size:0.83rem; color:#94a3b8; margin-top:3px; line-height:1.45;">{m.content}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No inter-agent messages transmitted in this hour (idle period).")

    with col_dec:
        st.markdown(f"#### ⚖️ Coordinator Arbitration Decisions")
        for dec in active_step.agent_decisions:
            is_app = dec.status == "APPROVED"
            stat_color = "#34d399" if is_app else "#f87171"
            stat_bg = "rgba(52, 211, 153, 0.15)" if is_app else "rgba(248, 113, 113, 0.15)"
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 0.85rem 1rem; margin-bottom: 0.6rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; font-size:0.88rem; color:#f8fafc;">{dec.agent_name}</span>
                    <span style="background:{stat_bg}; color:{stat_color}; font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:9999px;">{dec.status}</span>
                </div>
                <div style="font-size:0.85rem; color:#60a5fa; font-weight:600; margin-top:4px;">Power: {dec.target_power_kw:.2f} kW ({dec.action_type})</div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:3px; line-height:1.4;">{dec.reasoning}</div>
            </div>
            """, unsafe_allow_html=True)


render()
