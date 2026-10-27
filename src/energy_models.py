"""
energy_models.py — Data structures, appliance models, tariff schedules,
and 24-hour environmental simulation profiles for Smart Home Energy Management.
"""

from dataclasses import dataclass, field
from typing import Literal, Dict, List, Any
import numpy as np


@dataclass
class Appliance:
    """Represents a smart home electrical appliance."""
    id: str
    name: str
    category: Literal["shiftable", "thermostatic", "critical", "storage"]
    power_kw: float
    duration_hours: int
    earliest_start: int = 0         # Hour 0..23
    deadline: int = 24              # Hour 1..24
    priority: int = 2               # 1 (high) to 5 (low)
    current_state: str = "OFF"      # "OFF", "ON", "STANDBY"
    comfort_weight: float = 1.0     # Penalty multiplier for delay past ideal time
    preferred_start: int = 18       # User's default or preferred start hour
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "power_kw": self.power_kw,
            "duration_hours": self.duration_hours,
            "earliest_start": self.earliest_start,
            "deadline": self.deadline,
            "priority": self.priority,
            "current_state": self.current_state,
            "comfort_weight": self.comfort_weight,
            "preferred_start": self.preferred_start,
            "description": self.description,
        }


@dataclass
class BatteryStorage:
    """Residential battery energy storage system (BESS)."""
    capacity_kwh: float = 10.0
    max_charge_kw: float = 4.0
    max_discharge_kw: float = 4.0
    roundtrip_efficiency: float = 0.90
    min_soc: float = 0.20          # 20% reserve for grid resilience
    current_soc: float = 0.50      # Current state-of-charge (0.0 to 1.0)

    @property
    def current_energy_kwh(self) -> float:
        return self.capacity_kwh * self.current_soc

    @property
    def available_discharge_kwh(self) -> float:
        return max(0.0, (self.current_soc - self.min_soc) * self.capacity_kwh)

    @property
    def available_charge_kwh(self) -> float:
        return max(0.0, (1.0 - self.current_soc) * self.capacity_kwh)

    def step(self, power_kw: float) -> tuple[float, float]:
        """
        Simulate battery charge (>0) or discharge (<0) for 1 hour.
        Returns (actual_power_kw, new_soc).
        """
        if power_kw > 0:
            # Charging
            effective_power = min(power_kw, self.max_charge_kw)
            effective_charge = effective_power * np.sqrt(self.roundtrip_efficiency)
            possible_charge = min(effective_charge, self.available_charge_kwh)
            actual_power = possible_charge / max(np.sqrt(self.roundtrip_efficiency), 0.01)
            self.current_soc = min(1.0, self.current_soc + (possible_charge / self.capacity_kwh))
            return actual_power, self.current_soc
        elif power_kw < 0:
            # Discharging
            req_discharge = abs(power_kw)
            effective_discharge = min(req_discharge, self.max_discharge_kw)
            possible_draw = min(effective_discharge, self.available_discharge_kwh)
            actual_delivered = possible_draw * np.sqrt(self.roundtrip_efficiency)
            self.current_soc = max(self.min_soc, self.current_soc - (possible_draw / self.capacity_kwh))
            return -actual_delivered, self.current_soc
        return 0.0, self.current_soc


@dataclass
class HourlyTelemetry:
    """Telemetry readings and external grid parameters for 1 hour."""
    hour: int
    tou_tariff: float            # $/kWh
    feed_in_tariff: float        # $/kWh (solar export rate)
    solar_generation_kw: float   # Solar PV output
    baseload_demand_kw: float    # Uncontrollable baseload (lights, electronics, fridge)
    outdoor_temp_c: float        # Outdoor temperature (°C)
    grid_carbon_g_per_kwh: float # Carbon intensity (g CO2 / kWh)
    is_peak: bool = False
    demand_response_active: bool = False


# ── Default Smart Appliances ─────────────────────────────────

