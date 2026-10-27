"""
learning_workflows.py — Structured learning support workflows.

Each workflow is a deterministic, transparent function that generates
structured educational content from available data.
"""

import re
from datetime import datetime, timedelta
from typing import Optional

from src import knowledge_base as kb
from src import document_processor as dp
from src.llm_provider import generate_answer


# ── Helpers ───────────────────────────────────────────────

def _find_syllabus_topics(course_id: Optional[str] = None) -> list[str]:
    """Gather all syllabus topics, optionally filtered by course."""
    courses = kb.load_courses()
    topics = []
    for c in courses:
        if course_id and c["id"] != course_id:
            continue
        topics.extend(c.get("syllabus", []))
    return topics


# ── Workflow 1: Topic Explanation ─────────────────────────

def explain_topic(topic: str, level: str = "beginner", course_id: Optional[str] = None) -> dict:
    """
    Explain a syllabus topic at the requested level.

    Levels: beginner, intermediate, advanced

    Returns structured explanation dict.
    """
    # Find the topic in syllabus
    all_topics = _find_syllabus_topics(course_id)
    matching = [t for t in all_topics if topic.lower() in t.lower()]

    # Search documents for additional context
    doc_results = dp.retrieve(topic, top_k=3)
    if not doc_results:
        doc_results = dp.keyword_search(topic, top_k=3)

    level_guidance = {
        "beginner": {
            "approach": "Use simple language, analogies, and step-by-step explanations. Avoid jargon.",
            "depth": "Cover the fundamentals and core concepts only.",
            "example_prefix": "Think of it like this: ",
        },
        "intermediate": {
            "approach": "Use standard technical terminology with clear definitions. Include examples.",
            "depth": "Cover core concepts plus common variations and trade-offs.",
            "example_prefix": "For example: ",
        },
        "advanced": {
            "approach": "Use precise technical language. Discuss edge cases and optimizations.",
            "depth": "Cover advanced aspects, mathematical foundations, and research directions.",
            "example_prefix": "Consider the nuanced case: ",
        },
    }

    guide = level_guidance.get(level, level_guidance["beginner"])

    # Build explanation from available data
    explanation_parts = []

    if matching:
        explanation_parts.append(f"**Topic found in syllabus:** {', '.join(matching)}")
    else:
        explanation_parts.append(f"**Topic:** {topic} (not found in any loaded syllabus — providing general guidance)")

    explanation_parts.append(f"\n**Level:** {level.capitalize()}")
    explanation_parts.append(f"**Approach:** {guide['approach']}")
    explanation_parts.append(f"**Depth:** {guide['depth']}")

    if doc_results:
        explanation_parts.append("\n**Relevant content from documents:**")
        for i, chunk in enumerate(doc_results[:3], 1):
            source = chunk.get("doc_name", "unknown")
            page = chunk.get("page_or_section", "")
            text = chunk["text"][:400].strip()
            ref = f"[{source}"
            if page:
                ref += f", {page}"
            ref += "]"
            explanation_parts.append(f"\n*{guide['example_prefix']}*\n> {text}\n> — {ref}")
    else:
        explanation_parts.append(
            "\n*No supplementary documents found for this topic. "
            "Upload relevant materials to get richer explanations.*"
        )

    return {
        "workflow": "topic_explanation",
        "topic": topic,
        "level": level,
        "syllabus_match": matching,
        "document_sources": [c.get("doc_name", "") for c in doc_results],
        "explanation": "\n".join(explanation_parts),
    }


# ── Workflow 2: Practice Quiz Generation ──────────────────

