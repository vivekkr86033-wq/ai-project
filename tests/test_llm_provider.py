"""
test_llm_provider.py — Unit tests for the LLM provider and fallback.
"""

import pytest
from src.llm_provider import generate_answer, compute_confidence, _extractive_answer


class TestExtractiveFallback:
    """Tests for the deterministic extractive fallback."""

    def test_fallback_with_chunks(self):
        chunks = [
            {
                "doc_name": "test.txt",
                "page_or_section": "1",
                "text": "Python is a programming language used for web development.",
                "similarity": 0.85,
            },
            {
                "doc_name": "test.txt",
                "page_or_section": "2",
                "text": "Variables store data values in Python.",
                "similarity": 0.72,
            },
        ]
        result = _extractive_answer("What is Python?", chunks)
        assert result["mode"] == "fallback_extractive"
        assert result["model"] == "none"
        assert "Python" in result["answer"]
        assert "test.txt" in result["answer"]

    def test_fallback_without_chunks(self):
        result = _extractive_answer("Random question?", [])
        assert result["mode"] == "fallback_extractive"
        assert "could not find" in result["answer"].lower()

    def test_fallback_mentions_extractive_mode(self):
        chunks = [
            {"doc_name": "doc.md", "text": "Sample text.", "similarity": 0.5, "page_or_section": "1"},
        ]
        result = _extractive_answer("Test?", chunks)
        assert "extractive fallback" in result["answer"].lower() or "fallback" in result["answer"].lower()

    def test_fallback_does_not_claim_llm(self):
        chunks = [
            {"doc_name": "doc.md", "text": "Sample text.", "similarity": 0.5, "page_or_section": "1"},
        ]
        result = _extractive_answer("Test?", chunks)
        # Should not falsely claim AI generation
        assert result["model"] == "none"


class TestGenerateAnswer:
    """Tests for the generate_answer function."""

    def test_force_fallback(self):
        result = generate_answer("Test?", [], force_fallback=True)
        assert result["mode"] == "fallback_extractive"

    def test_default_no_llm_uses_fallback(self):
        # With no API key configured, should use fallback
        result = generate_answer("What is AI?", [])
        assert result["mode"] == "fallback_extractive"


class TestConfidenceComputation:
    """Tests for retrieval confidence computation."""

    def test_no_chunks(self):
        conf = compute_confidence([])
        assert conf["score"] == 0.0
        assert conf["label"] == "No Evidence"

    def test_high_similarity_chunks(self):
        chunks = [
            {"similarity": 0.95},
            {"similarity": 0.90},
            {"similarity": 0.85},
        ]
        conf = compute_confidence(chunks)
        assert conf["score"] > 0.7
        assert conf["label"] == "Strong Evidence"

    def test_low_similarity_chunks(self):
        chunks = [
            {"similarity": 0.15},
            {"similarity": 0.10},
        ]
        conf = compute_confidence(chunks)
        assert conf["score"] < 0.45

    def test_confidence_has_required_fields(self):
        conf = compute_confidence([{"similarity": 0.5}])
        assert "score" in conf
        assert "label" in conf
        assert "explanation" in conf

    def test_confidence_score_bounded(self):
        chunks = [{"similarity": 0.5}]
        conf = compute_confidence(chunks)
        assert 0.0 <= conf["score"] <= 1.0
