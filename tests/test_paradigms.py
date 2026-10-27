"""
test_paradigms.py — Unit tests for AI paradigms module.
"""

import pytest
from src.paradigms import (
    get_all_paradigms,
    get_paradigm,
    get_comparison_table,
    get_task_recommendations,
    recommend_for_task,
    PARADIGMS,
    TASK_RECOMMENDATIONS,
)


class TestParadigmData:
    """Tests for paradigm data completeness."""

    def test_all_six_paradigms_present(self):
        paradigms = get_all_paradigms()
        assert len(paradigms) == 6
        assert "symbolic_rule_based" in paradigms
        assert "classical_ml" in paradigms
        assert "deep_learning" in paradigms
        assert "generative_ai_llm" in paradigms
        assert "rag" in paradigms
        assert "agentic_ai" in paradigms

    def test_paradigm_has_required_fields(self):
        for pid, p in PARADIGMS.items():
            assert "name" in p, f"{pid} missing name"
            assert "operating_principle" in p, f"{pid} missing operating_principle"
            assert "strengths" in p, f"{pid} missing strengths"
            assert "limitations" in p, f"{pid} missing limitations"
            assert "classroom_applications" in p, f"{pid} missing classroom_applications"
            assert "computational_cost" in p, f"{pid} missing computational_cost"
            assert "recommendation" in p, f"{pid} missing recommendation"

    def test_paradigm_fields_non_empty(self):
        for pid, p in PARADIGMS.items():
            assert len(p["strengths"]) > 0, f"{pid} has empty strengths"
            assert len(p["limitations"]) > 0, f"{pid} has empty limitations"
            assert len(p["classroom_applications"]) > 0, f"{pid} has empty applications"

    def test_get_paradigm_by_id(self):
        p = get_paradigm("rag")
        assert p is not None
        assert "RAG" in p["name"]

    def test_get_paradigm_not_found(self):
        p = get_paradigm("nonexistent")
        assert p is None


class TestComparisonTable:
    """Tests for comparison table generation."""

    def test_comparison_table_format(self):
        table = get_comparison_table()
        assert len(table) == 6
        for row in table:
            assert "id" in row
            assert "name" in row
            assert "cost" in row


class TestTaskRecommender:
    """Tests for task-based paradigm recommendations."""

    def test_all_tasks_have_recommendations(self):
        tasks = get_task_recommendations()
        assert len(tasks) >= 5
        for tid, t in tasks.items():
            assert "task" in t
            assert "recommended_paradigm" in t
            assert "reasoning" in t

    def test_recommend_rule_enforcement(self):
        result = recommend_for_task("enforce_rule")
        assert result is not None
        assert result["recommended_paradigm"] == "symbolic_rule_based"

    def test_recommend_performance_prediction(self):
        result = recommend_for_task("predict_performance")
        assert result is not None
        assert result["recommended_paradigm"] == "classical_ml"

    def test_recommend_concept_explanation(self):
        result = recommend_for_task("explain_concept")
        assert result is not None
        assert result["recommended_paradigm"] == "rag"

    def test_recommend_nonexistent_task(self):
        result = recommend_for_task("nonexistent_task")
        assert result is None

    def test_recommendations_reference_valid_paradigms(self):
        tasks = get_task_recommendations()
        for tid, t in tasks.items():
            assert t["recommended_paradigm"] in PARADIGMS, \
                f"Task {tid} recommends unknown paradigm {t['recommended_paradigm']}"
