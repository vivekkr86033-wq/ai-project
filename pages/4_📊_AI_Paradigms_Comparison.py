"""
4_📊_AI_Paradigms_Comparison.py — Comparative Analysis of Modern AI Paradigms in Smart Home Energy.

Compares:
1. Classical State-Space Search & Planning
2. Symbolic Rule-Based Expert Systems
3. Supervised Machine Learning (Forecasting)
4. Reinforcement Learning / MDP (Dynamic Arbitrage)
5. Multi-Agent Systems (MAS) & Distributed Coordination
6. Generative AI & Explainable LLM Assistants
"""

import streamlit as st
import pandas as pd
from src.energy_paradigms import (
    ENERGY_AI_PARADIGMS,
    RECOMMENDED_TASKS,
    get_paradigm_by_id,
    get_recommendation_for_task,
)
from src.ui_theme import (
    inject_custom_css,
    render_hero_banner,
    render_sidebar_header,
    render_sidebar_footer,
)


def render():
    inject_custom_css()

    with st.sidebar:
        render_sidebar_header()
        st.markdown("#### 📊 Module Navigation")
        st.caption("Active Module: **AI Paradigms Comparison**")
        st.markdown("---")
        render_sidebar_footer()

    render_hero_banner(
        title="📊 Modern AI Paradigms Comparison & Task Recommender",
        subtitle="No single AI paradigm solves all challenges of Smart Home Energy Management. A robust home energy system integrates Classical Search, Symbolic Systems, Supervised ML, Reinforcement Learning, MAS, and Generative AI in a layered hybrid architecture.",
        badges=[
            ("🧠 6 Core AI Paradigms", "ai"),
            ("🎯 Interactive Task Recommender", "solar"),
            ("⚖️ Trade-Off Engineering Matrix", "agent"),
            ("🏛️ Hybrid Layered Stack", "battery"),
        ],
    )

    tab_matrix, tab_rec, tab_deep = st.tabs([
        "📋 Comparative Matrix",
        "🎯 Task-to-Paradigm Recommender",
        "🔬 Deep Paradigm Analysis",
    ])

    # ── Tab 1: Comparative Matrix ──────────────────────────────
    with tab_matrix:
        st.markdown("### 🏛️ 6 Modern AI Paradigms in Smart Home Energy")
        st.caption("Cross-dimensional trade-offs between optimality, computational latency, interpretability, and safety.")

        matrix_rows = []
        for p in ENERGY_AI_PARADIGMS:
            matrix_rows.append({
                "Paradigm": p.name,
                "Category": p.category,
                "Smart Home Application": p.smart_home_application,
                "Optimality": p.optimality,
                "Latency": p.latency,
                "Interpretability": p.interpretability,
                "Safety Assurance": p.safety_assurance,
                "Sample Efficiency": p.sample_efficiency,
            })

        df_matrix = pd.DataFrame(matrix_rows)
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 🏗️ Layered Smart Home Hybrid Architecture")
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 1.25rem 1.5rem; margin: 1rem 0;">
            <div style="display:flex; flex-direction:column; gap:8px;">
                <div style="background:rgba(59,130,246,0.15); border:1px solid rgba(59,130,246,0.3); border-radius:8px; padding:10px 14px; color:#93c5fd; font-weight:600;">
                    💬 <b>Generative AI Layer:</b> Explainable Resident Assistant & Telemetry Reasoning
                </div>
                <div style="background:rgba(139,92,246,0.15); border:1px solid rgba(139,92,246,0.3); border-radius:8px; padding:10px 14px; color:#c084fc; font-weight:600;">
                    🤖 <b>Multi-Agent Coordination Layer:</b> Distributed 5-Agent Breaker Auctioning (MAS)
                </div>
                <div style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.3); border-radius:8px; padding:10px 14px; color:#34d399; font-weight:600;">
                    🔍 <b>Planning & Search Layer:</b> A* State-Space Graph Search & CSP Heuristic Shifting
                </div>
                <div style="background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.3); border-radius:8px; padding:10px 14px; color:#fbbf24; font-weight:600;">
                    📈 <b>Prediction & Learning Layer:</b> Supervised ML Solar PV & Baseload Load Forecasting
                </div>
                <div style="background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); border-radius:8px; padding:10px 14px; color:#f87171; font-weight:600;">
                    🛡️ <b>Deterministic Safety Shield:</b> Symbolic Forward-Chaining Expert Rules (Zero Breaker Trips)
                </div>
                <div style="background:rgba(100,116,139,0.15); border:1px solid rgba(100,116,139,0.3); border-radius:8px; padding:10px 14px; color:#cbd5e1; font-weight:600;">
                    ⚡ <b>Physical Infrastructure:</b> Inverter, 10 kWh BESS, Service Breaker, HVAC, EV Charger
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Tab 2: Task-to-Paradigm Recommender ─────────────────────
    with tab_rec:
        st.markdown("### 🎯 Interactive Smart Home Task Recommender")
        st.caption("Select a real-world energy management problem to see the recommended AI paradigm and engineering trade-offs.")

        task_options = {t["id"]: f"{t['task_name']}" for t in RECOMMENDED_TASKS}
        selected_tid = st.selectbox(
            "Select Smart Home Energy Task:",
            options=list(task_options.keys()),
            format_func=lambda x: task_options[x],
        )

        task_info = get_recommendation_for_task(selected_tid)

        if task_info:
            prim_p = get_paradigm_by_id(task_info["recommended_paradigm"])
            alt_p = get_paradigm_by_id(task_info["alternative_paradigm"])

            col_t1, col_t2 = st.columns(2)

            with col_t1:
                st.markdown(f"""
                <div class="node-box" style="border-top:3px solid #10b981; text-align:left; align-items:flex-start; padding:1.25rem;">
                    <div style="font-size:0.78rem; font-weight:700; color:#34d399; text-transform:uppercase; letter-spacing:0.5px;">PRIMARY RECOMMENDATION</div>
                    <div style="font-size:1.35rem; font-weight:700; color:#f8fafc; font-family:'Outfit',sans-serif; margin:0.3rem 0;">⭐ {prim_p.name if prim_p else ''}</div>
                    <p style="font-size:0.9rem; color:#cbd5e1; margin-top:0.4rem; line-height:1.5;"><b>Why:</b> {task_info['rationale']}</p>
                    <hr style="margin:0.8rem 0; border-color:rgba(255,255,255,0.08); width:100%;">
                    <div style="font-size:0.83rem; color:#94a3b8; line-height:1.6;">
                        <b>Core Mechanism:</b> {prim_p.core_mechanism if prim_p else ''}<br>
                        <b>Optimality:</b> {prim_p.optimality if prim_p else ''} | <b>Latency:</b> {prim_p.latency if prim_p else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_t2:
                st.markdown(f"""
                <div class="node-box" style="border-top:3px solid #60a5fa; text-align:left; align-items:flex-start; padding:1.25rem;">
                    <div style="font-size:0.78rem; font-weight:700; color:#60a5fa; text-transform:uppercase; letter-spacing:0.5px;">COMPLEMENTARY ALTERNATIVE</div>
                    <div style="font-size:1.35rem; font-weight:700; color:#f8fafc; font-family:'Outfit',sans-serif; margin:0.3rem 0;">🔄 {alt_p.name if alt_p else ''}</div>
                    <p style="font-size:0.9rem; color:#cbd5e1; margin-top:0.4rem; line-height:1.5;">Can be paired with the primary paradigm for secondary multi-objective trade-offs.</p>
                    <hr style="margin:0.8rem 0; border-color:rgba(255,255,255,0.08); width:100%;">
                    <div style="font-size:0.83rem; color:#94a3b8; line-height:1.6;">
                        <b>Core Mechanism:</b> {alt_p.core_mechanism if alt_p else ''}<br>
                        <b>Interpretability:</b> {alt_p.interpretability if alt_p else ''} | <b>Safety:</b> {alt_p.safety_assurance if alt_p else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Tab 3: Deep Paradigm Analysis ──────────────────────────
    with tab_deep:
        st.markdown("### 🔬 Comprehensive Technical Breakdown")

        for p in ENERGY_AI_PARADIGMS:
            with st.expander(f"📌 {p.name} — {p.category}"):
                st.markdown(f"**Smart Home Application:** {p.smart_home_application}")
                st.markdown(f"**Mathematical / Algorithmic Mechanism:** {p.core_mechanism}")

                col_s, col_l = st.columns(2)
                with col_s:
                    st.markdown("##### ✅ Architectural Strengths")
                    for s in p.strengths:
                        st.markdown(f"- {s}")
                with col_l:
                    st.markdown("##### ⚠️ Engineering Limitations")
                    for l in p.limitations:
                        st.markdown(f"- {l}")


render()
