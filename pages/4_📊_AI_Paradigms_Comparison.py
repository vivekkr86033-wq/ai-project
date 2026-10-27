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


def render():
    st.markdown("## 📊 Modern AI Paradigms Comparison & Task Recommender")
    st.markdown(
        "No single AI paradigm solves all challenges of Smart Home Energy Management. "
        "A robust home energy management system (HEMS) integrates **Classical Search**, **Symbolic Systems**, "
        "**Machine Learning**, **Reinforcement Learning**, **Multi-Agent Systems**, and **Generative AI** in a layered hybrid architecture."
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
        ```
        ┌────────────────────────────────────────────────────────┐
        │  Generative AI Layer (Explainable Resident Assistant)  │
        ├────────────────────────────────────────────────────────┤
        │  Multi-Agent Coordination Layer (Decentralized MAS)    │
        ├────────────────────────────────────────────────────────┤
        │  Planning Layer (A* State-Space Shift-Scheduling & CSP)│
        ├────────────────────────────────────────────────────────┤
        │  Prediction Layer (Supervised ML Solar/Load Forecast)  │
        ├────────────────────────────────────────────────────────┤
        │  Safety Shield (Symbolic Forward-Chaining Rules)       │
        ├────────────────────────────────────────────────────────┤
        │  Physical Inverter, Battery, Breaker, Smart Appliances │
        └────────────────────────────────────────────────────────┘
        ```
        """)

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
                <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:12px; padding:1.2rem; height:100%;">
                    <div style="font-size:0.8rem; font-weight:700; color:#15803d; text-transform:uppercase;">Primary Recommendation</div>
                    <h3 style="color:#166534; margin:0.3rem 0;">⭐ {prim_p.name if prim_p else ''}</h3>
                    <p style="font-size:0.9rem; color:#1e293b; margin-top:0.5rem;"><b>Why:</b> {task_info['rationale']}</p>
                    <hr style="margin:0.8rem 0; border-color:#bbf7d0;">
                    <div style="font-size:0.82rem; color:#374151;">
                        <b>Core Mechanism:</b> {prim_p.core_mechanism if prim_p else ''}<br>
                        <b>Optimality:</b> {prim_p.optimality if prim_p else ''} | <b>Latency:</b> {prim_p.latency if prim_p else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_t2:
                st.markdown(f"""
                <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:12px; padding:1.2rem; height:100%;">
                    <div style="font-size:0.8rem; font-weight:700; color:#475569; text-transform:uppercase;">Viable Alternative / Complement</div>
                    <h3 style="color:#1e293b; margin:0.3rem 0;">🔄 {alt_p.name if alt_p else ''}</h3>
                    <p style="font-size:0.9rem; color:#475569; margin-top:0.5rem;">Can be paired with the primary paradigm for secondary multi-objective trade-offs.</p>
                    <hr style="margin:0.8rem 0; border-color:#e2e8f0;">
                    <div style="font-size:0.82rem; color:#374151;">
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
