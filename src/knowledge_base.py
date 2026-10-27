"""
knowledge_base.py — Structured course & rules data store.

Stores courses (name, description, syllabus topics, schedules,
assignments, deadlines) and classroom rules as editable JSON.
"""

import json
import re
from pathlib import Path
from typing import Any
from src.config import COURSE_DB_PATH, RULES_DB_PATH

# ── Default sample data ───────────────────────────────────

_DEFAULT_COURSES: list[dict[str, Any]] = [
    {
        "id": "CS101",
        "name": "Introduction to Computer Science",
        "description": "Foundational course covering algorithms, data structures, and programming basics.",
        "syllabus": [
            "Week 1-2: Introduction to Programming & Python Basics",
            "Week 3-4: Control Structures and Functions",
            "Week 5-6: Data Structures — Lists, Stacks, Queues",
            "Week 7-8: Sorting and Searching Algorithms",
            "Week 9-10: Object-Oriented Programming",
            "Week 11-12: File I/O and Exception Handling",
            "Week 13-14: Introduction to Databases",
            "Week 15-16: Final Project and Review",
        ],
        "schedule": "Mon/Wed/Fri 09:00–10:00 AM, Room 201",
        "assignments": [
            {
                "title": "Assignment 1: Python Basics",
                "description": "Write programs demonstrating variables, loops, and functions.",
                "deadline": "2026-11-10",
                "max_marks": 100,
            },
            {
                "title": "Assignment 2: Data Structures",
                "description": "Implement a stack and queue using linked lists.",
                "deadline": "2026-11-24",
                "max_marks": 100,
            },
            {
                "title": "Final Project: Mini Application",
                "description": "Build a small command-line application using concepts from the entire course.",
                "deadline": "2026-12-15",
                "max_marks": 200,
            },
        ],
        "instructor": "Dr. Alice Martin",
    },
    {
        "id": "AI201",
        "name": "Introduction to Artificial Intelligence",
        "description": "Survey course on AI paradigms, search, knowledge representation, and machine learning fundamentals.",
        "syllabus": [
            "Week 1-2: What is AI? History and Foundations",
            "Week 3-4: Intelligent Agents and Rational Behavior",
            "Week 5-6: Search Algorithms — BFS, DFS, A*",
            "Week 7-8: Knowledge Representation and Reasoning",
            "Week 9-10: Machine Learning Basics — Supervised Learning",
            "Week 11-12: Neural Networks and Deep Learning Introduction",
            "Week 13-14: Natural Language Processing and RAG",
            "Week 15-16: Ethics in AI and Course Review",
        ],
        "schedule": "Tue/Thu 11:00 AM–12:30 PM, Room 305",
        "assignments": [
            {
                "title": "Assignment 1: Search Algorithms",
                "description": "Implement BFS and A* on a grid-world problem.",
                "deadline": "2026-11-12",
                "max_marks": 100,
            },
            {
                "title": "Assignment 2: ML Classification",
                "description": "Train and evaluate a classifier on the Iris dataset.",
                "deadline": "2026-11-28",
                "max_marks": 100,
            },
            {
                "title": "Final Project: AI Application",
                "description": "Design an AI agent for a classroom task and present findings.",
                "deadline": "2026-12-18",
                "max_marks": 200,
            },
        ],
        "instructor": "Prof. Bob Singh",
    },
    {
        "id": "MATH150",
        "name": "Linear Algebra for Computing",
        "description": "Vectors, matrices, transformations, eigenvalues, and applications in data science.",
        "syllabus": [
            "Week 1-2: Systems of Linear Equations",
            "Week 3-4: Vectors and Vector Spaces",
            "Week 5-6: Matrices and Matrix Operations",
            "Week 7-8: Determinants",
            "Week 9-10: Eigenvalues and Eigenvectors",
            "Week 11-12: Orthogonality and Least Squares",
            "Week 13-14: Singular Value Decomposition",
            "Week 15-16: Applications in ML and Review",
        ],
        "schedule": "Mon/Wed 02:00–03:30 PM, Room 110",
        "assignments": [
            {
                "title": "Problem Set 1: Systems & Vectors",
                "description": "Solve systems of equations and perform vector operations.",
                "deadline": "2026-11-08",
                "max_marks": 50,
            },
            {
                "title": "Problem Set 2: Eigenvalue Analysis",
                "description": "Compute eigenvalues and eigenvectors for given matrices.",
                "deadline": "2026-12-01",
                "max_marks": 50,
            },
        ],
        "instructor": "Dr. Carol Zhang",
    },
]

