"""
rule_engine.py — Symbolic reasoning & forward-chaining expert system for Smart Home Energy Rules.

Provides an explainable rule-based engine that evaluates state facts (tariffs, solar surplus,
battery state, indoor temperatures, grid demand response) and triggers transparent energy actions.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any, Optional
from src.energy_models import HourlyTelemetry, BatteryStorage, Appliance


@dataclass
class Rule:
    id: str
    name: str
    category: str
    priority: int                   # 1 (highest) to 10 (lowest)
    condition_desc: str
    action_desc: str
    rationale: str
    is_active: bool = True


@dataclass
class RuleActivation:
    rule_id: str
    rule_name: str
    category: str
    priority: int
    action_taken: str
    rationale: str
    trigger_facts: Dict[str, Any]


@dataclass
class InferenceTrace:
    hour: int
    input_facts: Dict[str, Any]
    matched_rules: List[str]
    fired_rules: List[RuleActivation]
    final_actions: List[str]
    explanation: str


# ── Built-in Knowledge Base of Energy Rules ───────────────────

BUILTIN_RULES: List[Rule] = [
    Rule(
        id="R01",
        name="Peak Price Load Curtailment",
        category="Tariff Optimization",
        priority=2,
        condition_desc="Current tariff is PEAK (≥ $0.40/kWh) and appliance priority is flexible (≥ 3).",
        action_desc="Defer flexible appliances (dishwasher, washing machine) out of peak hours.",
        rationale="Peak electricity prices are 3.75x higher than off-peak rates.",
    ),
    Rule(
        id="R02",
        name="Solar Surplus Self-Consumption",
        category="Renewable Maximization",
        priority=3,
        condition_desc="Solar generation exceeds total household baseload by at least 1.0 kW.",
        action_desc="Divert green solar surplus to charge home battery or pre-cool home.",
        rationale="Exporting to grid yields only $0.06/kWh feed-in tariff, whereas self-consuming avoids $0.24-$0.45/kWh grid import.",
    ),
    Rule(
        id="R03",
        name="Peak Battery Arbitrage Discharge",
        category="Storage Arbitrage",
        priority=4,
        condition_desc="Current tariff is PEAK and battery state of charge (SOC) > 20% reserve.",
        action_desc="Discharge battery to power household loads and eliminate grid import.",
        rationale="Discharging stored low-cost energy avoids expensive on-peak grid power purchases.",
    ),
    Rule(
        id="R04",
        name="Battery Emergency Reserve Protection",
        category="Resilience & Health",
        priority=1,
        condition_desc="Battery SOC drops to or below 20% minimum safety reserve.",
        action_desc="Inhibit further battery discharging and retain 2.0 kWh emergency buffer.",
        rationale="Protects lithium cell longevity and guarantees blackout resilience for critical circuits.",
    ),
    Rule(
        id="R05",
        name="Off-Peak Battery Pre-Charging",
        category="Storage Arbitrage",
        priority=5,
        condition_desc="Current hour is deep off-peak (00:00-05:00) with cheap rates ($0.12) and battery SOC < 60%.",
        action_desc="Charge battery from cheap off-peak grid power to prepare for morning peak.",
        rationale="Locks in the lowest tariff of the day to offset daytime and evening usage.",
    ),
    Rule(
        id="R06",
        name="Critical Demand-Response Emergency",
        category="Grid Reliability",
        priority=1,
        condition_desc="Utility Demand-Response alert active ($1.25/kWh surcharge).",
        action_desc="Shed all non-essential loads, set HVAC to eco-setpoint, and discharge battery if available.",
        rationale="Prevents grid blackout penalties and protects neighborhood transformer capacity.",
    ),
    Rule(
        id="R07",
        name="Thermal Comfort Band Safety Override",
        category="Comfort & Health",
        priority=1,
        condition_desc="Indoor temperature exceeds 26°C or drops below 18°C.",
        action_desc="Engage HVAC heat pump regardless of price until temperature returns to comfort band.",
        rationale="Resident health and thermal comfort strictly supersede economic optimization.",
    ),
    Rule(
        id="R08",
        name="Grid Solar Export Maximizer",
        category="Renewable Maximization",
        priority=6,
        condition_desc="Solar generation surplus exists AND battery is fully charged (SOC ≥ 95%).",
        action_desc="Export remaining green solar energy to local grid for feed-in credit.",
        rationale="Prevents solar inverter curtailment and earns feed-in credit when battery is full.",
    ),
]


class EnergyRuleEngine:
    """
    Symbolic Forward-Chaining Inference Engine.
    Evaluates home energy telemetry against rule conditions, resolves conflicts by priority,
    and returns transparent decision traces.
    """

    def __init__(self, rules: Optional[List[Rule]] = None):
        self.rules = list(rules) if rules is not None else list(BUILTIN_RULES)

    def evaluate_hour(
        self,
        telemetry: HourlyTelemetry,
        battery: Optional[BatteryStorage] = None,
        indoor_temp_c: float = 22.0,
        active_appliances: Optional[List[Appliance]] = None,
        appliances: Optional[List[Appliance]] = None,
    ) -> InferenceTrace:
        """
        Run forward chaining over the knowledge base for a specific hour.
        """
        battery = battery if battery is not None else BatteryStorage(capacity_kwh=10.0, current_soc=0.50)
        active_apps = active_appliances if active_appliances is not None else (appliances or [])
        app_load = sum(a.power_kw for a in active_apps if a.current_state == "ON")
        net_power = telemetry.baseload_demand_kw + app_load - telemetry.solar_generation_kw

        facts = {
            "hour": telemetry.hour,
            "tou_tariff": telemetry.tou_tariff,
            "is_peak": telemetry.is_peak,
            "solar_kw": telemetry.solar_generation_kw,
            "baseload_kw": telemetry.baseload_demand_kw,
            "appliance_load_kw": round(app_load, 2),
            "net_power_kw": round(net_power, 2),
            "battery_soc": round(battery.current_soc, 3),
            "battery_soc_pct": round(battery.current_soc * 100, 1),
            "indoor_temp_c": round(indoor_temp_c, 1),
            "outdoor_temp_c": telemetry.outdoor_temp_c,
            "dr_alert": telemetry.demand_response_active,
        }

        matched_rules: List[str] = []
        activations: List[RuleActivation] = []
        actions: List[str] = []

        # ── Rule Matching Phase ───────────────────────────────────

        # R07: Thermal Comfort Safety
        if indoor_temp_c > 26.0 or indoor_temp_c < 18.0:
            matched_rules.append("R07")
            activations.append(RuleActivation(
                rule_id="R07",
                rule_name="Thermal Comfort Band Safety Override",
                category="Comfort & Health",
                priority=1,
                action_taken="Engage HVAC Climate Control to restore 21°C comfort.",
                rationale=f"Indoor temperature ({indoor_temp_c:.1f}°C) is outside acceptable band [18°C, 26°C].",
                trigger_facts={"indoor_temp_c": indoor_temp_c},
            ))

        # R06: Demand Response Emergency
        if telemetry.demand_response_active:
            matched_rules.append("R06")
            activations.append(RuleActivation(
                rule_id="R06",
                rule_name="Critical Demand-Response Emergency",
                category="Grid Reliability",
                priority=1,
                action_taken="Shed non-essential loads and switch battery to maximum grid relief discharge.",
                rationale=f"Utility DR alert in effect with emergency rate of ${telemetry.tou_tariff:.2f}/kWh.",
                trigger_facts={"dr_alert": True, "tariff": telemetry.tou_tariff},
            ))

        # R04: Battery Reserve Protection
        if battery.current_soc <= battery.min_soc + 0.01:
            matched_rules.append("R04")
            activations.append(RuleActivation(
                rule_id="R04",
                rule_name="Battery Emergency Reserve Protection",
                category="Resilience & Health",
                priority=1,
                action_taken="Lock battery discharge; preserve 20% minimum reserve for outage backup.",
                rationale=f"Battery SOC is at {battery.current_soc*100:.1f}%, reaching the 20% reserve threshold.",
                trigger_facts={"battery_soc": battery.current_soc},
            ))

        # R01: Peak Price Load Curtailment
        if telemetry.is_peak and any(a.priority >= 3 for a in active_apps):
            matched_rules.append("R01")
            curt_apps = [a.name for a in active_apps if a.priority >= 3]
            activations.append(RuleActivation(
                rule_id="R01",
                rule_name="Peak Price Load Curtailment",
                category="Tariff Optimization",
                priority=2,
                action_taken=f"Defer/pause flexible appliances: {', '.join(curt_apps)}.",
                rationale=f"Peak tariff active (${telemetry.tou_tariff:.2f}/kWh). Shifting loads saves up to 73% energy cost.",
                trigger_facts={"is_peak": True, "curtailed_apps": curt_apps},
            ))

        # R02: Solar Surplus Self-Consumption
        surplus_kw = telemetry.solar_generation_kw - (telemetry.baseload_demand_kw + app_load)
        if surplus_kw >= 1.0 and battery.current_soc < 0.95:
            matched_rules.append("R02")
            activations.append(RuleActivation(
                rule_id="R02",
                rule_name="Solar Surplus Self-Consumption",
                category="Renewable Maximization",
                priority=3,
                action_taken=f"Charge battery with {min(surplus_kw, battery.max_charge_kw):.2f} kW solar surplus.",
                rationale=f"Solar surplus of {surplus_kw:.2f} kW detected. Storing energy captures full retail value.",
                trigger_facts={"solar_kw": telemetry.solar_generation_kw, "surplus_kw": round(surplus_kw, 2)},
            ))

        # R03: Peak Battery Arbitrage Discharge
        if telemetry.is_peak and battery.current_soc > battery.min_soc + 0.05 and not telemetry.demand_response_active:
            matched_rules.append("R03")
            discharge_power = min(battery.max_discharge_kw, max(0.0, net_power))
            activations.append(RuleActivation(
                rule_id="R03",
                rule_name="Peak Battery Arbitrage Discharge",
                category="Storage Arbitrage",
                priority=4,
                action_taken=f"Discharge battery at {discharge_power:.2f} kW to offset expensive grid import.",
                rationale=f"On-peak rate is ${telemetry.tou_tariff:.2f}/kWh with {battery.current_soc*100:.1f}% battery charge available.",
                trigger_facts={"is_peak": True, "battery_soc": battery.current_soc},
            ))

        # R05: Off-Peak Battery Pre-Charging
        if 0 <= telemetry.hour <= 5 and telemetry.tou_tariff <= 0.15 and battery.current_soc < 0.60:
            matched_rules.append("R05")
            activations.append(RuleActivation(
                rule_id="R05",
                rule_name="Off-Peak Battery Pre-Charging",
                category="Storage Arbitrage",
                priority=5,
                action_taken="Pre-charge battery at 3.0 kW from low-cost off-peak grid.",
                rationale=f"Lowest tariff of the day (${telemetry.tou_tariff:.2f}/kWh) at hour {telemetry.hour:02d}:00.",
                trigger_facts={"hour": telemetry.hour, "tariff": telemetry.tou_tariff},
            ))

        # R08: Grid Solar Export Maximizer
        if surplus_kw > 0 and battery.current_soc >= 0.95:
            matched_rules.append("R08")
            activations.append(RuleActivation(
                rule_id="R08",
                rule_name="Grid Solar Export Maximizer",
                category="Renewable Maximization",
                priority=6,
                action_taken=f"Export {surplus_kw:.2f} kW clean excess solar to grid.",
                rationale="Battery is fully charged at ≥95%. Exporting maximizes feed-in revenue.",
                trigger_facts={"battery_soc": battery.current_soc, "surplus_kw": round(surplus_kw, 2)},
            ))

        # ── Conflict Resolution by Priority ───────────────────────
        activations.sort(key=lambda a: a.priority)

        for act in activations:
            actions.append(f"[{act.rule_id} P{act.priority}] {act.action_taken}")

        # Build natural-language explanation
        if activations:
            reasons = [f"• **{a.rule_name} (Priority {a.priority})**: {a.rationale} → *Action*: {a.action_taken}" for a in activations]
            explanation = (
                f"Hour {telemetry.hour:02d}:00 Reasoning Trace:\n"
                f"Fired {len(activations)} active rules based on telemetry "
                f"(Rate: ${telemetry.tou_tariff}/kWh, Solar: {telemetry.solar_generation_kw}kW, "
                f"Battery: {battery.current_soc*100:.1f}%):\n" + "\n".join(reasons)
            )
        else:
            explanation = (
                f"Hour {telemetry.hour:02d}:00: Normal steady-state operation. "
                f"No constraint thresholds or rule triggers were breached."
            )

        return InferenceTrace(
            hour=telemetry.hour,
            input_facts=facts,
            matched_rules=matched_rules,
            fired_rules=activations,
            final_actions=actions,
            explanation=explanation,
        )
