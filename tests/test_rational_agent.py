"""
test_rational_agent.py — Unit tests for the rational agent.
"""

import pytest
from src.rational_agent import classify_intent, run_agent, INTENTS, ACTIONS


class TestIntentClassification:
    """Tests for intent classification."""

    def test_course_info_intent(self):
        intent, scores = classify_intent("What is the schedule for CS101?")
        assert intent == "course_info"

    def test_classroom_rules_intent(self):
        intent, scores = classify_intent("What is the attendance policy?")
        assert intent == "classroom_rules"

    def test_syllabus_help_intent(self):
        intent, scores = classify_intent("What topics are in the syllabus?")
        assert intent == "syllabus_help"

    def test_assignment_intent(self):
        intent, scores = classify_intent("When is the assignment due?")
        assert intent == "assignment_guidance"

    def test_general_intent(self):
        intent, scores = classify_intent("Hello, how are you?")
        assert intent == "general_question"

    def test_rules_keywords(self):
        intent, scores = classify_intent("Is plagiarism allowed?")
        assert intent == "classroom_rules"

    def test_learning_resources_intent(self):
        intent, scores = classify_intent("Can you find a document about neural networks?")
        assert intent == "learning_resources"

    def test_intent_returns_scores(self):
        intent, scores = classify_intent("What is the deadline?")
        assert isinstance(scores, dict)
        assert len(scores) > 0

    def test_all_intents_defined(self):
        assert "course_info" in INTENTS
        assert "classroom_rules" in INTENTS
        assert "syllabus_help" in INTENTS
        assert "assignment_guidance" in INTENTS
        assert "learning_resources" in INTENTS
        assert "general_question" in INTENTS


class TestAgentCycle:
    """Tests for the full agent cycle."""

    def test_agent_returns_trace(self):
        trace = run_agent("What is CS101?", force_fallback=True)
        assert trace.question == "What is CS101?"
        assert trace.classified_intent != ""
        assert trace.selected_action != ""
        assert trace.answer != ""

    def test_agent_trace_has_all_steps(self):
        trace = run_agent("When is the exam?", force_fallback=True)
        assert trace.observation != ""
        assert trace.classified_intent != ""
        assert trace.goal != ""
        assert len(trace.constraints) > 0
        assert trace.selected_action != ""
        assert trace.action_reason != ""
        assert trace.answer != ""
        assert trace.decision_explanation != ""

    def test_agent_course_lookup(self):
        trace = run_agent("What is the schedule for Introduction to Computer Science?", force_fallback=True)
        assert trace.classified_intent == "course_info"
        assert trace.selected_action in ("database_lookup", "combined_lookup")
        assert len(trace.sources) > 0

    def test_agent_rules_lookup(self):
        trace = run_agent("What is the late submission policy?", force_fallback=True)
        assert trace.classified_intent == "classroom_rules"
        assert len(trace.sources) > 0

    def test_agent_elapsed_time_recorded(self):
        trace = run_agent("Hello", force_fallback=True)
        assert trace.elapsed_ms > 0

    def test_agent_confidence_computed(self):
        trace = run_agent("What courses are available?", force_fallback=True)
        assert "score" in trace.confidence
        assert "label" in trace.confidence

    def test_agent_no_fabrication_in_fallback(self):
        """Verify fallback mode does not claim LLM was used."""
        trace = run_agent("Explain quantum computing", force_fallback=True)
        assert trace.answer_mode == "fallback_extractive"
        # Should not claim LLM usage
        assert "AI-generated" not in trace.answer or "fallback" in trace.answer.lower()

    def test_agent_to_dict(self):
        trace = run_agent("Test query", force_fallback=True)
        d = trace.to_dict()
        assert isinstance(d, dict)
        assert "question" in d
        assert "classified_intent" in d
        assert "answer" in d


class TestActionSelection:
    """Tests for action selection logic."""

    def test_all_actions_defined(self):
        assert "database_lookup" in ACTIONS
        assert "rag_retrieval" in ACTIONS
        assert "combined_lookup" in ACTIONS
        assert "general_explanation" in ACTIONS