_DEFAULT_RULES: list[dict[str, str]] = [
    {"id": "R1", "rule": "Attendance is mandatory. Students missing more than 3 classes must meet with the instructor."},
    {"id": "R2", "rule": "Assignments must be submitted before the deadline. Late submissions lose 10% per day, up to 3 days."},
    {"id": "R3", "rule": "Academic integrity: plagiarism or AI-generated submissions without attribution will result in a zero grade."},
    {"id": "R4", "rule": "Mobile phones must be silenced during lectures."},
    {"id": "R5", "rule": "Lab sessions require safety goggles where applicable. Food and drinks are not allowed in the computer lab."},
    {"id": "R6", "rule": "Students may request office hours by email at least 24 hours in advance."},
    {"id": "R7", "rule": "Group projects: each member must contribute. Peer evaluations are part of the grading rubric."},
    {"id": "R8", "rule": "Exams are closed-book unless otherwise stated. Allowed materials will be specified per exam."},
]


# ── Persistence helpers ───────────────────────────────────

def _load_json(path: Path, default: Any) -> Any:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Public API ────────────────────────────────────────────

def load_courses() -> list[dict]:
    """Load courses from disk; initialise with samples if absent."""
    courses = _load_json(COURSE_DB_PATH, None)
    if courses is None:
        courses = _DEFAULT_COURSES
        _save_json(COURSE_DB_PATH, courses)
    return courses


def save_courses(courses: list[dict]) -> None:
    _save_json(COURSE_DB_PATH, courses)


def load_rules() -> list[dict]:
    rules = _load_json(RULES_DB_PATH, None)
    if rules is None:
        rules = _DEFAULT_RULES
        _save_json(RULES_DB_PATH, rules)
    return rules


def save_rules(rules: list[dict]) -> None:
    _save_json(RULES_DB_PATH, rules)


def get_course_by_id(course_id: str) -> dict | None:
    for c in load_courses():
        if c["id"] == course_id:
            return c
    return None


_SEARCH_STOPWORDS = {
    "what", "is", "the", "for", "to", "in", "a", "an", "and", "or", "of",
    "how", "can", "you", "tell", "me", "about", "are", "do", "does", "did",
    "please", "i", "we", "my", "our", "your", "there", "any", "when",
    "where", "which", "who", "whom", "this", "that", "these", "those",
    "with", "from", "at", "by", "on"
}


def _extract_query_tokens(query: str) -> list[str]:
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower())
    tokens = [w for w in words if w not in _SEARCH_STOPWORDS and len(w) >= 2]
    return tokens if tokens else [w for w in words if len(w) >= 2]


def search_courses(query: str) -> list[dict]:
    """Case-insensitive keyword search across course fields."""
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    courses = load_courses()
    exact_matches = []
    course_searchables = []

    for c in courses:
        searchable = " ".join([
            c.get("id", ""),
            c.get("name", ""),
            c.get("description", ""),
            " ".join(c.get("syllabus", [])),
            c.get("schedule", ""),
            c.get("instructor", ""),
            " ".join(a.get("title", "") + " " + a.get("description", "") for a in c.get("assignments", [])),
        ]).lower()
        course_searchables.append((c, searchable))
        if query_lower in searchable:
            exact_matches.append(c)

    if exact_matches:
        return exact_matches

    tokens = _extract_query_tokens(query_lower)
    if not tokens:
        return []

    scored = []
    for c, searchable in course_searchables:
        match_count = sum(1 for t in tokens if t in searchable)
        if match_count > 0:
            scored.append((match_count, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for count, c in scored]


def search_rules(query: str) -> list[dict]:
    """Case-insensitive keyword search across classroom rules."""
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    rules = load_rules()
    exact_matches = []
    rule_searchables = []

    for r in rules:
        searchable = f"{r.get('id', '')} {r.get('rule', '')} {r.get('category', '')}".lower()
        rule_searchables.append((r, searchable))
        if query_lower in searchable:
            exact_matches.append(r)

    if exact_matches:
        return exact_matches

    tokens = _extract_query_tokens(query_lower)
    if not tokens:
        return []

    scored = []
    for r, searchable in rule_searchables:
        match_count = sum(1 for t in tokens if t in searchable)
        if match_count > 0:
            scored.append((match_count, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for count, r in scored]


def get_all_structured_text() -> str:
    """Return all course + rule information as a single text block (used by the agent)."""
    parts: list[str] = []
    for c in load_courses():
        parts.append(f"Course: {c['name']} ({c['id']})")
        parts.append(f"  Description: {c['description']}")
        parts.append(f"  Instructor: {c.get('instructor', 'N/A')}")
        parts.append(f"  Schedule: {c.get('schedule', 'N/A')}")
        parts.append("  Syllabus:")
        for topic in c.get("syllabus", []):
            parts.append(f"    - {topic}")
        for a in c.get("assignments", []):
            parts.append(f"  Assignment: {a['title']} — Due {a['deadline']} — {a['description']}")
    parts.append("\nClassroom Rules:")
    for r in load_rules():
        parts.append(f"  [{r['id']}] {r['rule']}")
    return "\n".join(parts)
