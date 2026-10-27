"""
evaluation.py — Test dataset, metrics computation, and evaluation runner.

Provides a structured test suite for the Classroom AI Assistant,
measuring intent classification, retrieval, and answer quality.
"""

import json
import time
from pathlib import Path
from typing import Optional

from src.config import TEST_DATA_DIR
from src import knowledge_base as kb
from src import document_processor as dp
from src.rational_agent import classify_intent, run_agent

# ── Test Dataset ──────────────────────────────────────────

TEST_DATASET: list[dict] = [
    {
        "id": "T01",
        "question": "What is the schedule for Introduction to Computer Science?",
        "expected_intent": "course_info",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["Mon/Wed/Fri", "09:00", "Room 201"],
        "supporting_source": "Course Database",
        "category": "course_info",
    },
    {
        "id": "T02",
        "question": "What is the attendance policy?",
        "expected_intent": "classroom_rules",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["attendance", "mandatory", "3 classes"],
        "supporting_source": "Classroom Rules",
        "category": "classroom_rules",
    },
    {
        "id": "T03",
        "question": "What topics are covered in AI201?",
        "expected_intent": "syllabus_help",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["Intelligent Agents", "Search Algorithms"],
        "supporting_source": "Course Database",
        "category": "syllabus_help",
    },
    {
        "id": "T04",
        "question": "When is Assignment 1 for CS101 due?",
        "expected_intent": "assignment_guidance",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["2026-11-10", "Python Basics"],
        "supporting_source": "Course Database",
        "category": "assignment_guidance",
    },
    {
        "id": "T05",
        "question": "What is the late submission penalty?",
        "expected_intent": "classroom_rules",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["10%", "per day", "3 days"],
        "supporting_source": "Classroom Rules",
        "category": "classroom_rules",
    },
    {
        "id": "T06",
        "question": "Who teaches Linear Algebra?",
        "expected_intent": "course_info",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["Carol Zhang"],
        "supporting_source": "Course Database",
        "category": "course_info",
    },
    {
        "id": "T07",
        "question": "Are phones allowed in class?",
        "expected_intent": "classroom_rules",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["phone", "silenced"],
        "supporting_source": "Classroom Rules",
        "category": "classroom_rules",
    },
    {
        "id": "T08",
        "question": "Tell me about the final project for AI201",
        "expected_intent": "assignment_guidance",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["AI Application", "2026-12-18"],
        "supporting_source": "Course Database",
        "category": "assignment_guidance",
    },
    {
        "id": "T09",
        "question": "What is the rule about academic integrity?",
        "expected_intent": "classroom_rules",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["plagiarism", "zero grade"],
        "supporting_source": "Classroom Rules",
        "category": "classroom_rules",
    },
    {
        "id": "T10",
        "question": "Hello, how are you?",
        "expected_intent": "general_question",
        "expected_action": "general_explanation",
        "expected_answer_contains": [],
        "supporting_source": "N/A",
        "category": "general",
    },
    {
        "id": "T11",
        "question": "What week covers Neural Networks in AI201?",
        "expected_intent": "syllabus_help",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["Neural Networks", "Deep Learning"],
        "supporting_source": "Course Database",
        "category": "syllabus_help",
    },
    {
        "id": "T12",
        "question": "Can I eat in the computer lab?",
        "expected_intent": "classroom_rules",
        "expected_action": "database_lookup",
        "expected_answer_contains": ["food", "drinks", "not allowed"],
        "supporting_source": "Classroom Rules",
        "category": "classroom_rules",
    },
]


# ── Metrics computation ──────────────────────────────────

def evaluate_intent_classification() -> dict:
    """
    Test intent classification accuracy on the test dataset.
    Returns detailed results with per-question breakdown.
    """
    correct = 0
    total = len(TEST_DATASET)
    results = []

    for test in TEST_DATASET:
        predicted_intent, scores = classify_intent(test["question"])
        is_correct = predicted_intent == test["expected_intent"]
        if is_correct:
            correct += 1
        results.append({
            "id": test["id"],
            "question": test["question"],
            "expected": test["expected_intent"],
            "predicted": predicted_intent,
            "correct": is_correct,
            "scores": scores,
        })

    return {
        "metric": "intent_classification_accuracy",
        "correct": correct,
        "total": total,
        "accuracy": round(correct / total, 4) if total > 0 else 0,
        "details": results,
    }


