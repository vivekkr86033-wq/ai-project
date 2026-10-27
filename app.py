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
from src.config import llm_available, get_llm_provider, get_openai_model

# ── Streamlit Page Configuration ───────────────────────────
st.set_page_config(
    page_title="AI Smart Home Energy Planner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Rich Glassmorphism Aesthetics ───────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1300px;
    }

    .hero-container {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(59, 130, 246, 0.12) 50%, rgba(139, 92, 246, 0.12) 100%);
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
    }

    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #059669 0%, #2563eb 50%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }

    .hero-subtitle {
        font-size: 1.15rem;
        color: #4b5563;
        font-weight: 400;
        margin-bottom: 1rem;
    }

    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.12);
        border-color: rgba(37, 99, 235, 0.3);
    }

    .kpi-val {
        font-family: 'Outfit', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0.2rem 0;
    }

    .kpi-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .kpi-sub {
        font-size: 0.8rem;
        color: #10b981;
        font-weight: 500;
    }

    .feature-card {
        background: #ffffff;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }

    .feature-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 10px 25px rgba(59, 130, 246, 0.1);
        transform: translateY(-2px);
    }

    .badge-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }

    .badge-solar { background: #fef3c7; color: #b45309; }
    .badge-battery { background: #dcfce7; color: #15803d; }
    .badge-peak { background: #fee2e2; color: #b91c1c; }
    .badge-agent { background: #ede9fe; color: #6d28d9; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar: Simulation Scenario & Global Config ───────────
with st.sidebar:
    st.markdown("## ⚡ AI Smart Home")
    st.markdown("---")
    st.markdown("**Autonomous Energy Planner & Multi-Agent Coordinator**")

    st.markdown("### 🌤️ Simulation Environment")
    scenario_choice = st.selectbox(
        "Active 24h Weather Scenario",
        options=["summer_peak", "winter_heating", "critical_event"],
        format_func=lambda x: {
            "summer_peak": "☀️ Sunny Summer Day (High Solar + AC)",
            "winter_heating": "❄️ Cloudy Winter Day (Heat Pump Peak)",
            "critical_event": "🚨 Critical Demand-Response Emergency",
        }[x],
        index=0,
    )

    max_grid_breaker = st.slider("Main Breaker Capacity (kW)", min_value=6.0, max_value=16.0, value=10.0, step=0.5)
    battery_kwh = st.slider("Battery Storage Capacity (kWh)", min_value=5.0, max_value=25.0, value=10.0, step=2.5)

    st.markdown("---")
    st.markdown("### 🤖 Intelligence System Status")

    if llm_available():
        st.success(f"🧠 Generative Assistant: **{get_llm_provider().upper()}** ({get_openai_model()})")
    else:
        st.info("⚡ Explainability: **Deterministic Grounded Fallback** (Zero API Cost)")

    st.caption("A* Search • Forward-Chaining Rules • Multi-Agent Control")

# ── Load Simulation Data ───────────────────────────────────
telemetry = get_simulation_profile(scenario_choice)
appliances = get_default_appliances()

# Execute baseline vs A* search in memory for instantaneous dashboard stats
baseline_res = run_baseline_asap(appliances, telemetry)
astar_res = run_astar_search(appliances, telemetry, max_grid_kw=max_grid_breaker)

savings_dollar = max(0.0, baseline_res.total_cost - astar_res.total_cost)
savings_pct = (savings_dollar / max(baseline_res.total_cost, 0.01)) * 100.0
peak_shaved_kw = max(0.0, baseline_res.peak_demand_kw - astar_res.peak_demand_kw)
carbon_saved_kg = max(0.0, baseline_res.carbon_emissions_kg - astar_res.carbon_emissions_kg)

# ── Hero Banner ───────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">⚡ AI-Based Smart Home Energy Management</div>
    <div class="hero-subtitle">
        Autonomous appliance scheduling, symbolic energy reasoning, multi-agent coordination, and explainable AI.
    </div>
    <div>
        <span class="badge-pill badge-solar">☀️ Solar PV Optimization</span>
        <span class="badge-pill badge-battery">🔋 10 kWh BESS Arbitrage</span>
        <span class="badge-pill badge-peak">📈 Dynamic TOU Peak Shifting</span>
        <span class="badge-pill badge-agent">🤖 5-Agent Collaborative MAS</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Key Performance Indicators (KPIs) ─────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💰 Daily Cost Savings</div>
        <div class="kpi-val">${savings_dollar:.2f}</div>
        <div class="kpi-sub">▼ {savings_pct:.1f}% vs. Unmanaged</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">⚡ Peak Demand Shaved</div>
        <div class="kpi-val">{peak_shaved_kw:.2f} kW</div>
        <div class="kpi-sub">Peak reduced from {baseline_res.peak_demand_kw:.1f} to {astar_res.peak_demand_kw:.1f} kW</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🌱 Carbon Avoided</div>
        <div class="kpi-val">{carbon_saved_kg:.2f} kg</div>
        <div class="kpi-sub">Optimized for clean solar hours</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🛡️ Breaker Safety Margin</div>
        <div class="kpi-val">{max_grid_breaker - astar_res.peak_demand_kw:.1f} kW</div>
        <div class="kpi-sub">100% Breaker Trip Protection</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

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
    fillcolor='rgba(245, 158, 11, 0.25)',
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
    line=dict(color='#dc2626', width=2, dash='dash'),
))

# Secondary axis for TOU tariff
fig.add_trace(go.Scatter(
    x=hours,
    y=tariffs,
    mode='lines',
    name='💲 TOU Electricity Tariff ($/kWh)',
    yaxis='y2',
    line=dict(color='#8b5cf6', width=2),
))

fig.update_layout(
    height=440,
    margin=dict(l=40, r=40, t=30, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    xaxis=dict(title="Time of Day (Hours)"),
    yaxis=dict(title="Electrical Power (kW)", side="left"),
    yaxis2=dict(
        title="Tariff ($/kWh)",
        side="right",
        overlaying="y",
        showgrid=False,
        range=[0.0, 1.4],
    ),
    template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)

# ── Module Navigation Grid ─────────────────────────────────
st.markdown("---")
st.markdown("### 🎛️ AI Smart Home Architecture & Functional Modules")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="feature-card">
        <h4>🔍 Appliance State Search</h4>
        <p style="color:#64748b; font-size:0.9rem;">
            State-space graph search over 24-hour horizon. Compare <b>ASAP Baseline</b>, <b>Greedy Best-First</b>,
            <b>A* Search</b> (with admissible heuristic bounds), and <b>CSP</b> peak-shaving.
        </p>
        <a href="/Appliance_Search_and_Schedule" target="_self" style="color:#2563eb; font-weight:600; text-decoration:none;">Open Appliance Search →</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h4>🤖 Autonomous Multi-Agent System</h4>
        <p style="color:#64748b; font-size:0.9rem;">
            Five specialized agents (Grid, Solar/Storage, HVAC Climate, Flexible Loads, and Central Coordinator)
            collaborating and negotiating power allocations under breaker limits.
        </p>
        <a href="/Autonomous_and_Multi_Agent_Control" target="_self" style="color:#2563eb; font-weight:600; text-decoration:none;">Open Multi-Agent Control →</a>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="feature-card">
        <h4>📋 Symbolic Rule Reasoning</h4>
        <p style="color:#64748b; font-size:0.9rem;">
            Forward-chaining expert system evaluating peak price curtailment, solar self-consumption,
            battery emergency reserves, and thermal safety overrides.
        </p>
        <a href="/Rule_Based_Energy_Reasoning" target="_self" style="color:#2563eb; font-weight:600; text-decoration:none;">Open Energy Rule Engine →</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h4>💬 Explainable Generative Assistant</h4>
        <p style="color:#64748b; font-size:0.9rem;">
            Ask natural language questions about why your EV was delayed, how the battery saved money,
            or what rules fired. Powered by OpenAI or grounded deterministic fallback.
        </p>
        <a href="/Explainable_Energy_Assistant" target="_self" style="color:#2563eb; font-weight:600; text-decoration:none;">Open Energy Assistant →</a>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="feature-card">
        <h4>📊 AI Paradigms Comparison</h4>
        <p style="color:#64748b; font-size:0.9rem;">
            Compare Classical Search, Symbolic Systems, Supervised ML, Reinforcement Learning, MAS,
            and Generative AI across 6 dimensions with an interactive task recommender.
        </p>
        <a href="/AI_Paradigms_Comparison" target="_self" style="color:#2563eb; font-weight:600; text-decoration:none;">Open Paradigms Matrix →</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-card">
        <h4>⚙️ Simulation & Evaluation Suite</h4>
        <p style="color:#64748b; font-size:0.9rem;">
            Execute automated 24h benchmark evaluations across seasonal weather profiles, inspect
            quantitative metrics (PAR, cost, carbon), and manage API secrets.
        </p>
        <a href="/Simulation_and_Evaluation" target="_self" style="color:#2563eb; font-weight:600; text-decoration:none;">Open Simulation & Eval →</a>
    </div>
    """, unsafe_allow_html=True)