def generate_quiz(topic: str, num_questions: int = 5, course_id: Optional[str] = None) -> dict:
    """
    Generate practice quiz questions from the syllabus and uploaded material.

    Uses deterministic templates + retrieved content to create questions.
    """
    # Search for content
    doc_results = dp.retrieve(topic, top_k=5)
    if not doc_results:
        doc_results = dp.keyword_search(topic, top_k=5)

    syllabus_topics = _find_syllabus_topics(course_id)
    matching_topics = [t for t in syllabus_topics if topic.lower() in t.lower()]

    questions = []

    # Template-based question generation from content
    question_templates = [
        ("definition", "Define the following concept: **{concept}**"),
        ("explanation", "Explain how **{concept}** works in your own words."),
        ("comparison", "Compare and contrast two aspects of **{concept}**."),
        ("application", "Give a real-world example of how **{concept}** can be applied."),
        ("critical_thinking", "What are the limitations or challenges of **{concept}**?"),
        ("short_answer", "In 2-3 sentences, summarize the key idea of **{concept}**."),
        ("true_false", "True or False: **{concept}** is a fundamental topic in this course. Justify your answer."),
    ]

    # Generate questions from matching topics and document content
    concepts = []
    if matching_topics:
        for t in matching_topics:
            # Extract the main concept from the topic string
            concept = re.sub(r"Week \d+-?\d*:\s*", "", t).strip()
            if concept:
                concepts.append(concept)

    # Also extract key phrases from documents
    if doc_results:
        for chunk in doc_results[:3]:
            text = chunk["text"]
            # Extract capitalized phrases or key terms
            sentences = text.split(".")
            for sent in sentences[:2]:
                sent = sent.strip()
                if len(sent) > 10 and len(sent) < 100:
                    concepts.append(sent)

    if not concepts:
        concepts = [topic]

    # Generate questions
    for i in range(min(num_questions, len(question_templates))):
        template_type, template = question_templates[i]
        concept = concepts[i % len(concepts)]
        questions.append({
            "number": i + 1,
            "type": template_type,
            "question": template.format(concept=concept),
            "source_topic": concept,
        })

    sources = []
    if matching_topics:
        sources.append("Course Syllabus")
    sources.extend([c.get("doc_name", "") for c in doc_results if c.get("doc_name")])

    return {
        "workflow": "practice_quiz",
        "topic": topic,
        "num_questions": len(questions),
        "questions": questions,
        "sources": list(set(sources)),
        "note": "These questions are generated from syllabus topics and uploaded documents. "
                "Answers should be based on course materials.",
    }


# ── Workflow 3: Revision Plan ─────────────────────────────

def create_revision_plan(
    course_id: Optional[str] = None,
    exam_date: Optional[str] = None,
    topics: Optional[list[str]] = None,
) -> dict:
    """
    Create a revision plan from syllabus topics and an exam date.

    If no exam date is given, defaults to 14 days from now.
    """
    # Get topics
    if topics:
        all_topics = topics
    else:
        all_topics = _find_syllabus_topics(course_id)
        if not all_topics:
            all_topics = _find_syllabus_topics()  # All courses

    if not all_topics:
        return {
            "workflow": "revision_plan",
            "error": "No syllabus topics found. Please specify a course or provide topics.",
        }

    # Parse exam date
    if exam_date:
        try:
            exam_dt = datetime.strptime(exam_date, "%Y-%m-%d")
        except ValueError:
            exam_dt = datetime.now() + timedelta(days=14)
    else:
        exam_dt = datetime.now() + timedelta(days=14)

    today = datetime.now()
    days_available = max((exam_dt - today).days, 1)

    # Distribute topics across available days
    topics_per_day = max(1, len(all_topics) // days_available + 1)

    plan_days = []
    topic_idx = 0
    current_date = today

    while topic_idx < len(all_topics) and current_date <= exam_dt:
        day_topics = all_topics[topic_idx:topic_idx + topics_per_day]
        plan_days.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_number": len(plan_days) + 1,
            "topics": day_topics,
            "activity": "Review" if len(plan_days) < days_available - 2 else "Practice & Self-Test",
        })
        topic_idx += topics_per_day
        current_date += timedelta(days=1)

    # Add final review day
    if current_date <= exam_dt:
        plan_days.append({
            "date": exam_dt.strftime("%Y-%m-%d"),
            "day_number": len(plan_days) + 1,
            "topics": ["All topics — final review"],
            "activity": "Mock Test & Final Review",
        })

    return {
        "workflow": "revision_plan",
        "course_id": course_id,
        "exam_date": exam_dt.strftime("%Y-%m-%d"),
        "days_available": days_available,
        "total_topics": len(all_topics),
        "plan": plan_days,
        "tips": [
            "Focus on understanding concepts, not memorization.",
            "Practice with the quiz generator for each topic.",
            "Review weak areas identified during practice.",
            "Take breaks — the Pomodoro technique (25 min study, 5 min break) is effective.",
            "Get adequate sleep before the exam.",
        ],
    }


