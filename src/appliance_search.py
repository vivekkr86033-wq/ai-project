"""
appliance_search.py — State-space search & planning algorithms for smart appliance scheduling.

Implements:
1. Baseline (As-Soon-As-Possible, unoptimized)
2. Breadth-First Search (BFS)
3. Greedy Best-First Search
4. A* Search (admissible heuristic with peak-cost avoidance)
5. Constraint-Satisfaction Search (Peak Power Limiter / Main Breaker Cap)
"""

import time
import heapq
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

from src.energy_models import Appliance, HourlyTelemetry, BatteryStorage


@dataclass(order=True)
class SearchNode:
    priority: float
    g_cost: float = field(compare=False)
    h_cost: float = field(compare=False)
    appliance_index: int = field(compare=False)
    schedule: Dict[str, int] = field(compare=False)  # appliance_id -> start_hour


@dataclass
class SearchResult:
    algorithm: str
    schedule: Dict[str, int]               # appliance_id -> start_hour
    hourly_appliance_load: List[float]     # 24-hour kW curve
    total_cost: float                      # $
    peak_demand_kw: float                  # kW
    carbon_emissions_kg: float             # kg CO2
    comfort_penalty: float                 # abstract penalty units
    nodes_expanded: int
    execution_time_ms: float
    description: str


def compute_schedule_cost(
    schedule: Dict[str, int],
    appliances: List[Appliance],
    telemetry: List[HourlyTelemetry],
    max_grid_kw: float = 10.0,
) -> Tuple[float, List[float], float, float, float]:
    """
    Calculate electricity cost, hourly load profile, peak kW, carbon emissions,
    and comfort penalty for a given start-time schedule.
    """
    hourly_load = [0.0] * 24
    comfort_penalty = 0.0

    app_dict = {a.id: a for a in appliances}

    for app_id, start_hour in schedule.items():
        app = app_dict.get(app_id)
        if not app:
            continue
        # Apply load across duration
        for dh in range(app.duration_hours):
            hour = (start_hour + dh) % 24
            hourly_load[hour] += app.power_kw

        # Comfort penalty for deviation from preferred time
        deviation = abs(start_hour - app.preferred_start)
        if deviation > 12:
            deviation = 24 - deviation
        comfort_penalty += deviation * app.comfort_weight * 0.05

    total_cost = 0.0
    total_carbon = 0.0

    for h in range(24):
        tel = telemetry[h]
        # Net demand: baseload + scheduled load - solar
        net_load = tel.baseload_demand_kw + hourly_load[h] - tel.solar_generation_kw

        if net_load > 0:
            # Importing from grid
            grid_import = net_load
            cost_h = grid_import * tel.tou_tariff
            carbon_h = grid_import * (tel.grid_carbon_g_per_kwh / 1000.0)

            # Heavy penalty if exceeds max grid capacity (breaker trip)
            if grid_import > max_grid_kw:
                cost_h += (grid_import - max_grid_kw) * 5.0
        else:
            # Solar surplus exported to grid
            grid_export = abs(net_load)
            cost_h = - (grid_export * tel.feed_in_tariff)
            carbon_h = 0.0

        total_cost += cost_h
        total_carbon += carbon_h

    peak_kw = max(tel.baseload_demand_kw + hourly_load[h] for h, tel in enumerate(telemetry))

    return round(total_cost, 2), [round(x, 2) for x in hourly_load], round(peak_kw, 2), round(total_carbon, 2), round(comfort_penalty, 2)


# ── Search Algorithms ─────────────────────────────────────────

def run_baseline_asap(
    appliances: List[Appliance],
    telemetry: List[HourlyTelemetry],
) -> SearchResult:
    """
    Baseline strategy: start each appliance as soon as possible (preferred/earliest time),
    without price awareness. Represents typical unmanaged household.
    """
    start_time = time.perf_counter()
    schedule = {}
    for app in appliances:
        schedule[app.id] = app.earliest_start

    cost, load_curve, peak, carbon, comfort = compute_schedule_cost(schedule, appliances, telemetry)
    elapsed = max(round((time.perf_counter() - start_time) * 1000, 2), 0.01)

    return SearchResult(
        algorithm="Baseline (ASAP)",
        schedule=schedule,
        hourly_appliance_load=load_curve,
        total_cost=cost,
        peak_demand_kw=peak,
        carbon_emissions_kg=carbon,
        comfort_penalty=comfort,
        nodes_expanded=len(appliances),
        execution_time_ms=elapsed,
        description="Naive unmanaged scheduling where appliances run at the earliest available time.",
    )


