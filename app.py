"""
app.py — AI-Based Smart Home Energy Management: Main Dashboard

A comprehensive smart-home energy planner combining:
1. State-Space Appliance Search (A*, CSP, Greedy)
2. Symbolic Rule-Based Reasoning & Expert System
3. Autonomous & Multi-Agent System (MAS) Coordination
4. Comparative Modern AI Paradigms
5. Explainable Generative Assistant with Telemetry Grounding
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from src.energy_models import (
    Appliance,
    BatteryStorage,
    get_default_appliances,
    get_simulation_profile,
)
from src.appliance_search import (
    run_baseline_asap,
    run_astar_search,
    run_constraint_satisfaction_search,
)
from src.config import (
    llm_available,
    get_llm_provider,
    get_openai_model,
    get_gemini_model,
    get_active_model,
)
from src.ui_theme import (
    inject_custom_css,
    apply_plotly_theme,
    render_hero_banner,
    render_kpi_card,
    render_interactive_energy_topology,
    render_smart_devices_matrix,
    render_sidebar_header,
    render_sidebar_footer,
)

# ── Streamlit Page Configuration ───────────────────────────
st.set_page_config(
    page_title="AI Smart Home Energy Planner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Modern Glassmorphism Styling ────────────────────
inject_custom_css()

# ── Sidebar: Professional Navigation & Global Control ─────────
with st.sidebar:
    render_sidebar_header()

    st.markdown("#### 🧭 Platform Modules")
    st.markdown("""
    <div style="display: flex; flex-direction: column; gap: 4px; margin-bottom: 1.2rem;">
        <a href="/" target="_self" style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; background: rgba(0, 245, 155, 0.12); color: #00f59b; font-weight: 700; text-decoration: none; border: 1px solid rgba(0, 245, 155, 0.3); font-size: 0.86rem;">
            <span>🏠</span> <b>Dashboard Overview</b>
        </a>
        <a href="/Appliance_Search_and_Schedule" target="_self" style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.84rem; font-weight: 600;">
            <span>🔍</span> Appliance Search
        </a>
        <a href="/Rule_Based_Energy_Reasoning" target="_self" style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.84rem; font-weight: 600;">
            <span>📋</span> Rule Reasoning
        </a>
        <a href="/Autonomous_and_Multi_Agent_Control" target="_self" style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.84rem; font-weight: 600;">
            <span>🤖</span> Multi-Agent Control
        </a>
        <a href="/AI_Paradigms_Comparison" target="_self" style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.84rem; font-weight: 600;">
            <span>📊</span> AI Paradigms
        </a>
        <a href="/Explainable_Energy_Assistant" target="_self" style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.84rem; font-weight: 600;">
            <span>💬</span> Explainable Assistant
        </a>
        <a href="/Simulation_and_Evaluation" target="_self" style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.84rem; font-weight: 600;">
            <span>⚙️</span> Simulation & Eval
        </a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🌤️ Simulation Environment")
    scenario_choice = st.selectbox(
        "Active 24h Weather Scenario",
        options=["summer_peak", "winter_heating", "critical_event"],
        format_func=lambda x: {
            "summer_peak": "☀️ Summer Peak Day (High Solar + AC)",
            "winter_heating": "❄️ Winter Heating Day (Heat Pump Peak)",
            "critical_event": "🚨 Critical Demand-Response Emergency",
        }[x],
        index=0,
    )

    max_grid_breaker = st.slider("Main Breaker Capacity (kW)", min_value=6.0, max_value=16.0, value=10.0, step=0.5)
    battery_kwh = st.slider("Battery Storage Capacity (kWh)", min_value=5.0, max_value=25.0, value=10.0, step=2.5)

    st.markdown("---")
    st.markdown("#### 🤖 Intelligence Status")

    provider = get_llm_provider()
    if llm_available() and provider == "gemini":
        st.markdown(f"""
        <div style="background: rgba(0, 245, 155, 0.12); border: 1px solid rgba(0, 245, 155, 0.35); border-radius: 10px; padding: 8px 12px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; color: #00f59b; font-size: 0.84rem;">
                <span class="status-pulse pulse-green"></span> Gemini AI Active
            </div>
            <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 2px;">Model: <code>{get_gemini_model()}</code></div>
        </div>
        """, unsafe_allow_html=True)
    elif llm_available() and provider == "openai":
        st.markdown(f"""
        <div style="background: rgba(0, 229, 255, 0.12); border: 1px solid rgba(0, 229, 255, 0.35); border-radius: 10px; padding: 8px 12px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; color: #00e5ff; font-size: 0.84rem;">
                <span class="status-pulse pulse-cyan"></span> OpenAI Active
            </div>
            <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 2px;">Model: <code>{get_openai_model()}</code></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 10px; padding: 8px 12px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; color: #fbbf24; font-size: 0.84rem;">
                <span class="status-pulse pulse-amber"></span> Deterministic Fallback
            </div>
            <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 2px;">Offline Grounded (Zero API Cost)</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption("A* Search • Forward-Chaining Rules • Multi-Agent Control")

    render_sidebar_footer()

# ── Load Simulation Data & Scrubber ────────────────────────
telemetry = get_simulation_profile(scenario_choice)
appliances = get_default_appliances()

# Execute baseline vs A* search in memory for instantaneous dashboard stats
baseline_res = run_baseline_asap(appliances, telemetry)
astar_res = run_astar_search(appliances, telemetry, max_grid_kw=max_grid_breaker)

# Default to 14:00 (peak solar generation hour) for initial scrubber
if "dash_sim_hour" not in st.session_state:
    st.session_state.dash_sim_hour = 14

savings_dollar = max(0.0, baseline_res.total_cost - astar_res.total_cost)
savings_pct = (savings_dollar / max(baseline_res.total_cost, 0.01)) * 100.0
peak_shaved_kw = max(0.0, baseline_res.peak_demand_kw - astar_res.peak_demand_kw)
carbon_saved_kg = max(0.0, baseline_res.carbon_emissions_kg - astar_res.carbon_emissions_kg)

total_consumption_kwh = sum(astar_res.hourly_appliance_load) + sum(t.baseload_demand_kw for t in telemetry)
total_solar_kwh = sum(t.solar_generation_kw for t in telemetry)

# ── Hero Banner ───────────────────────────────────────────
render_hero_banner(
    title="⚡ AI-Based Smart Home Energy Management",
    subtitle="Autonomous appliance state-space search, symbolic forward-chaining reasoning, 5-agent distributed coordination, and an explainable generative assistant grounded in physical telemetry.",
    badges=[
        ("☀️ Solar PV Optimization", "solar"),
        ("🔋 10 kWh BESS Arbitrage", "battery"),
        ("📈 Dynamic TOU Peak Shifting", "peak"),
        ("🤖 5-Agent Collaborative MAS", "agent"),
        ("🧠 Explainable GenAI Grounding", "ai"),
    ],
)

# ── Interactive Microgrid Power Flow Scrubber Controls ─────
col_top_hdr, col_scrubber = st.columns([1.6, 2.4])
with col_top_hdr:
    st.markdown("### 🎛️ Real-Time Microgrid Power Flow")
    st.caption("Drag the slider to inspect physical power transfers, battery dispatch, and active load for any hour.")
with col_scrubber:
    sim_hour = st.slider("⏱️ Timeline Scrubber (Hour of Day)", 0, 23, st.session_state.dash_sim_hour, format="%02d:00", key="dash_sim_hour")

# Compute instantaneous values for selected hour
tel_h = telemetry[sim_hour]
solar_now = tel_h.solar_generation_kw
baseload_now = tel_h.baseload_demand_kw
sched_now = astar_res.hourly_appliance_load[sim_hour]
current_power_kw = baseload_now + sched_now

# Estimate BESS discharge/charge for current hour
# Under A* / Peak hours, battery discharges to support load; under cheap hours it charges
is_peak_now = tel_h.is_peak
if is_peak_now and (current_power_kw > solar_now):
    bess_flow = min(3.0, current_power_kw - solar_now)
    sim_soc = max(20.0, 75.0 - (sim_hour - 16) * 12.0)
elif solar_now > current_power_kw:
    bess_flow = -min(2.5, solar_now - current_power_kw)
    sim_soc = min(95.0, 30.0 + (sim_hour - 8) * 8.0)
else:
    bess_flow = 0.0
    sim_soc = 50.0

grid_net_now = current_power_kw - solar_now - bess_flow

# ── Key Performance Indicators (6 Client Core Metrics) ─────
st.markdown("#### 📈 Energy Performance & Telemetry Overview")
k1, k2, k3 = st.columns(3)
with k1:
    render_kpi_card(
        label="Total Energy Consumption",
        value=f"{total_consumption_kwh:.1f} kWh",
        subtext=f"24h Managed Load Profile (Base + Smart)",
        delta_type="neutral",
        icon="⚡",
    )
with k2:
    render_kpi_card(
        label="Current Power Usage",
        value=f"{current_power_kw:.2f} kW",
        subtext=f"Active Load at {sim_hour:02d}:00 (Base {baseload_now:.1f} + Sched {sched_now:.1f} kW)",
        delta_type="positive" if current_power_kw < max_grid_breaker else "negative",
        icon="🔌",
    )
with k3:
    render_kpi_card(
        label="Solar Energy Generation",
        value=f"{total_solar_kwh:.1f} kWh",
        subtext=f"Current: {solar_now:.2f} kW PV Generation",
        delta_type="positive" if solar_now > 0 else "neutral",
        icon="☀️",
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

k4, k5, k6 = st.columns(3)
with k4:
    render_kpi_card(
        label="Energy Cost Savings",
        value=f"${savings_dollar:.2f}",
        subtext=f"▼ {savings_pct:.1f}% vs. Unmanaged (${baseline_res.total_cost:.2f})",
        delta_type="positive",
        icon="💰",
    )
with k5:
    render_kpi_card(
        label="Carbon Footprint Reduction",
        value=f"{carbon_saved_kg:.2f} kg",
        subtext=f"Avoided CO₂ emissions (Clean Solar Hours)",
        delta_type="positive",
        icon="🌱",
    )
with k6:
    render_kpi_card(
        label="Connected Smart Devices",
        value="6 Online",
        subtext=f"Breaker Margin: {max_grid_breaker - astar_res.peak_demand_kw:.1f} kW Safe",
        delta_type="positive",
        icon="🛡️",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Interactive Real-Time Physical Microgrid Topology ─────
render_interactive_energy_topology(
    solar_kw=solar_now,
    baseload_kw=baseload_now,
    scheduled_kw=sched_now,
    battery_soc_pct=sim_soc,
    battery_power_kw=bess_flow,
    grid_kw=grid_net_now,
    tariff_price=tel_h.tou_tariff,
    is_peak=is_peak_now,
)

# ── Interactive 24-Hour Energy Dispatch Chart ──────────────
st.markdown("### 📊 24-Hour Smart Home Power Dispatch Flow")
st.caption("Visualizing live interaction between solar generation, baseload consumption, smart scheduled appliances, and TOU tariff pricing.")

hours = [f"{h:02d}:00" for h in range(24)]
tariffs = [t.tou_tariff for t in telemetry]
solar_curve = [t.solar_generation_kw for t in telemetry]
baseload_curve = [t.baseload_demand_kw for t in telemetry]
scheduled_load = astar_res.hourly_appliance_load
total_load = [b + s for b, s in zip(baseload_curve, scheduled_load)]

fig = go.Figure()

# Solar Area
fig.add_trace(go.Scatter(
    x=hours,
    y=solar_curve,
    mode='lines',
    name='☀️ Solar PV Generation (kW)',
    fill='tozeroy',
    fillcolor='rgba(245, 158, 11, 0.20)',
    line=dict(color='#f59e0b', width=2.5),
))

# Unmanaged vs A* Scheduled Load
fig.add_trace(go.Scatter(
    x=hours,
    y=[b + s for b, s in zip(baseload_curve, baseline_res.hourly_appliance_load)],
    mode='lines',
    name='🔴 Unmanaged Baseline Load (kW)',
    line=dict(color='#ef4444', width=2, dash='dot'),
))

fig.add_trace(go.Scatter(
    x=hours,
    y=total_load,
    mode='lines+markers',
    name='🟢 A* Optimized Smart Load (kW)',
    line=dict(color='#10b981', width=3),
    marker=dict(size=5),
))

# Breaker Limit Line
fig.add_trace(go.Scatter(
    x=hours,
    y=[max_grid_breaker] * 24,
    mode='lines',
    name=f'⚠️ Breaker Cap ({max_grid_breaker} kW)',
    line=dict(color='#f87171', width=2, dash='dash'),
))

# Secondary axis for TOU tariff
fig.add_trace(go.Scatter(
    x=hours,
    y=tariffs,
    mode='lines',
    name='💲 TOU Electricity Tariff ($/kWh)',
    yaxis='y2',
    line=dict(color='#a855f7', width=2),
))

# Add interactive vertical cursor at selected hour
fig.add_vline(
    x=f"{sim_hour:02d}:00",
    line_width=2,
    line_dash="dash",
    line_color="#38bdf8",
)

apply_plotly_theme(fig, height=440, title="24-Hour Energy Dispatch Flow & TOU Tariff Dynamics")
fig.update_layout(
    yaxis=dict(title="Electrical Power (kW)", side="left"),
    yaxis2=dict(
        title="Tariff ($/kWh)",
        side="right",
        overlaying="y",
        showgrid=False,
        range=[0.0, 1.4],
        tickfont=dict(color="#a855f7"),
    ),
)

st.plotly_chart(fig, use_container_width=True)

# ── Connected Smart Energy Devices Matrix ──────────────────
st.markdown("---")
render_smart_devices_matrix(appliances, astar_res.schedule)

# ── Module Navigation Grid ─────────────────────────────────
st.markdown("---")
st.markdown("### 🎛️ AI Smart Home Architecture & Functional Modules")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="feature-card">
        <div>
            <h4><span style="font-size:1.3rem;">🔍</span> Appliance State Search</h4>
            <p>
                State-space graph search over 24-hour horizon. Compare <b>ASAP Baseline</b>, <b>Greedy Best-First</b>,
                <b>A* Search</b> (with admissible heuristic bounds), and <b>CSP</b> peak-shaving.
            </p>
        </div>
        <a class="feature-action" href="/Appliance_Search_and_Schedule" target="_self">Explore Appliance Planner &rarr;</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <div>
            <h4><span style="font-size:1.3rem;">🤖</span> Autonomous Multi-Agent System</h4>
            <p>
                Five collaborative physical sub-agents (Grid, Solar/Storage, HVAC Climate, Flexible Loads, and Coordinator)
                negotiating and arbitrating power allocations under breaker limits.
            </p>
        </div>
        <a class="feature-action" href="/Autonomous_and_Multi_Agent_Control" target="_self">Inspect Multi-Agent Control &rarr;</a>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="feature-card">
        <div>
            <h4><span style="font-size:1.3rem;">📋</span> Symbolic Rule Reasoning</h4>
            <p>
                Forward-chaining expert system evaluating peak price curtailment, solar self-consumption,
                battery emergency reserves, and thermodynamic safety overrides.
            </p>
        </div>
        <a class="feature-action" href="/Rule_Based_Energy_Reasoning" target="_self">Launch Rule Inference Tracer &rarr;</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <div>
            <h4><span style="font-size:1.3rem;">💬</span> Explainable Generative Assistant</h4>
            <p>
                Conversational assistant explaining automated energy decisions citing telemetry and active rules.
                Powered by Gemini / OpenAI with verified deterministic fallback.
            </p>
        </div>
        <a class="feature-action" href="/Explainable_Energy_Assistant" target="_self">Open Energy Assistant Chat &rarr;</a>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="feature-card">
        <div>
            <h4><span style="font-size:1.3rem;">📊</span> AI Paradigms Comparison</h4>
            <p>
                Trade-off matrix comparing Classical Search, Symbolic Systems, Supervised ML, RL, MAS,
                and Generative AI across 6 dimensions with an interactive task recommender.
            </p>
        </div>
        <a class="feature-action" href="/AI_Paradigms_Comparison" target="_self">View Paradigms Matrix &rarr;</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <div>
            <h4><span style="font-size:1.3rem;">⚙️</span> Simulation & Evaluation Suite</h4>
            <p>
                Execute automated 24h benchmark evaluations across seasonal weather profiles, inspect
                quantitative metrics (PAR, cost, carbon), and run the verified live test suite.
            </p>
        </div>
        <a class="feature-action" href="/Simulation_and_Evaluation" target="_self">Launch Benchmark & Test Suite &rarr;</a>
    </div>
    """, unsafe_allow_html=True)
