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


def render():
    st.markdown("## 🤖 Autonomous & Multi-Agent System (MAS) Control")
    st.markdown(
        "Model residential energy management as a **decentralized Multi-Agent System**. "
        "Independent sub-agents represent specialized physical subsystems, communicating via "
        "standardized communicative performatives (`INFORM`, `REQUEST`, `PROPOSE`, `ACCEPT`, `REJECT`, `CONFIRM`) "
        "and negotiating power shares to prevent tripping the service breaker."
    )

    # ── Agent Architecture Diagram Cards ──────────────────────
    st.markdown("### 🏛️ Multi-Agent Architecture")
    a1, a2, a3, a4, a5 = st.columns(5)

    with a1:
        st.markdown("""
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:0.8rem; text-align:center;">
            <div style="font-size:1.5rem;">🌐</div>
            <div style="font-weight:700; font-size:0.85rem;">Grid Agent</div>
            <div style="font-size:0.75rem; color:#64748b;">Monitors TOU tariffs, carbon intensity, and emergency DR alerts.</div>
        </div>
        """, unsafe_allow_html=True)

    with a2:
        st.markdown("""
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:0.8rem; text-align:center;">
            <div style="font-size:1.5rem;">☀️🔋</div>
            <div style="font-weight:700; font-size:0.85rem;">Solar & Storage</div>
            <div style="font-size:0.75rem; color:#64748b;">Directs PV generation, battery arbitrage, and reserve buffer.</div>
        </div>
        """, unsafe_allow_html=True)

    with a3:
        st.markdown("""
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:0.8rem; text-align:center;">
            <div style="font-size:1.5rem;">❄️🔥</div>
            <div style="font-weight:700; font-size:0.85rem;">Climate HVAC</div>
            <div style="font-size:0.75rem; color:#64748b;">Maintains thermal comfort band via thermodynamic 1R-1C model.</div>
        </div>
        """, unsafe_allow_html=True)

    with a4:
        st.markdown("""
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:10px; padding:0.8rem; text-align:center;">
            <div style="font-size:1.5rem;">🚗🧺</div>
            <div style="font-weight:700; font-size:0.85rem;">Flexible Loads</div>
            <div style="font-size:0.75rem; color:#64748b;">Bids for EV, laundry, and dishwasher runtime before deadlines.</div>
        </div>
        """, unsafe_allow_html=True)

    with a5:
        st.markdown("""
        <div style="background:#eff6ff; border:1px solid #93c5fd; border-radius:10px; padding:0.8rem; text-align:center;">
            <div style="font-size:1.5rem;">⚖️</div>
            <div style="font-weight:700; font-size:0.85rem; color:#1e40af;">Coordinator</div>
            <div style="font-size:0.75rem; color:#3b82f6;">Arbitrates power requests and enforces main breaker capacity.</div>
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
                "summer_peak": "☀️ Summer Peak Day",
                "winter_heating": "❄️ Winter Heating Day",
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
    st.markdown("### 📊 24-Hour Coordinated Multi-Agent Power Flow")

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
        marker_color="#3b82f6",
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
        name="Battery Power (kW) [>0 Charge, <0 Discharge]",
        line=dict(color="#10b981", width=2),
    ))

    fig_mas.add_trace(go.Scatter(
        x=hours_x,
        y=[max_breaker_kw] * 24,
        mode="lines",
        name=f"Breaker Limit ({max_breaker_kw} kW)",
        line=dict(color="#ef4444", dash="dash", width=2),
    ))

    # Secondary axis for Battery SOC %
    fig_mas.add_trace(go.Scatter(
        x=hours_x,
        y=soc_pcts,
        mode="lines",
        name="Battery SOC (%)",
        yaxis="y2",
        line=dict(color="#8b5cf6", width=2, dash="dot"),
    ))

    fig_mas.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=30, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode="relative",
        xaxis_title="Hour of Day",
        yaxis_title="Power (kW)",
        yaxis2=dict(
            title="Battery SOC (%)",
            side="right",
            overlaying="y",
            showgrid=False,
            range=[0, 105],
        ),
        template="plotly_white",
        hovermode="x unified",
    )

    st.plotly_chart(fig_mas, use_container_width=True)

    # ── Inter-Agent Message Inspector ─────────────────────────
    st.markdown("### 💬 Inter-Agent Message Passing Protocol Log")
    st.caption("Inspect communicative performatives transmitted between autonomous agents according to FIPA agent interaction standards.")

    sel_step_hour = st.slider("Select Hour to Inspect Agent Dialogue", 0, 23, 18, format="%02d:00")
    active_step = simulation_steps[sel_step_hour]

    col_msg, col_dec = st.columns([3, 2])

    with col_msg:
        st.markdown(f"#### 📨 Messages Exchanged at Hour {sel_step_hour:02d}:00 ({len(active_step.messages)} messages)")
        if active_step.messages:
            for m in active_step.messages:
                perf_colors = {
                    "INFORM": "#3b82f6",
                    "REQUEST": "#eab308",
                    "PROPOSE": "#10b981",
                    "ACCEPT": "#059669",
                    "REJECT": "#ef4444",
                    "CONFIRM": "#8b5cf6",
                }
                badge_c = perf_colors.get(m.performative, "#6b7280")

                st.markdown(f"""
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:0.7rem 1rem; margin-bottom:0.5rem; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:600; font-size:0.85rem; color:#1e293b;">{m.sender} ➔ {m.receiver}</span>
                        <span style="background:{badge_c}; color:#ffffff; font-size:0.7rem; font-weight:700; padding:2px 8px; border-radius:4px;">{m.performative}</span>
                    </div>
                    <div style="font-size:0.85rem; font-weight:500; color:#334155; margin-top:4px;"><b>Topic:</b> {m.topic}</div>
                    <div style="font-size:0.83rem; color:#64748b; margin-top:2px;">{m.content}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No inter-agent messages transmitted in this hour (idle period).")

    with col_dec:
        st.markdown(f"#### ⚖️ Coordinator Arbitration Decisions")
        for dec in active_step.agent_decisions:
            status_badge = "🟢 APPROVED" if dec.status == "APPROVED" else "🔴 CURTAILED"
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:0.6rem 0.9rem; margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:700; font-size:0.85rem;">{dec.agent_name}</span>
                    <span style="font-size:0.75rem; font-weight:700;">{status_badge}</span>
                </div>
                <div style="font-size:0.85rem; color:#0369a1; font-weight:600;">Target Power: {dec.target_power_kw:.2f} kW ({dec.action_type})</div>
                <div style="font-size:0.8rem; color:#64748b; margin-top:2px;">{dec.reasoning}</div>
            </div>
            """, unsafe_allow_html=True)


render()
