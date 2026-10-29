"""
test_smart_home.py — Comprehensive unit test suite for AI-Based Smart Home Energy Management.
"""

import pytest
from unittest.mock import MagicMock, patch

import pandas as pd
import plotly.express as px

from src.energy_models import (
    Appliance,
    BatteryStorage,
    get_default_appliances,
    get_simulation_profile,
)
from src.appliance_search import (
    run_baseline_asap,
    run_greedy_best_first,
    run_astar_search,
    run_constraint_satisfaction_search,
    compare_search_algorithms,
    build_gantt_dataframe,
)

from src.rule_engine import EnergyRuleEngine, BUILTIN_RULES
from src.multi_agent import run_multi_agent_simulation
from src.energy_paradigms import (
    ENERGY_AI_PARADIGMS,
    RECOMMENDED_TASKS,
    get_paradigm_by_id,
    get_recommendation_for_task,
)
from src.energy_assistant import generate_energy_explanation


class TestEnergyModels:
    def test_default_appliances_exist(self):
        apps = get_default_appliances()
        assert len(apps) >= 5
        assert any(a.id == "ev_charger" for a in apps)
        assert any(a.id == "dishwasher" for a in apps)

    def test_battery_storage_charge_discharge(self):
        bat = BatteryStorage(capacity_kwh=10.0, current_soc=0.50, min_soc=0.20)
        # Charge
        actual_power, new_soc = bat.step(3.0)
        assert new_soc > 0.50
        assert actual_power > 0

        # Discharge
        actual_draw, discharged_soc = bat.step(-4.0)
        assert discharged_soc < new_soc
        assert actual_draw < 0

    def test_battery_respects_minimum_reserve(self):
        bat = BatteryStorage(capacity_kwh=10.0, current_soc=0.22, min_soc=0.20)
        # Attempt massive discharge
        actual_draw, final_soc = bat.step(-8.0)
        assert final_soc >= 0.20

    def test_simulation_profiles(self):
        summer = get_simulation_profile("summer_peak")
        winter = get_simulation_profile("winter_heating")
        assert len(summer) == 24
        assert len(winter) == 24
        assert max(t.solar_generation_kw for t in summer) > max(t.solar_generation_kw for t in winter)