# ── Workflow 4: Find Relevant Documents ───────────────────

def find_relevant_documents(query: str, top_k: int = 5) -> dict:
    """Search the document library for relevant learning materials."""
    results = dp.retrieve(query, top_k=top_k)
    if not results:
        results = dp.keyword_search(query, top_k=top_k)

    available_docs = dp.list_documents()

    if results:
        grouped: dict[str, list] = {}
        for r in results:
            name = r.get("doc_name", "unknown")
            if name not in grouped:
                grouped[name] = []
            grouped[name].append({
                "section": r.get("page_or_section", "N/A"),
                "relevance": round(r.get("similarity", 0), 3),
                "preview": r["text"][:200],
            })

        return {
            "workflow": "find_documents",
            "query": query,
            "found": True,
            "documents": grouped,
            "total_matches": len(results),
            "available_documents": len(available_docs),
        }
    else:
        return {
            "workflow": "find_documents",
            "query": query,
            "found": False,
            "documents": {},
            "total_matches": 0,
            "available_documents": len(available_docs),
            "suggestion": "No matching documents found. Try uploading relevant materials "
                         "in the Document Library, or rephrase your search.",
        }


# ── Workflow 5: Assignment Help ───────────────────────────

def explain_assignment(course_id: str, assignment_title: str = "") -> dict:
    """
    Explain assignment requirements. Does NOT claim to submit assignments.
    """
    course = kb.get_course_by_id(course_id)
    if not course:
        return {
            "workflow": "assignment_help",
            "error": f"Course '{course_id}' not found.",
        }

    assignments = course.get("assignments", [])
    if assignment_title:
        matching = [a for a in assignments if assignment_title.lower() in a["title"].lower()]
    else:
        matching = assignments

    if not matching:
        return {
            "workflow": "assignment_help",
            "course": course["name"],
            "error": "No matching assignment found.",
            "available_assignments": [a["title"] for a in assignments],
        }

    explanations = []
    for a in matching:
        explanations.append({
            "title": a["title"],
            "description": a["description"],
            "deadline": a["deadline"],
            "max_marks": a.get("max_marks", "N/A"),
            "guidance": [
                f"Read the assignment description carefully: \"{a['description']}\"",
                "Break the task into smaller sub-tasks.",
                "Start early — the deadline is " + a["deadline"] + ".",
                "Refer to relevant syllabus topics and uploaded materials.",
                "Ask your instructor during office hours if you need clarification.",
            ],
        })

    return {
        "workflow": "assignment_help",
        "course": course["name"],
        "assignments": explanations,
        "note": "This assistant explains requirements and provides guidance. "
                "It cannot submit assignments on your behalf. "
                "For submission, follow your course's submission process.",
    }


# ── Workflow 6: Refer to Teacher ──────────────────────────

def refer_to_teacher(question: str) -> dict:
    """
    For administrative questions the assistant cannot answer,
    provide referral information.
    """
    courses = kb.load_courses()
    instructors = []
    for c in courses:
        instr = c.get("instructor", "Unknown")
        schedule = c.get("schedule", "N/A")
        instructors.append({
            "course": c["name"],
            "instructor": instr,
            "schedule": schedule,
        })

    return {
        "workflow": "refer_to_teacher",
        "original_question": question,
        "message": (
            "This question requires human assistance. I cannot answer administrative "
            "questions about grade changes, special accommodations, enrollment issues, "
            "or other matters that require instructor authorization."
        ),
        "instructors": instructors,
        "suggestions": [
            "Contact your course instructor during office hours.",
            "Email your instructor at least 24 hours before office hours (per Rule R6).",
            "For urgent matters, contact the department office.",
        ],
    }