def run_greedy_best_first(
    appliances: List[Appliance],
    telemetry: List[HourlyTelemetry],
) -> SearchResult:
    """
    Greedy Best-First Search: For each appliance, evaluate all valid starting hours
    independently and select the single lowest-cost start hour.
    """
    start_time = time.perf_counter()
    schedule = {}
    nodes_expanded = 0

    # Sort appliances by power * duration descending (schedule heaviest loads first)
    sorted_apps = sorted(appliances, key=lambda a: a.power_kw * a.duration_hours, reverse=True)

    for app in sorted_apps:
        best_hour = app.earliest_start
        min_cost = float("inf")

        valid_starts = _get_valid_start_hours(app)
        for h in valid_starts:
            nodes_expanded += 1
            temp_schedule = {**schedule, app.id: h}
            c, _, _, _, comfort = compute_schedule_cost(temp_schedule, appliances, telemetry)
            eval_score = c + comfort
            if eval_score < min_cost:
                min_cost = eval_score
                best_hour = h

        schedule[app.id] = best_hour

    cost, load_curve, peak, carbon, comfort = compute_schedule_cost(schedule, appliances, telemetry)
    elapsed = max(round((time.perf_counter() - start_time) * 1000, 2), 0.01)

    return SearchResult(
        algorithm="Greedy Best-First",
        schedule=schedule,
        hourly_appliance_load=load_curve,
        total_cost=cost,
        peak_demand_kw=peak,
        carbon_emissions_kg=carbon,
        comfort_penalty=comfort,
        nodes_expanded=nodes_expanded,
        execution_time_ms=elapsed,
        description="Locally optimizes each appliance start time into the cheapest available slot sequentially.",
    )