class TestApplianceSearchAlgorithms:
    @pytest.fixture
    def setup_data(self):
        apps = get_default_appliances()
        profile = get_simulation_profile("summer_peak")
        return apps, profile

    def test_baseline_asap(self, setup_data):
        apps, profile = setup_data
        res = run_baseline_asap(apps, profile)
        assert res.total_cost > 0
        assert res.peak_demand_kw > 0
        assert len(res.hourly_appliance_load) == 24
        assert "ev_charger" in res.schedule

    def test_greedy_best_first(self, setup_data):
        apps, profile = setup_data
        baseline = run_baseline_asap(apps, profile)
        greedy = run_greedy_best_first(apps, profile)
        assert greedy.nodes_expanded > 0
        assert greedy.total_cost <= baseline.total_cost

    def test_astar_search_optimality(self, setup_data):
        apps, profile = setup_data
        baseline = run_baseline_asap(apps, profile)
        astar = run_astar_search(apps, profile)
        assert astar.nodes_expanded > 0
        assert astar.total_cost <= baseline.total_cost
        assert astar.execution_time_ms > 0

    def test_constraint_satisfaction_search(self, setup_data):
        apps, profile = setup_data
        csp = run_constraint_satisfaction_search(apps, profile, max_grid_kw=8.0)
        assert csp.peak_demand_kw <= 8.5  # Allows minor baseload boundary tolerance

    def test_compare_search_algorithms(self, setup_data):
        apps, profile = setup_data
        results = compare_search_algorithms(apps, profile)
        assert len(results) == 4
        assert any(r.algorithm == "A* Heuristic Search" for r in results)

    def test_gantt_dataframe_midnight_representation(self, setup_data):
        """Verify midnight at end of day is represented as 00:00 on the following day, not 24:00."""
        apps, _ = setup_data
        # Dishwasher: duration_hours=2, scheduled at hour 22 -> finishes at midnight
        schedule = {"dishwasher": 22}
        base_date = pd.Timestamp("2026-10-27 00:00:00")
        df = build_gantt_dataframe(schedule, apps, base_date=base_date)

        assert len(df) == 1
        row = df.iloc[0]
        # Start should be 2026-10-27 22:00:00
        assert row["Start"] == pd.Timestamp("2026-10-27 22:00:00")
        # Finish must be 2026-10-28 00:00:00 (hour 0 of next day, never 24:00)
        assert row["Finish"] == pd.Timestamp("2026-10-28 00:00:00")
        assert row["Finish"].hour == 0
        assert row["Finish"].day == 28
        assert row["Finish"] > row["Start"]

    def test_gantt_dataframe_overnight_interval_preserved(self, setup_data):
        """Verify overnight schedules crossing midnight are preserved with valid datetimes."""
        apps, _ = setup_data
        # EV charger: duration_hours=4, scheduled at 23:00 -> finishes at 03:00 on day 2
        schedule = {"ev_charger": 23}
        base_date = pd.Timestamp("2026-10-27 00:00:00")
        df = build_gantt_dataframe(schedule, apps, base_date=base_date)

        assert len(df) == 1
        row = df.iloc[0]
        assert row["Start"] == pd.Timestamp("2026-10-27 23:00:00")
        assert row["Finish"] == pd.Timestamp("2026-10-28 03:00:00")
        assert row["Finish"] > row["Start"]

    def test_gantt_dataframe_malformed_and_missing_values(self, setup_data):
        """Verify non-numeric or negative start hours or durations are safely discarded."""
        apps, _ = setup_data
        malformed_schedule = {
            "dishwasher": "invalid",
            "ev_charger": -5,
            "non_existent_appliance": 10,
            "water_heater": 6,  # valid: duration 3h -> finishes at 9:00
        }
        df = build_gantt_dataframe(malformed_schedule, apps)
        assert len(df) == 1
        assert df.iloc[0]["Appliance"] == "Heat Pump Water Heater"

    def test_gantt_plotly_timeline_rendering(self, setup_data):
        """Verify plotly.express.timeline creates the Gantt chart without TypeError or DateParseError."""
        apps, profile = setup_data
        astar = run_astar_search(apps, profile)
        df = build_gantt_dataframe(astar.schedule, apps)
        assert not df.empty

        # This should execute cleanly without raising:
        # TypeError: Both x_start and x_end must refer to data convertible to datetimes
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Appliance",
            color="Appliance",
        )
        assert fig is not None
        assert len(fig.data) == len(df)



class TestSymbolicRuleEngine:
    def test_builtin_rules_structure(self):
        assert len(BUILTIN_RULES) >= 7
        assert any(r.id == "R01" for r in BUILTIN_RULES)
        assert any(r.id == "R04" for r in BUILTIN_RULES)

    def test_rule_peak_curtailment_fires(self):
        engine = EnergyRuleEngine()
        profile = get_simulation_profile("summer_peak")
        peak_hour_tel = next(t for t in profile if t.is_peak)
        apps = get_default_appliances()
        for a in apps:
            if a.priority >= 3:
                a.current_state = "ON"

        battery = BatteryStorage(current_soc=0.60)
        trace = engine.evaluate_hour(peak_hour_tel, battery, active_appliances=apps)
        assert "R01" in trace.matched_rules
        assert len(trace.fired_rules) > 0

    def test_rule_battery_reserve_protection_fires(self):
        engine = EnergyRuleEngine()
        profile = get_simulation_profile("summer_peak")
        battery = BatteryStorage(current_soc=0.19, min_soc=0.20)
        trace = engine.evaluate_hour(profile[18], battery)
        assert "R04" in trace.matched_rules
        assert any(act.rule_id == "R04" for act in trace.fired_rules)


class TestMultiAgentSystem:
    def test_multi_agent_24h_simulation(self):
        apps = get_default_appliances()
        profile = get_simulation_profile("summer_peak")
        schedule = {a.id: a.earliest_start for a in apps}

        steps = run_multi_agent_simulation(apps, profile, schedule, max_grid_kw=10.0)
        assert len(steps) == 24

        total_msgs = sum(len(s.messages) for s in steps)
        assert total_msgs > 10

        # Check coordinator arbitration works
        for s in steps:
            assert s.grid_import_kw <= 10.05
            assert s.battery_soc >= 0.19


