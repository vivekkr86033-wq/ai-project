"""
multi_agent.py — Autonomous & Multi-Agent System (MAS) for Smart Home Energy Control.

Implements distributed multi-agent architecture with specialized agents:
1. GridMonitorAgent (tariffs, grid stress, carbon intensity)
2. SolarStorageAgent (photovoltaics & battery state-of-charge management)
3. ClimateHVACAgent (indoor thermal comfort & rational temperature control)
4. FlexibleLoadAgent (appliance scheduling & deadline satisfaction)
5. CoordinatorAgent (central capacity arbiter enforcing main breaker limit & priority auctions)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal, Tuple
import time
import numpy as np

from src.energy_models import Appliance, BatteryStorage, HourlyTelemetry


@dataclass
class AgentMessage:
    timestamp_hour: int
    sender: str
    receiver: str
    performative: Literal["INFORM", "REQUEST", "PROPOSE", "ACCEPT", "REJECT", "CONFIRM"]
    topic: str
    content: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDecision:
    agent_id: str
    agent_name: str
    action_type: str
    target_power_kw: float
    reasoning: str
    status: str = "PROPOSED"  # PROPOSED, APPROVED, CURTAILED


@dataclass
class MultiAgentSimulationStep:
    hour: int
    telemetry: HourlyTelemetry
    messages: List[AgentMessage]
    agent_decisions: List[AgentDecision]
    approved_power_kw: float
    grid_import_kw: float
    battery_power_kw: float     # >0 charging, <0 discharging
    battery_soc: float
    indoor_temp_c: float
    notes: str


# ── Individual Agent Implementations ──────────────────────────

class GridMonitorAgent:
    """Monitors grid conditions, TOU rates, carbon intensity, and demand response."""
    def __init__(self):
        self.name = "Grid Monitor Agent"
        self.id = "grid_agent"

    def observe_and_inform(self, telemetry: HourlyTelemetry) -> List[AgentMessage]:
        messages = []
        if telemetry.is_peak:
            messages.append(AgentMessage(
                timestamp_hour=telemetry.hour,
                sender=self.id,
                receiver="coordinator",
                performative="INFORM",
                topic="PEAK_TARIFF_ALERT",
                content=f"Peak tariff active (${telemetry.tou_tariff}/kWh). Advise load shedding.",
                data={"tariff": telemetry.tou_tariff, "carbon": telemetry.grid_carbon_g_per_kwh},
            ))
        if telemetry.demand_response_active:
            messages.append(AgentMessage(
                timestamp_hour=telemetry.hour,
                sender=self.id,
                receiver="coordinator",
                performative="INFORM",
                topic="CRITICAL_GRID_EVENT",
                content="Utility Demand-Response alert! Emergency power reduction requested.",
                data={"emergency_rate": telemetry.tou_tariff},
            ))
        return messages


class SolarStorageAgent:
    """Controls battery charging, discharging, and solar self-consumption."""
    def __init__(self, battery: BatteryStorage):
        self.name = "Solar & Storage Agent"
        self.id = "storage_agent"
        self.battery = battery

    def decide_storage_action(
        self,
        telemetry: HourlyTelemetry,
        net_demand_kw: float,
    ) -> Tuple[AgentDecision, List[AgentMessage]]:
        messages = []
        soc = self.battery.current_soc
        solar = telemetry.solar_generation_kw

        # Rule 1: High solar surplus -> charge battery
        if solar > telemetry.baseload_demand_kw and soc < 0.98:
            surplus = solar - telemetry.baseload_demand_kw
            target_charge = min(surplus, self.battery.max_charge_kw)
            decision = AgentDecision(
                agent_id=self.id,
                agent_name=self.name,
                action_type="CHARGE_SOLAR",
                target_power_kw=target_charge,
                reasoning=f"Absorbing {surplus:.2f} kW clean solar surplus into battery (SOC: {soc*100:.1f}%).",
            )
            messages.append(AgentMessage(
                timestamp_hour=telemetry.hour,
                sender=self.id,
                receiver="coordinator",
                performative="PROPOSE",
                topic="BATTERY_CHARGING",
                content=f"Charging battery at {target_charge:.2f} kW using rooftop solar.",
            ))
            return decision, messages

        # Rule 2: Peak rate and battery has energy -> discharge
        if telemetry.is_peak and soc > self.battery.min_soc:
            avail = min(self.battery.max_discharge_kw, max(0.0, net_demand_kw))
            decision = AgentDecision(
                agent_id=self.id,
                agent_name=self.name,
                action_type="DISCHARGE_PEAK",
                target_power_kw=-avail,
                reasoning=f"Discharging {avail:.2f} kW to avoid peak grid tariff (${telemetry.tou_tariff}/kWh).",
            )
            messages.append(AgentMessage(
                timestamp_hour=telemetry.hour,
                sender=self.id,
                receiver="coordinator",
                performative="PROPOSE",
                topic="BATTERY_DISCHARGE",
                content=f"Offering {avail:.2f} kW battery discharge to offset peak load.",
            ))
            return decision, messages

        # Rule 3: Deep off-peak pre-charge
        if telemetry.hour in (1, 2, 3, 4) and soc < 0.60:
            target_charge = 3.0
            decision = AgentDecision(
                agent_id=self.id,
                agent_name=self.name,
                action_type="CHARGE_OFFPEAK",
                target_power_kw=target_charge,
                reasoning="Off-peak grid pre-charging at lowest $0.12/kWh tariff.",
            )
            return decision, messages

        # Idle
        decision = AgentDecision(
            agent_id=self.id,
            agent_name=self.name,
            action_type="IDLE",
            target_power_kw=0.0,
            reasoning=f"Battery standing by at {soc*100:.1f}% SOC.",
        )
        return decision, messages


class ClimateHVACAgent:
    """Manages home thermal comfort with rational cost-comfort tradeoff."""
    def __init__(self, target_temp_c: float = 21.5, band_c: float = 1.5):
        self.name = "Climate & HVAC Agent"
        self.id = "climate_agent"
        self.target_temp = target_temp_c
        self.band = band_c
        self.current_temp = target_temp_c

    def step_temperature(self, outdoor_temp_c: float, hvac_kw: float, is_cooling: bool = True) -> float:
        """Simple 1R-1C thermal resistance-capacitance indoor model."""
        heat_gain = 0.15 * (outdoor_temp_c - self.current_temp)
        if is_cooling:
            hvac_effect = -0.55 * hvac_kw
        else:
            hvac_effect = 0.55 * hvac_kw
        self.current_temp += heat_gain + hvac_effect
        return round(self.current_temp, 2)

    def decide_climate_action(self, telemetry: HourlyTelemetry) -> Tuple[AgentDecision, List[AgentMessage]]:
        messages = []
        is_cooling = telemetry.outdoor_temp_c > self.target_temp
        temp_error = self.current_temp - self.target_temp

        # Need cooling
        if is_cooling and temp_error > 0.5:
            # If peak price, modulate power down to save money unless thermal comfort is violated
            power = 1.8 if (telemetry.is_peak and temp_error < 2.0) else 3.2
            decision = AgentDecision(
                agent_id=self.id,
                agent_name=self.name,
                action_type="COOLING",
                target_power_kw=power,
                reasoning=f"Indoor temp ({self.current_temp:.1f}°C) above target ({self.target_temp}°C). Running AC.",
            )
            messages.append(AgentMessage(
                timestamp_hour=telemetry.hour,
                sender=self.id,
                receiver="coordinator",
                performative="REQUEST",
                topic="HVAC_POWER_REQUEST",
                content=f"Requesting {power:.1f} kW for cooling.",
                data={"power_kw": power, "temp_error": temp_error},
            ))
            return decision, messages

        decision = AgentDecision(
            agent_id=self.id,
            agent_name=self.name,
            action_type="IDLE",
            target_power_kw=0.0,
            reasoning=f"Indoor temp ({self.current_temp:.1f}°C) inside acceptable comfort band.",
        )
        return decision, messages


class FlexibleLoadAgent:
    """Represents smart shiftable household appliances (EV, laundry, dishwasher)."""
    def __init__(self, appliances: List[Appliance]):
        self.name = "Flexible Load Agent"
        self.id = "loads_agent"
        self.appliances = appliances

    def get_requests(self, hour: int, schedule: Dict[str, int]) -> Tuple[List[AgentDecision], List[AgentMessage]]:
        decisions = []
        messages = []

        for app in self.appliances:
            start_hour = schedule.get(app.id, app.earliest_start)
            # Check if appliance should run during this hour
            if (start_hour <= hour < start_hour + app.duration_hours) or \
               (start_hour + app.duration_hours > 24 and (hour >= start_hour or hour < (start_hour + app.duration_hours) % 24)):
                dec = AgentDecision(
                    agent_id=self.id,
                    agent_name=f"{app.name} Agent",
                    action_type="RUN_APPLIANCE",
                    target_power_kw=app.power_kw,
                    reasoning=f"Scheduled run hour for {app.name} (Priority {app.priority}, Deadline {app.deadline}:00).",
                )
                decisions.append(dec)
                messages.append(AgentMessage(
                    timestamp_hour=hour,
                    sender=self.id,
                    receiver="coordinator",
                    performative="REQUEST",
                    topic="APPLIANCE_POWER_ALLOCATION",
                    content=f"Requesting {app.power_kw} kW for {app.name}.",
                    data={"appliance_id": app.id, "power_kw": app.power_kw, "priority": app.priority},
                ))

        return decisions, messages


class CoordinatorAgent:
    """
    Central capacity arbiter and auction mediator.
    Enforces maximum grid breaker capacity (e.g. 10.0 kW) and resolves multi-agent load conflicts.
    """
    def __init__(self, max_grid_kw: float = 10.0):
        self.name = "Central Coordinator Agent"
        self.id = "coordinator"
        self.max_grid_kw = max_grid_kw

    def arbitrate_power(
        self,
        hour: int,
        telemetry: HourlyTelemetry,
        storage_dec: AgentDecision,
        climate_dec: AgentDecision,
        load_decs: List[AgentDecision],
    ) -> Tuple[List[AgentDecision], List[AgentMessage], float, float]:
        messages = []
        approved: List[AgentDecision] = []

        battery_kw = storage_dec.target_power_kw
        total_requested = (
            telemetry.baseload_demand_kw +
            climate_dec.target_power_kw +
            sum(d.target_power_kw for d in load_decs) +
            (battery_kw if battery_kw > 0 else 0.0)
        )

        net_grid = total_requested - telemetry.solar_generation_kw - (-battery_kw if battery_kw < 0 else 0.0)

        # Capacity check
        if net_grid > self.max_grid_kw:
            # First throttle optional battery charging if active
            if battery_kw > 0:
                excess = net_grid - self.max_grid_kw
                reduce_charge = min(battery_kw, excess)
                battery_kw -= reduce_charge
                storage_dec.target_power_kw = battery_kw
                storage_dec.reasoning += f" [Charge throttled by Coordinator to {battery_kw:.2f} kW]"
                net_grid -= reduce_charge

            # If still overloaded, curtail lowest-priority appliances
            sorted_loads = sorted(load_decs, key=lambda d: d.target_power_kw, reverse=True)
            curtailed_kw = 0.0

            for dec in sorted_loads:
                if net_grid - curtailed_kw > self.max_grid_kw:
                    dec.status = "CURTAILED"
                    dec.reasoning += f" [CURTAILED by Coordinator: Overloads {self.max_grid_kw} kW main breaker]"
                    curtailed_kw += dec.target_power_kw
                    messages.append(AgentMessage(
                        timestamp_hour=hour,
                        sender=self.id,
                        receiver=dec.agent_id,
                        performative="REJECT",
                        topic="POWER_CURTAILMENT",
                        content=f"Power request denied for {dec.agent_name} due to {self.max_grid_kw} kW breaker safety limit.",
                    ))
                else:
                    dec.status = "APPROVED"
                    approved.append(dec)

            climate_dec.status = "APPROVED"
            storage_dec.status = "APPROVED"
            approved.extend([climate_dec, storage_dec])
        else:
            climate_dec.status = "APPROVED"
            storage_dec.status = "APPROVED"
            for dec in load_decs:
                dec.status = "APPROVED"
            approved.extend([climate_dec, storage_dec] + load_decs)

            messages.append(AgentMessage(
                timestamp_hour=hour,
                sender=self.id,
                receiver="all",
                performative="CONFIRM",
                topic="SCHEDULE_APPROVED",
                content=f"All power requests approved. Net grid demand: {max(0.0, net_grid):.2f} kW ≤ {self.max_grid_kw} kW.",
            ))

        final_load = sum(d.target_power_kw for d in approved if d.target_power_kw > 0) + telemetry.baseload_demand_kw
        final_bat = storage_dec.target_power_kw
        final_grid = max(0.0, final_load - telemetry.solar_generation_kw - (-final_bat if final_bat < 0 else 0.0))

        return approved, messages, round(final_load, 2), round(final_grid, 2)


# ── Full 24-Hour Multi-Agent Simulation Engine ─────────────────

def run_multi_agent_simulation(
    appliances: List[Appliance],
    telemetry_profile: List[HourlyTelemetry],
    schedule: Dict[str, int],
    battery_capacity: float = 10.0,
    max_grid_kw: float = 10.0,
) -> List[MultiAgentSimulationStep]:
    """
    Simulate autonomous coordination across 24 hours with inter-agent message logs.
    """
    battery = BatteryStorage(capacity_kwh=battery_capacity, current_soc=0.55)
    grid_agent = GridMonitorAgent()
    storage_agent = SolarStorageAgent(battery)
    climate_agent = ClimateHVACAgent(target_temp_c=21.5)
    loads_agent = FlexibleLoadAgent(appliances)
    coordinator = CoordinatorAgent(max_grid_kw=max_grid_kw)

    simulation_steps: List[MultiAgentSimulationStep] = []

    for h, tel in enumerate(telemetry_profile):
        all_messages: List[AgentMessage] = []

        # 1. Grid Agent informs
        grid_msgs = grid_agent.observe_and_inform(tel)
        all_messages.extend(grid_msgs)

        # 2. Climate Agent decides
        climate_dec, climate_msgs = climate_agent.decide_climate_action(tel)
        all_messages.extend(climate_msgs)

        # 3. Flexible Loads Agent requests
        load_decs, load_msgs = loads_agent.get_requests(h, schedule)
        all_messages.extend(load_msgs)

        # 4. Storage Agent decides
        temp_net = tel.baseload_demand_kw + sum(d.target_power_kw for d in load_decs) + climate_dec.target_power_kw - tel.solar_generation_kw
        storage_dec, storage_msgs = storage_agent.decide_storage_action(tel, temp_net)
        all_messages.extend(storage_msgs)

        # 5. Coordinator arbitrates
        approved_decs, coord_msgs, approved_load, grid_import = coordinator.arbitrate_power(
            h, tel, storage_dec, climate_dec, load_decs
        )
        all_messages.extend(coord_msgs)

        # Apply battery update
        actual_bat_kw, new_soc = battery.step(storage_dec.target_power_kw)

        # Apply climate temp drift
        hvac_kw = climate_dec.target_power_kw if climate_dec.status == "APPROVED" else 0.0
        new_temp = climate_agent.step_temperature(tel.outdoor_temp_c, hvac_kw)

        notes = f"Grid Import: {grid_import:.2f}kW | Solar: {tel.solar_generation_kw}kW | Battery: {new_soc*100:.1f}% | Temp: {new_temp:.1f}°C"

        simulation_steps.append(MultiAgentSimulationStep(
            hour=h,
            telemetry=tel,
            messages=all_messages,
            agent_decisions=approved_decs,
            approved_power_kw=round(approved_load, 2),
            grid_import_kw=round(grid_import, 2),
            battery_power_kw=round(actual_bat_kw, 2),
            battery_soc=round(new_soc, 3),
            indoor_temp_c=new_temp,
            notes=notes,
        ))

    return simulation_steps
