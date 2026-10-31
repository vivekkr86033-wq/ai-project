"""
2_📋_Rule_Based_Energy_Reasoning.py — Symbolic Rule Reasoning & Forward-Chaining Expert System.

Evaluates transparent production rules (IF-THEN) against real-time telemetry to enforce
tariffs, battery reserves, solar self-consumption, and thermal safety overrides.
"""

import streamlit as st
import pandas as pd
from src.energy_models import HourlyTelemetry, BatteryStorage, get_default_appliances
from src.rule_engine import EnergyRuleEngine, BUILTIN_RULES
from src.ui_theme import (
    inject_custom_css,
    render_hero_banner,
    render_kpi_card,
    render_sidebar_header,
    render_sidebar_footer,
)


def render():
    inject_custom_css()

    with st.sidebar:
        render_sidebar_header()
        st.markdown("#### 📋 Module Navigation")
        st.caption("Active Module: **Rule-Based Energy Reasoning**")
        st.markdown("---")
        render_sidebar_footer()

    render_hero_banner(
        title="📋 Symbolic Energy Rules & Inference Engine",
        subtitle="A classical Symbolic Expert System executing forward-chaining deduction over the smart home knowledge base. Provides 100% deterministic safety guarantees and transparent audit trails for every physical control action.",
        badges=[
            ("📜 Forward-Chaining Rete-Like Deduction", "agent"),
            ("🛡️ 100% Deterministic Safety Overrides", "peak"),
            ("🔋 Battery Reserve Protection Floor", "battery"),
            ("☀️ Solar Self-Consumption Priority", "solar"),
        ],
    )

    tab_eval, tab_rules = st.tabs(["🧪 Interactive Rule Sandbox & Tracer", "📚 Knowledge Base Rule Catalog"])

    # ── Tab 1: Interactive Sandbox ─────────────────────────────
    with tab_eval:
        st.markdown("### 🎛️ Live Working Memory & Rule Tracer")
        st.caption("Select a scenario preset or manually adjust parameters below to trigger the production rule engine and inspect conflict resolution.")

        # Interactive Scenario Presets
        st.markdown("##### ⚡ Quick Scenario Presets")
        p1, p2, p3, p4 = st.columns(4)
        if "rule_preset" not in st.session_state:
            st.session_state.rule_preset = "peak"

        with p1:
            if st.button("🚨 18:00 Peak Tariff ($0.45)", use_container_width=True):
                st.session_state.rule_preset = "peak"
        with p2:
            if st.button("☀️ 13:00 Solar Surplus (6 kW)", use_container_width=True):
                st.session_state.rule_preset = "solar"
        with p3:
            if st.button("🔋 Low Battery SOC (15%)", use_container_width=True):
                st.session_state.rule_preset = "battery"
        with p4:
            if st.button("❄️ Thermal Cold Draft (16°C)", use_container_width=True):
                st.session_state.rule_preset = "thermal"

        preset = st.session_state.rule_preset
        if preset == "solar":
            def_hour, def_tariff, def_soc, def_solar, def_base, def_temp, def_dr = 13, 0.24, 45, 6.2, 0.9, 23.0, False
        elif preset == "battery":
            def_hour, def_tariff, def_soc, def_solar, def_base, def_temp, def_dr = 19, 0.45, 15, 0.0, 1.4, 24.0, False
        elif preset == "thermal":
            def_hour, def_tariff, def_soc, def_solar, def_base, def_temp, def_dr = 7, 0.12, 60, 0.2, 1.1, 16.0, False
        else:  # peak
            def_hour, def_tariff, def_soc, def_solar, def_base, def_temp, def_dr = 18, 0.45, 40, 0.8, 1.2, 25.5, True

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            sel_hour = st.slider("Hour of Day", 0, 23, def_hour, format="%02d:00")
            is_peak = (16 <= sel_hour <= 21)
            tariff = st.number_input("TOU Tariff ($/kWh)", 0.05, 2.00, def_tariff, 0.01)

        with col2:
            battery_soc_pct = st.slider("Battery SOC (%)", 5, 100, def_soc, 1)
            battery_soc = battery_soc_pct / 100.0

        with col3:
            solar_kw = st.number_input("Solar Generation (kW)", 0.0, 10.0, def_solar, 0.5)
            baseload_kw = st.number_input("Household Baseload (kW)", 0.2, 5.0, def_base, 0.1)

        with col4:
            indoor_temp = st.slider("Indoor Temp (°C)", 14.0, 32.0, def_temp, 0.5)
            dr_alert = st.toggle("🚨 Grid DR Emergency Alert", value=def_dr)

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

        res_col1, res_col2 = st.columns([1.1, 1.9])

        with res_col1:
            st.markdown("#### 📥 Working Memory Facts")
            facts = trace.input_facts
            st.markdown(f"""
            <div class="node-box" style="text-align:left; align-items:flex-start; padding:1.2rem;">
                <div style="font-size:0.85rem; color:#94a3b8; font-weight:600; margin-bottom:8px;">EXTRACTED STATE FACTS</div>
                <div style="font-size:0.9rem; color:#f1f5f9; line-height:1.7;">
                    • <b>Hour:</b> <code>{facts.get('hour', sel_hour):02d}:00</code> ({'PEAK' if is_peak else 'OFF-PEAK'})<br>
                    • <b>Tariff:</b> <code>${facts.get('tou_tariff', tariff):.2f}/kWh</code><br>
                    • <b>Battery SOC:</b> <code>{battery_soc_pct}%</code> (Min Reserve: 20%)<br>
                    • <b>Solar PV:</b> <code>{solar_kw:.2f} kW</code><br>
                    • <b>Baseload:</b> <code>{baseload_kw:.2f} kW</code><br>
                    • <b>Indoor Temp:</b> <code>{indoor_temp:.1f}°C</code> (Safe: 18–26°C)<br>
                    • <b>DR Alert:</b> <code style="color:{'#f87171' if dr_alert else '#34d399'}">{dr_alert}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with res_col2:
            st.markdown(f"#### ⚡ Fired Production Rules ({len(trace.fired_rules)} Active)")
            if trace.fired_rules:
                for act in trace.fired_rules:
                    st.markdown(f"""
                    <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.08); border-left: 4px solid #3b82f6; padding: 1rem 1.2rem; border-radius: 12px; margin-bottom: 0.75rem; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#f8fafc; font-size:1rem;">[{act.rule_id}] {act.rule_name}</span>
                            <span class="badge-pill badge-ai" style="margin:0;">Priority P{act.priority}</span>
                        </div>
                        <div style="font-size:0.92rem; color:#34d399; font-weight:600; margin-top:6px;">▶ Action: {act.action_taken}</div>
                        <div style="font-size:0.84rem; color:#94a3b8; margin-top:4px; line-height:1.45;">💡 Rationale: {act.rationale}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ No rule safety thresholds were triggered. The system remains in normal steady-state economic dispatch.")

            st.markdown("#### 📜 Natural-Language Audit Trail")
            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.06); padding: 1rem 1.2rem; border-radius: 12px; font-size:0.92rem; line-height:1.6; color:#cbd5e1;">
                {trace.explanation}
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 2: Rule Catalog ────────────────────────────────────
    with tab_rules:
        st.markdown("### 📚 Knowledge Base: Production Rules Catalog")
        st.caption("Symbolic production rules encoding electrical engineering safety, utility tariffs, and thermodynamic comfort bounds.")

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
