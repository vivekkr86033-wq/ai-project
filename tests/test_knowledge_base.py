"""
test_knowledge_base.py — Unit tests for the knowledge base module.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src import knowledge_base as kb


class TestKnowledgeBase:
    """Tests for course and rules data operations."""

    def test_load_courses_returns_list(self):
        courses = kb.load_courses()
        assert isinstance(courses, list)
        assert len(courses) > 0

    def test_courses_have_required_fields(self):
        courses = kb.load_courses()
        for c in courses:
            assert "id" in c
            assert "name" in c
            assert "description" in c
            assert "syllabus" in c
            assert isinstance(c["syllabus"], list)

    def test_load_rules_returns_list(self):
        rules = kb.load_rules()
        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_rules_have_required_fields(self):
        rules = kb.load_rules()
        for r in rules:
            assert "id" in r
            assert "rule" in r

    def test_get_course_by_id_found(self):
        course = kb.get_course_by_id("CS101")
        assert course is not None
        assert course["id"] == "CS101"
        assert "Computer Science" in course["name"]

    def test_get_course_by_id_not_found(self):
        course = kb.get_course_by_id("NONEXISTENT999")
        assert course is None

    def test_search_courses_finds_results(self):
        results = kb.search_courses("Computer Science")
        assert len(results) > 0
        assert any("CS101" == c["id"] for c in results)

    def test_search_courses_case_insensitive(self):
        results = kb.search_courses("computer science")
        assert len(results) > 0

    def test_search_courses_no_results(self):
        results = kb.search_courses("xyznonexistenttopic123")
        assert len(results) == 0

    def test_search_rules_finds_results(self):
        results = kb.search_rules("attendance")
        assert len(results) > 0
        assert any("attendance" in r["rule"].lower() for r in results)

    def test_search_rules_no_results(self):
        results = kb.search_rules("xyznonexistentrule123")
        assert len(results) == 0

    def test_get_all_structured_text(self):
        text = kb.get_all_structured_text()
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Course:" in text
        assert "Classroom Rules:" in text

    def test_courses_have_assignments(self):
        courses = kb.load_courses()
        for c in courses:
            assert "assignments" in c
            for a in c["assignments"]:
                assert "title" in a
                assert "deadline" in a


class TestSearchFunctionality:
    """Tests for search across courses and rules."""

    def test_search_by_instructor(self):
        results = kb.search_courses("Alice Martin")
        assert len(results) > 0

    def test_search_by_schedule(self):
        results = kb.search_courses("Room 201")
        assert len(results) > 0

    def test_search_assignment(self):
        results = kb.search_courses("Python Basics")
        assert len(results) > 0

    def test_search_syllabus_topic(self):
        results = kb.search_courses("Neural Networks")
        assert len(results) > 0