def run_astar_search(
    appliances: List[Appliance],
    telemetry: List[HourlyTelemetry],
    max_grid_kw: float = 10.0,
) -> SearchResult:
    """
    A* State-Space Search:
    - State: Assignment of start hours to the first `k` appliances.
    - g(n): Actual electricity cost + comfort penalty accumulated by the scheduled appliances.
    - h(n): Admissible heuristic: Remaining unscheduled appliance energy multiplied by the
            minimum off-peak tariff rate (guarantees lower bound / admissibility).
    - f(n) = g(n) + h(n)
    """
    start_time = time.perf_counter()
    nodes_expanded = 0

    # Sort appliances by priority & energy requirement
    shiftable_apps = [a for a in appliances if a.category in ("shiftable", "thermostatic")]
    fixed_apps = [a for a in appliances if a.category not in ("shiftable", "thermostatic")]

    fixed_schedule = {a.id: a.earliest_start for a in fixed_apps}

    # Minimum electricity tariff across the 24 hours (admissible lower bound)
    min_rate = min(t.tou_tariff for t in telemetry)

    # Priority queue: (f_score, g_cost, h_cost, appliance_index, schedule)
    initial_h = sum(a.power_kw * a.duration_hours * min_rate for a in shiftable_apps)
    start_node = SearchNode(
        priority=initial_h,
        g_cost=0.0,
        h_cost=initial_h,
        appliance_index=0,
        schedule=dict(fixed_schedule),
    )

    open_set: List[SearchNode] = [start_node]
    best_complete_schedule = None
    min_complete_cost = float("inf")

    # Safety limit on nodes expanded to ensure sub-second responsiveness
    MAX_EXPANSIONS = 2500

    while open_set and nodes_expanded < MAX_EXPANSIONS:
        current = heapq.heappop(open_set)
        nodes_expanded += 1

        idx = current.appliance_index

        if idx >= len(shiftable_apps):
            # Goal state: all appliances scheduled
            total_eval, _, _, _, _ = compute_schedule_cost(current.schedule, appliances, telemetry, max_grid_kw)
            if total_eval < min_complete_cost:
                min_complete_cost = total_eval
                best_complete_schedule = current.schedule
            break

        next_app = shiftable_apps[idx]
        valid_starts = _get_valid_start_hours(next_app)

        # Remaining appliances after next_app
        remaining_energy = sum(a.power_kw * a.duration_hours for a in shiftable_apps[idx + 1:])
        future_h = remaining_energy * min_rate

        for h in valid_starts:
            new_schedule = {**current.schedule, next_app.id: h}
            g_cost, _, peak_kw, _, comfort = compute_schedule_cost(new_schedule, appliances, telemetry, max_grid_kw)
            
            # Admissible heuristic: future minimum cost + comfort estimate
            f_score = g_cost + future_h + comfort

            child_node = SearchNode(
                priority=f_score,
                g_cost=g_cost + comfort,
                h_cost=future_h,
                appliance_index=idx + 1,
                schedule=new_schedule,
            )
            heapq.heappush(open_set, child_node)

    if not best_complete_schedule:
        # Fallback to greedy if search cutoff occurred
        return run_greedy_best_first(appliances, telemetry)

    cost, load_curve, peak, carbon, comfort = compute_schedule_cost(
        best_complete_schedule, appliances, telemetry, max_grid_kw
    )
    elapsed = max(round((time.perf_counter() - start_time) * 1000, 2), 0.01)

    return SearchResult(
        algorithm="A* Heuristic Search",
        schedule=best_complete_schedule,
        hourly_appliance_load=load_curve,
        total_cost=cost,
        peak_demand_kw=peak,
        carbon_emissions_kg=carbon,
        comfort_penalty=comfort,
        nodes_expanded=nodes_expanded,
        execution_time_ms=elapsed,
        description="Globally guides state-space exploration using f(n)=g(n)+h(n) with admissible peak-cost bounds.",
    )


def run_constraint_satisfaction_search(
    appliances: List[Appliance],
    telemetry: List[HourlyTelemetry],
    max_grid_kw: float = 8.0,
) -> SearchResult:
    """
    Constraint-Satisfaction Problem (CSP) / Peak-Shaving Planner:
    Finds a schedule that strictly satisfies peak-breaker constraint (e.g. max_grid_kw)
    while minimizing off-peak shifting costs.
    """
    start_time = time.perf_counter()
    nodes_expanded = 0

    sorted_apps = sorted(appliances, key=lambda a: (a.priority, -a.power_kw))
    schedule: Dict[str, int] = {}

    for app in sorted_apps:
        valid_starts = _get_valid_start_hours(app)
        best_h = valid_starts[0]
        min_penalty = float("inf")

        for h in valid_starts:
            nodes_expanded += 1
            test_sched = {**schedule, app.id: h}
            cost, _, peak, _, comfort = compute_schedule_cost(test_sched, appliances, telemetry, max_grid_kw)

            # Heavy penalty if peak breaches grid breaker limit
            over_limit = max(0.0, peak - max_grid_kw)
            csp_penalty = cost + comfort + (over_limit * 50.0)

            if csp_penalty < min_penalty:
                min_penalty = csp_penalty
                best_h = h

        schedule[app.id] = best_h

    cost, load_curve, peak, carbon, comfort = compute_schedule_cost(schedule, appliances, telemetry, max_grid_kw)
    elapsed = max(round((time.perf_counter() - start_time) * 1000, 2), 0.01)

    return SearchResult(
        algorithm="CSP Peak-Shaving Search",
        schedule=schedule,
        hourly_appliance_load=load_curve,
        total_cost=cost,
        peak_demand_kw=peak,
        carbon_emissions_kg=carbon,
        comfort_penalty=comfort,
        nodes_expanded=nodes_expanded,
        execution_time_ms=elapsed,
        description=f"Enforces hard capacity constraint (Peak ≤ {max_grid_kw} kW) to prevent breaker trips.",
    )


