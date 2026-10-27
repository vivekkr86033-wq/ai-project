"""
2_📋_Rule_Based_Energy_Reasoning.py — Symbolic Rule Reasoning & Forward-Chaining Expert System.

Evaluates transparent production rules (IF-THEN) against real-time telemetry to enforce
tariffs, battery reserves, solar self-consumption, and thermal safety overrides.
"""

import streamlit as st
import pandas as pd
from src.energy_models import HourlyTelemetry, BatteryStorage, get_default_appliances, get_simulation_profile
from src.rule_engine import EnergyRuleEngine, BUILTIN_RULES, Rule


def render():
    st.markdown("## 📋 Symbolic Energy Rules & Inference Engine")
    st.markdown(
        "A classical **Symbolic Expert System** executing forward-chaining deduction over the smart home knowledge base. "
        "Provides 100% deterministic safety guarantees and transparent audit trails for every physical control action."
    )

    tab_eval, tab_rules = st.tabs(["🧪 Interactive Rule Sandbox & Tracer", "📚 Knowledge Base Rule Catalog"])

    # ── Tab 1: Interactive Sandbox ─────────────────────────────
    with tab_eval:
        st.markdown("### 🎛️ Live Working Memory & Rule Tracer")
        st.caption("Adjust state parameters below to inspect which production rules fire, their priority conflict resolution, and the generated reasoning.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sel_hour = st.slider("Hour of Day", 0, 23, 18, format="%02d:00")
            is_peak = (16 <= sel_hour <= 21)
            tariff = st.number_input("TOU Tariff ($/kWh)", 0.05, 2.00, 0.45 if is_peak else 0.12, 0.01)

        with col2:
            battery_soc_pct = st.slider("Battery SOC (%)", 5, 100, 35, 1)
            battery_soc = battery_soc_pct / 100.0

        with col3:
            solar_kw = st.number_input("Solar Generation (kW)", 0.0, 10.0, 1.2 if (8 <= sel_hour <= 17) else 0.0, 0.5)
            baseload_kw = st.number_input("Household Baseload (kW)", 0.2, 5.0, 0.8, 0.1)

        with col4:
            indoor_temp = st.slider("Indoor Temp (°C)", 15.0, 32.0, 22.0, 0.5)
            dr_alert = st.toggle("🚨 Grid DR Emergency Alert", value=False)

        # Build telemetry & battery objects for evaluation
        tel = HourlyTelemetry(
            hour=sel_hour,
            tou_tariff=tariff,
            feed_in_tariff=0.06,
            solar_generation_kw=solar_kw,
            baseload_demand_kw=baseload_kw,
            outdoor_temp_c=28.0 if is_peak else 20.0,
            grid_carbon_g_per_kwh=480.0,
            is_peak=is_peak,
            demand_response_active=dr_alert,
        )

        battery = BatteryStorage(capacity_kwh=10.0, current_soc=battery_soc, min_soc=0.20)
        appliances = get_default_appliances()
        for a in appliances:
            a.current_state = "ON" if a.priority >= 3 else "OFF"

        engine = EnergyRuleEngine()
        trace = engine.evaluate_hour(tel, battery, indoor_temp_c=indoor_temp, active_appliances=appliances)

        st.markdown("---")
        st.markdown("### 🔍 Forward-Chaining Inference Result")

        res_col1, res_col2 = st.columns([1, 2])

        with res_col1:
            st.markdown("#### 📥 Working Memory Facts")
            st.json(trace.input_facts)

        with res_col2:
            st.markdown(f"#### ⚡ Fired Production Rules ({len(trace.fired_rules)} active)")
            if trace.fired_rules:
                for act in trace.fired_rules:
                    with st.container():
                        st.markdown(f"""
                        <div style="background:#f8fafc; border-left: 4px solid #3b82f6; padding: 0.8rem 1rem; border-radius: 6px; margin-bottom: 0.6rem;">
                            <div style="font-weight:700; color:#1e293b;">[{act.rule_id} — Priority {act.priority}] {act.rule_name}</div>
                            <div style="font-size:0.9rem; color:#059669; font-weight:600; margin-top:2px;">▶ Action: {act.action_taken}</div>
                            <div style="font-size:0.83rem; color:#64748b; margin-top:2px;">💡 Rationale: {act.rationale}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No rule thresholds were triggered. Normal steady-state operation.")

            st.markdown("#### 📜 Natural-Language Audit Trail")
            st.markdown(trace.explanation)

    # ── Tab 2: Rule Catalog ────────────────────────────────────
    with tab_rules:
        st.markdown("### 📚 Knowledge Base: Production Rules Catalog")
        st.caption("These symbolic production rules encode electrical engineering safety guidelines, utility tariffs, and thermodynamic comfort bounds.")

        rule_table = []
        for r in BUILTIN_RULES:
            rule_table.append({
                "Rule ID": r.id,
                "Name": r.name,
                "Category": r.category,
                "Priority": f"P{r.priority}",
                "Antecedent (IF Condition)": r.condition_desc,
                "Consequent (THEN Action)": r.action_desc,
                "Engineering Rationale": r.rationale,
            })

        df_rules = pd.DataFrame(rule_table)
        st.dataframe(df_rules, use_container_width=True, hide_index=True)


render()
