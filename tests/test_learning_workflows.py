"""
test_learning_workflows.py — Unit tests for learning workflows.
"""

import pytest
from src.learning_workflows import (
    explain_topic,
    generate_quiz,
    create_revision_plan,
    find_relevant_documents,
    explain_assignment,
    refer_to_teacher,
)


class TestTopicExplanation:
    """Tests for the topic explanation workflow."""

    def test_explain_beginner(self):
        result = explain_topic("Sorting Algorithms", level="beginner")
        assert result["workflow"] == "topic_explanation"
        assert result["level"] == "beginner"
        assert len(result["explanation"]) > 0

    def test_explain_advanced(self):
        result = explain_topic("Neural Networks", level="advanced")
        assert result["level"] == "advanced"

    def test_explain_with_course_filter(self):
        result = explain_topic("Python", course_id="CS101")
        assert result["workflow"] == "topic_explanation"

    def test_explain_nonexistent_topic(self):
        result = explain_topic("Quantum Teleportation")
        assert "not found" in result["explanation"].lower() or len(result["syllabus_match"]) == 0


class TestQuizGeneration:
    """Tests for quiz generation workflow."""

    def test_generate_quiz(self):
        result = generate_quiz("Data Structures", num_questions=3)
        assert result["workflow"] == "practice_quiz"
        assert len(result["questions"]) > 0

    def test_quiz_question_format(self):
        result = generate_quiz("Python", num_questions=5)
        for q in result["questions"]:
            assert "number" in q
            assert "type" in q
            assert "question" in q

    def test_quiz_with_course(self):
        result = generate_quiz("Search Algorithms", course_id="AI201")
        assert result["workflow"] == "practice_quiz"


class TestRevisionPlan:
    """Tests for revision plan workflow."""

    def test_create_plan(self):
        result = create_revision_plan(course_id="CS101", exam_date="2026-12-15")
        assert result["workflow"] == "revision_plan"
        assert "plan" in result
        assert len(result["plan"]) > 0

    def test_plan_has_dates(self):
        result = create_revision_plan(course_id="AI201")
        if "plan" in result:
            for day in result["plan"]:
                assert "date" in day
                assert "topics" in day

    def test_plan_has_tips(self):
        result = create_revision_plan(course_id="CS101")
        assert "tips" in result
        assert len(result["tips"]) > 0


class TestAssignmentHelp:
    """Tests for assignment help workflow."""

    def test_explain_all_assignments(self):
        result = explain_assignment("CS101")
        assert result["workflow"] == "assignment_help"
        assert "assignments" in result
        assert len(result["assignments"]) > 0

    def test_explain_specific_assignment(self):
        result = explain_assignment("CS101", "Python Basics")
        assert len(result["assignments"]) > 0

    def test_no_submit_claim(self):
        result = explain_assignment("CS101")
        note = result.get("note", "")
        assert "cannot submit" in note.lower() or "cannot submit" in str(result).lower()

    def test_nonexistent_course(self):
        result = explain_assignment("FAKE999")
        assert "error" in result


class TestReferToTeacher:
    """Tests for teacher referral workflow."""

    def test_referral_message(self):
        result = refer_to_teacher("Can I get an extension?")
        assert result["workflow"] == "refer_to_teacher"
        assert "instructors" in result
        assert len(result["instructors"]) > 0

    def test_referral_has_suggestions(self):
        result = refer_to_teacher("Change my grade please")
        assert "suggestions" in result
        assert len(result["suggestions"]) > 0