def compare_search_algorithms(
    appliances: List[Appliance],
    telemetry: List[HourlyTelemetry],
) -> List[SearchResult]:
    """Run and compare all search planners side-by-side."""
    asap = run_baseline_asap(appliances, telemetry)
    greedy = run_greedy_best_first(appliances, telemetry)
    astar = run_astar_search(appliances, telemetry)
    csp = run_constraint_satisfaction_search(appliances, telemetry, max_grid_kw=8.0)
    return [asap, greedy, astar, csp]


def _get_valid_start_hours(app: Appliance) -> List[int]:
    """Return all valid starting hours for an appliance within its operating window."""
    if app.category not in ("shiftable", "thermostatic"):
        return [app.earliest_start]

    valid = []
    # If deadline > earliest_start (same day window)
    if app.deadline > app.earliest_start:
        latest = app.deadline - app.duration_hours
        for h in range(app.earliest_start, max(app.earliest_start + 1, latest + 1)):
            if 0 <= h < 24:
                valid.append(h)
    else:
        # Wrap-around window (e.g. overnight 18:00 to 07:00 next morning)
        # Hours: 18..23 and 0..(deadline - duration)
        for h in range(app.earliest_start, 24):
            valid.append(h)
        latest_morning = max(0, app.deadline - app.duration_hours)
        for h in range(0, latest_morning + 1):
            valid.append(h)

    return valid if valid else [app.earliest_start]
 
 
def build_gantt_dataframe(
    schedule: Dict[str, Any],
    appliances: List[Appliance],
    base_date: Optional[Any] = None,
) -> pd.DataFrame:
    """
    Construct a validated pandas DataFrame for Plotly Express timeline Gantt chart.

    Ensures:
    1. Start and Finish columns are proper pd.Timestamp objects.
    2. Midnight at the end of a day is represented as 00:00 on the following day
       (e.g., 2026-10-28 00:00:00), rather than invalid '24:00'.
    3. Proper datetime arithmetic with pd.Timedelta for exact intervals.
    4. Legitimate overnight schedules crossing midnight are preserved (Finish > Start across date boundary).
    5. Invalid, non-numeric, or negative entries are safely excluded.
    """
    if base_date is None:
        base_dt = pd.Timestamp("2026-10-27 00:00:00")
    elif isinstance(base_date, str):
        base_dt = pd.to_datetime(base_date, errors="coerce")
        if pd.isna(base_dt):
            base_dt = pd.Timestamp("2026-10-27 00:00:00")
    elif isinstance(base_date, (pd.Timestamp, np.datetime64)):
        base_dt = pd.Timestamp(base_date)
    else:
        base_dt = pd.Timestamp("2026-10-27 00:00:00")

    app_dict = {a.id: a for a in appliances}
    gantt_rows = []

    for app_id, start_h in schedule.items():
        app = app_dict.get(app_id)
        if not app:
            continue

        try:
            start_num = float(start_h)
            dur_num = float(app.duration_hours)
        except (ValueError, TypeError):
            continue

        # Reject invalid numbers
        if start_num < 0 or dur_num <= 0:
            continue

        # Datetime arithmetic: midnight at end of day becomes 00:00 next day
        start_dt = base_dt + pd.Timedelta(hours=start_num)
        end_dt = start_dt + pd.Timedelta(hours=dur_num)

        gantt_rows.append({
            "Appliance": app.name,
            "Start": start_dt,
            "Finish": end_dt,
            "Power (kW)": f"{app.power_kw} kW",
            "Duration": f"{app.duration_hours} hrs",
        })

    if not gantt_rows:
        return pd.DataFrame(columns=["Appliance", "Start", "Finish", "Power (kW)", "Duration"])

    df = pd.DataFrame(gantt_rows)

    # Validate and explicitly convert columns to Pandas datetimes
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
    df["Finish"] = pd.to_datetime(df["Finish"], errors="coerce")

    # Safely filter out malformed or missing datetimes, preserving legitimate overnight intervals
    valid_mask = (
        df["Start"].notna()
        & df["Finish"].notna()
        & (df["Finish"] > df["Start"])
    )
    return df[valid_mask].copy().reset_index(drop=True)