def get_default_appliances() -> list[Appliance]:
    return [
        Appliance(
            id="ev_charger",
            name="Electric Vehicle Charger",
            category="shiftable",
            power_kw=7.0,
            duration_hours=4,
            earliest_start=18,
            deadline=7,          # Next morning 7 AM (wrap-around handled by horizon)
            priority=1,
            preferred_start=18,
            comfort_weight=3.0,
            description="Level 2 EV charger requiring 4 hours of charging before morning commute.",
        ),
        Appliance(
            id="water_heater",
            name="Heat Pump Water Heater",
            category="thermostatic",
            power_kw=3.0,
            duration_hours=3,
            earliest_start=0,
            deadline=24,
            priority=2,
            preferred_start=6,
            comfort_weight=2.0,
            description="Domestic hot water storage tank with thermal buffer capacity.",
        ),
        Appliance(
            id="dishwasher",
            name="Smart Dishwasher",
            category="shiftable",
            power_kw=1.8,
            duration_hours=2,
            earliest_start=19,
            deadline=24,
            priority=3,
            preferred_start=20,
            comfort_weight=1.2,
            description="Eco-cycle dishwasher that can run anytime before midnight.",
        ),
        Appliance(
            id="washing_machine",
            name="Washing Machine & Dryer",
            category="shiftable",
            power_kw=2.5,
            duration_hours=2,
            earliest_start=12,
            deadline=21,
            priority=3,
            preferred_start=17,
            comfort_weight=1.0,
            description="Combined laundry cycle with flexible daytime/afternoon scheduling.",
        ),
        Appliance(
            id="hvac_heatpump",
            name="HVAC Climate Heat Pump",
            category="thermostatic",
            power_kw=3.5,
            duration_hours=8,
            earliest_start=0,
            deadline=24,
            priority=1,
            preferred_start=14,
            comfort_weight=4.0,
            description="Main variable-speed heating/cooling inverter heat pump.",
        ),
        Appliance(
            id="refrigerator",
            name="Smart Refrigerator",
            category="critical",
            power_kw=0.25,
            duration_hours=24,
            earliest_start=0,
            deadline=24,
            priority=1,
            preferred_start=0,
            comfort_weight=5.0,
            description="Continuous food preservation load with minor compressor modulation.",
        ),
    ]


# ── 24-Hour Simulation Scenarios ──────────────────────────────

def get_simulation_profile(scenario: str = "summer_peak") -> list[HourlyTelemetry]:
    """
    Generate realistic 24-hour time series for tariffs, solar, baseload, and outdoor temp.
    """
    telemetry = []
    
    # 24-Hour TOU tariff curve ($/kWh)
    # Peak (16-21): $0.45, Shoulder (07-16, 21-23): $0.24, Off-Peak (23-07): $0.12
    # Solar Feed-in tariff: $0.06/kWh
    for h in range(24):
        is_peak = (16 <= h <= 21)
        if is_peak:
            rate = 0.45
        elif 7 <= h < 16 or 21 < h <= 23:
            rate = 0.24
        else:
            rate = 0.12

        fit = 0.06
        dr_active = (scenario == "critical_event" and 17 <= h <= 19)
        if dr_active:
            rate = 1.25  # Demand response penalty surcharge

        if scenario == "summer_peak":
            # High solar curve peaking at 12:00-13:00 (up to 6.2 kW)
            solar = max(0.0, 6.2 * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0.0
            # Summer outdoor temp peaking in late afternoon
            temp = 22.0 + 13.0 * np.sin(np.pi * (h - 8) / 14) if 8 <= h <= 22 else 21.0
            baseload = 0.6 + 0.3 * np.sin(np.pi * h / 24) + (0.5 if 18 <= h <= 22 else 0.0)
            carbon = 420.0 - 150.0 * (solar / 6.2) + (80.0 if is_peak else 0.0)

        elif scenario == "winter_heating":
            # Low solar peaking at ~2.4 kW
            solar = max(0.0, 2.4 * np.sin(np.pi * (h - 7) / 10)) if 7 <= h <= 17 else 0.0
            temp = 3.0 + 7.0 * np.sin(np.pi * (h - 9) / 12) if 9 <= h <= 21 else 2.0
            baseload = 0.8 + 0.4 * np.sin(np.pi * h / 24) + (0.6 if 6 <= h <= 9 or 18 <= h <= 22 else 0.0)
            carbon = 510.0 - 60.0 * (solar / 2.4) + (60.0 if is_peak else 0.0)

        else: # "critical_event" / default
            solar = max(0.0, 5.0 * np.sin(np.pi * (h - 6) / 12)) if 6 <= h <= 18 else 0.0
            temp = 28.0 + 8.0 * np.sin(np.pi * (h - 8) / 14) if 8 <= h <= 22 else 24.0
            baseload = 0.7 + 0.4 * np.sin(np.pi * h / 24)
            carbon = 480.0 if not dr_active else 650.0

        telemetry.append(HourlyTelemetry(
            hour=h,
            tou_tariff=round(rate, 3),
            feed_in_tariff=fit,
            solar_generation_kw=round(float(solar), 2),
            baseload_demand_kw=round(float(baseload), 2),
            outdoor_temp_c=round(float(temp), 1),
            grid_carbon_g_per_kwh=round(float(carbon), 1),
            is_peak=is_peak,
            demand_response_active=dr_active,
        ))

    return telemetry