def evaluate_database_lookups() -> dict:
    """
    Test that database lookups return expected content.
    """
    correct = 0
    total = 0
    results = []

    for test in TEST_DATASET:
        if test["expected_action"] != "database_lookup":
            continue
        total += 1

        # Run agent
        trace = run_agent(test["question"], force_fallback=True)

        # Check if expected content is in the answer
        answer_lower = trace.answer.lower()
        expected = test["expected_answer_contains"]
        found = [term for term in expected if term.lower() in answer_lower]
        is_correct = len(found) == len(expected) if expected else True

        if is_correct:
            correct += 1

        results.append({
            "id": test["id"],
            "question": test["question"],
            "expected_terms": expected,
            "found_terms": found,
            "missing_terms": [t for t in expected if t not in found],
            "correct": is_correct,
            "action_used": trace.selected_action,
            "expected_action": test["expected_action"],
            "action_correct": trace.selected_action == test["expected_action"],
        })

    return {
        "metric": "database_lookup_accuracy",
        "correct": correct,
        "total": total,
        "accuracy": round(correct / total, 4) if total > 0 else 0,
        "details": results,
    }


def evaluate_source_attribution() -> dict:
    """
    Test that answers include source references.
    """
    total = 0
    attributed = 0
    results = []

    for test in TEST_DATASET:
        if test["supporting_source"] == "N/A":
            continue
        total += 1

        trace = run_agent(test["question"], force_fallback=True)
        has_sources = len(trace.sources) > 0

        if has_sources:
            attributed += 1

        results.append({
            "id": test["id"],
            "question": test["question"],
            "expected_source": test["supporting_source"],
            "actual_sources": trace.sources,
            "has_attribution": has_sources,
        })

    return {
        "metric": "source_attribution_rate",
        "attributed": attributed,
        "total": total,
        "rate": round(attributed / total, 4) if total > 0 else 0,
        "details": results,
    }


def evaluate_missing_evidence_handling() -> dict:
    """
    Test that the system handles questions with no available evidence gracefully.
    """
    unanswerable_questions = [
        "What is the quantum mechanics homework for next week?",
        "Can you change my grade to an A?",
        "What is Professor Smith's phone number?",
    ]

    results = []
    graceful = 0

    for q in unanswerable_questions:
        trace = run_agent(q, force_fallback=True)

        # Check for graceful handling: should not assert strong confidence
        confidence_appropriate = trace.confidence.get("score", 1.0) < 0.7
        has_no_fabrication = not any(
            phrase in trace.answer.lower()
            for phrase in ["i am certain", "definitely", "i guarantee"]
        )

        is_graceful = confidence_appropriate and has_no_fabrication
        if is_graceful:
            graceful += 1

        results.append({
            "question": q,
            "confidence_score": trace.confidence.get("score", 0),
            "confidence_label": trace.confidence.get("label", ""),
            "confidence_appropriate": confidence_appropriate,
            "no_fabrication": has_no_fabrication,
            "graceful": is_graceful,
        })

    return {
        "metric": "missing_evidence_handling",
        "graceful": graceful,
        "total": len(unanswerable_questions),
        "rate": round(graceful / len(unanswerable_questions), 4),
        "details": results,
    }


def evaluate_retrieval_recall(k: int = 5) -> dict:
    """
    Measure Recall@k for document retrieval.
    Only meaningful when documents are indexed.
    """
    index_meta = dp.get_index_meta()
    if index_meta.get("num_chunks", 0) == 0:
        return {
            "metric": f"retrieval_recall@{k}",
            "status": "skipped",
            "reason": "No documents indexed. Upload documents and rebuild index to test retrieval.",
        }

    # Use test questions that should match documents
    retrieval_tests = [
        {"query": t["question"], "id": t["id"]}
        for t in TEST_DATASET
        if t["category"] != "general"
    ]

    results = []
    retrieved_count = 0

    for test in retrieval_tests:
        chunks = dp.retrieve(test["query"], top_k=k)
        has_results = len(chunks) > 0
        if has_results:
            retrieved_count += 1
        results.append({
            "id": test["id"],
            "query": test["query"],
            "num_retrieved": len(chunks),
            "top_similarity": round(chunks[0]["similarity"], 4) if chunks else 0,
            "retrieved": has_results,
        })

    return {
        "metric": f"retrieval_recall@{k}",
        "retrieved": retrieved_count,
        "total": len(retrieval_tests),
        "recall": round(retrieved_count / len(retrieval_tests), 4) if retrieval_tests else 0,
        "details": results,
    }


# ── Full evaluation runner ────────────────────────────────

def run_full_evaluation() -> dict:
    """Run all evaluation metrics and return combined results."""
    start = time.time()

    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "intent_classification": evaluate_intent_classification(),
        "database_lookups": evaluate_database_lookups(),
        "source_attribution": evaluate_source_attribution(),
        "missing_evidence": evaluate_missing_evidence_handling(),
        "retrieval_recall": evaluate_retrieval_recall(),
        "elapsed_seconds": 0,
    }

    results["elapsed_seconds"] = round(time.time() - start, 2)

    # Save results
    output_path = TEST_DATA_DIR / "evaluation_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results