class TestAIParadigms:
    def test_all_six_paradigms_present(self):
        assert len(ENERGY_AI_PARADIGMS) == 6
        ids = [p.id for p in ENERGY_AI_PARADIGMS]
        assert "classical_search" in ids
        assert "symbolic_rules" in ids
        assert "supervised_ml" in ids
        assert "reinforcement_learning" in ids
        assert "multi_agent_systems" in ids
        assert "generative_ai" in ids

    def test_task_recommender(self):
        assert len(RECOMMENDED_TASKS) >= 5
        rec = get_recommendation_for_task("T1")
        assert rec is not None
        assert rec["recommended_paradigm"] == "classical_search"


class TestExplainableEnergyAssistant:
    def test_deterministic_fallback_ev_query(self):
        apps = get_default_appliances()
        profile = get_simulation_profile("summer_peak")
        search_res = run_astar_search(apps, profile)
        base_res = run_baseline_asap(apps, profile)

        res = generate_energy_explanation(
            "Why was my EV charging delayed?",
            search_result=search_res,
            baseline_result=base_res,
            telemetry_profile=profile,
            force_fallback=True,
        )
        assert res["mode"] == "grounded_extractive"
        assert "EV" in res["answer"]
        assert len(res["citations"]) > 0

    def test_deterministic_fallback_savings_query(self):
        apps = get_default_appliances()
        profile = get_simulation_profile("summer_peak")
        search_res = run_astar_search(apps, profile)
        base_res = run_baseline_asap(apps, profile)

        res = generate_energy_explanation(
            "How much money did I save today?",
            search_result=search_res,
            baseline_result=base_res,
            telemetry_profile=profile,
            force_fallback=True,
        )
        assert "Savings" in res["answer"] or "saved" in res["answer"].lower()
        assert "cost_savings" in res["key_metrics"]

    def test_mocked_openai_call(self):
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Mocked explanation: EV charging was shifted to 2 AM to avoid peak rates."
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        with patch("src.config.llm_available", return_value=True), \
             patch("src.config.get_llm_provider", return_value="openai"), \
             patch("src.config.get_openai_api_key", return_value="sk-test-key-12345"), \
             patch("src.config.get_openai_model", return_value="gpt-3.5-turbo"), \
             patch("openai.OpenAI", return_value=mock_client):

            res = generate_energy_explanation(
                "Why was my EV charging delayed?",
                force_fallback=False,
            )
            assert res["mode"] == "llm"
            assert res["provider"] == "openai"
            assert "EV charging was shifted" in res["answer"]

    def test_mocked_gemini_call(self):
        mock_response = MagicMock()
        mock_response.text = "Gemini explanation: EV was scheduled for 2:00 AM off-peak."
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("src.config.llm_available", return_value=True), \
             patch("src.config.get_llm_provider", return_value="gemini"), \
             patch("src.config.get_gemini_api_key", return_value="AQ.test-key-1234567890"), \
             patch("src.config.get_gemini_model", return_value="gemini-3.8-flash"), \
             patch("google.genai.Client", return_value=mock_client):

            res = generate_energy_explanation(
                "Why was my EV charging delayed?",
                force_fallback=False,
            )
            assert res["mode"] == "llm"
            assert res["provider"] == "gemini"
            assert "EV was scheduled for 2:00 AM" in res["answer"]

    def test_gemini_fallback_on_api_error(self):
        with patch("src.config.llm_available", return_value=True), \
             patch("src.config.get_llm_provider", return_value="gemini"), \
             patch("src.config.get_gemini_api_key", return_value="AQ.test-key-1234567890"), \
             patch("google.genai.Client", side_effect=Exception("API Error")):

            res = generate_energy_explanation(
                "Why was my EV charging delayed?",
                force_fallback=False,
            )
            assert res["mode"] == "grounded_extractive"
            assert "Electric Vehicle" in res["answer"]
