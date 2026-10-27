"""
rational_agent.py — Explicit rational agent cycle.

Implements a transparent, testable agent that:
1. Observes the user's question and available context
2. Classifies intent
3. Identifies goal and constraints
4. Selects an action
5. Evaluates evidence and produces an answer
6. Returns answer + sources + action + decision explanation
"""

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from src import knowledge_base as kb
from src import document_processor as dp
from src.llm_provider import generate_answer, compute_confidence


# ── Intent taxonomy ───────────────────────────────────────

INTENTS = {
    "course_info": {
        "description": "Questions about course details, schedules, instructors",
        "keywords": [
            "course", "class", "schedule", "instructor", "professor", "teacher",
            "room", "time", "when", "where", "who teaches", "section", "credit",
        ],
    },
    "classroom_rules": {
        "description": "Questions about rules, policies, conduct",
        "keywords": [
            "rule", "policy", "attendance", "plagiarism", "late", "submission",
            "phone", "lab", "integrity", "conduct", "allowed", "prohibited",
            "penalty", "grading", "deadline policy",
        ],
    },
    "syllabus_help": {
        "description": "Questions about syllabus topics, what is covered, curriculum",
        "keywords": [
            "syllabus", "topic", "cover", "curriculum", "week", "learn",
            "subject", "module", "chapter", "content", "what will", "outline",
        ],
    },
    "assignment_guidance": {
        "description": "Questions about assignments, homework, projects, deadlines",
        "keywords": [
            "assignment", "homework", "project", "due", "deadline", "submit",
            "marks", "grade", "requirement", "deliverable", "task", "problem set",
        ],
    },
    "learning_resources": {
        "description": "Questions about learning materials, documents, references",
        "keywords": [
            "document", "resource", "material", "reading", "reference", "book",
            "pdf", "notes", "slides", "tutorial", "guide", "explain", "help me understand",
        ],
    },
    "general_question": {
        "description": "General questions, greetings, or unclear intent",
        "keywords": [],
    },
}


# ── Agent data structures ─────────────────────────────────

@dataclass
class AgentTrace:
    """Complete trace of one agent cycle for transparency."""
    timestamp: float = 0.0
    question: str = ""
    # Step 1: Observation
    observation: str = ""
    # Step 2: Intent classification
    classified_intent: str = ""
    intent_scores: dict = field(default_factory=dict)
    # Step 3: Goal identification
    goal: str = ""
    constraints: list = field(default_factory=list)
    # Step 4: Action selection
    selected_action: str = ""
    action_reason: str = ""
    # Step 5: Evidence evaluation
    evidence_summary: str = ""
    retrieval_results: list = field(default_factory=list)
    confidence: dict = field(default_factory=dict)
    # Step 6: Answer
    answer: str = ""
    sources: list = field(default_factory=list)
    answer_mode: str = ""
    decision_explanation: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ── Intent classifier ────────────────────────────────────

def classify_intent(query: str) -> tuple[str, dict]:
    """
    Rule-based intent classifier using keyword matching.
    Returns (best_intent, scores_dict).
    """
    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower))
    scores = {}

    for intent, info in INTENTS.items():
        if intent == "general_question":
            continue
        keywords = info["keywords"]
        score = 0
        for kw in keywords:
            kw_words = set(kw.lower().split())
            if kw_words.issubset(query_words):
                score += 2  # Exact multi-word match
            elif any(w in query_lower for w in kw_words):
                score += 1  # Partial match
        scores[intent] = score

    best_intent = max(scores, key=scores.get) if scores else "general_question"
    if scores.get(best_intent, 0) == 0:
        best_intent = "general_question"
        scores["general_question"] = 1
    else:
        scores["general_question"] = 0

    return best_intent, scores


# ── Action selection ──────────────────────────────────────

ACTIONS = {
    "database_lookup": "Search the structured course/rules database",
    "rag_retrieval": "Retrieve and answer from uploaded documents using RAG",
    "combined_lookup": "Search both database and documents",
    "learning_workflow": "Activate a learning support workflow",
    "general_explanation": "Provide a general explanation or guidance",
    "refer_to_teacher": "Refer the question to a teacher/instructor",
}


def select_action(intent: str, query: str, has_documents: bool) -> tuple[str, str]:
    """
    Select the best action based on intent and available resources.
    Returns (action_name, reason).
    """
    if intent == "course_info":
        return "database_lookup", "Course information is stored in the structured database."
    elif intent == "classroom_rules":
        return "database_lookup", "Classroom rules are stored in the structured database."
    elif intent == "syllabus_help":
        if has_documents:
            return "combined_lookup", "Syllabus info may be in both the database and uploaded documents."
        return "database_lookup", "Syllabus topics are stored in the course database."
    elif intent == "assignment_guidance":
        if has_documents:
            return "combined_lookup", "Assignment details may be in the database and supplementary documents."
        return "database_lookup", "Assignment information is stored in the course database."
    elif intent == "learning_resources":
        if has_documents:
            return "rag_retrieval", "Learning resources should be searched in the uploaded document library."
        return "general_explanation", "No documents are indexed yet. Providing general guidance."
    else:
        if has_documents:
            return "combined_lookup", "General question — searching all available sources."
        return "general_explanation", "No specific data source identified. Providing general guidance."


# ── Execute actions ───────────────────────────────────────

def _execute_database_lookup(query: str) -> tuple[list[dict], list[str]]:
    """Search structured knowledge base."""
    course_results = kb.search_courses(query)
    rule_results = kb.search_rules(query)

    chunks = []
    sources = []

    for c in course_results:
        text_parts = [f"Course: {c['name']} ({c['id']})"]
        text_parts.append(f"Description: {c['description']}")
        text_parts.append(f"Schedule: {c.get('schedule', 'N/A')}")
        text_parts.append(f"Instructor: {c.get('instructor', 'N/A')}")
        if c.get("syllabus"):
            text_parts.append("Syllabus: " + "; ".join(c["syllabus"]))
        for a in c.get("assignments", []):
            text_parts.append(f"Assignment: {a['title']} — Due: {a['deadline']} — {a['description']}")
        chunks.append({
            "doc_name": "Course Database",
            "page_or_section": c["id"],
            "text": "\n".join(text_parts),
            "similarity": 0.9,  # High confidence for structured data
        })
        sources.append(f"Course Database: {c['name']} ({c['id']})")

    for r in rule_results:
        chunks.append({
            "doc_name": "Classroom Rules",
            "page_or_section": r["id"],
            "text": f"Rule {r['id']}: {r['rule']}",
            "similarity": 0.85,
        })
        sources.append(f"Classroom Rules: {r['id']}")

    return chunks, sources


def _execute_rag_retrieval(query: str) -> tuple[list[dict], list[str]]:
    """Search indexed documents using semantic retrieval."""
    results = dp.retrieve(query)
    if not results:
        # Fallback to keyword search
        results = dp.keyword_search(query)

    sources = []
    for r in results:
        source = r["doc_name"]
        page = r.get("page_or_section", "")
        label = source
        if page:
            label += f" ({page})"
        if label not in sources:
            sources.append(label)

    return results, sources


# ── Main agent cycle ──────────────────────────────────────

def run_agent(query: str, force_fallback: bool = False) -> AgentTrace:
    """
    Execute the full rational agent cycle.

    Parameters:
        query: The user's question
        force_fallback: If True, use extractive fallback even if LLM is available

    Returns:
        AgentTrace with full transparency into the decision process
    """
    wall_time = time.time()
    start_time = time.perf_counter()
    trace = AgentTrace(timestamp=wall_time, question=query)

    # ── Step 1: Observe ───────────────────────────────────
    index_meta = dp.get_index_meta()
    has_documents = index_meta.get("num_chunks", 0) > 0
    num_courses = len(kb.load_courses())
    num_rules = len(kb.load_rules())

    trace.observation = (
        f"Received question: \"{query}\". "
        f"Available resources: {num_courses} courses, {num_rules} rules, "
        f"{index_meta.get('num_chunks', 0)} document chunks from "
        f"{index_meta.get('num_docs', 0)} documents."
    )

    # ── Step 2: Classify intent ───────────────────────────
    intent, scores = classify_intent(query)
    trace.classified_intent = intent
    trace.intent_scores = scores

    # ── Step 3: Identify goal & constraints ───────────────
    intent_info = INTENTS.get(intent, INTENTS["general_question"])
    trace.goal = f"Answer a {intent_info['description'].lower()} question."
    trace.constraints = [
        "Answer must be grounded in available data.",
        "Must cite sources when available.",
        "Must not fabricate information.",
        "Must indicate when evidence is insufficient.",
    ]
    if intent == "assignment_guidance":
        trace.constraints.append("Must not claim to submit assignments on behalf of the student.")

    # ── Step 4: Select action ─────────────────────────────
    action, reason = select_action(intent, query, has_documents)
    trace.selected_action = action
    trace.action_reason = reason

    # ── Step 5: Execute action & evaluate evidence ────────
    all_chunks = []
    all_sources = []

    if action in ("database_lookup", "combined_lookup"):
        db_chunks, db_sources = _execute_database_lookup(query)
        all_chunks.extend(db_chunks)
        all_sources.extend(db_sources)

    if action in ("rag_retrieval", "combined_lookup"):
        rag_chunks, rag_sources = _execute_rag_retrieval(query)
        all_chunks.extend(rag_chunks)
        all_sources.extend(rag_sources)

    if action == "general_explanation" and not all_chunks:
        # Try a broad search as last resort
        db_chunks, db_sources = _execute_database_lookup(query)
        all_chunks.extend(db_chunks)
        all_sources.extend(db_sources)

    trace.retrieval_results = [
        {
            "doc_name": c.get("doc_name", ""),
            "page_or_section": c.get("page_or_section", ""),
            "similarity": c.get("similarity", 0),
            "text_preview": c["text"][:200] + "…" if len(c["text"]) > 200 else c["text"],
        }
        for c in all_chunks
    ]

    confidence = compute_confidence(all_chunks)
    trace.confidence = confidence

    if all_chunks:
        trace.evidence_summary = (
            f"Found {len(all_chunks)} relevant pieces of evidence. "
            f"Retrieval confidence: {confidence['label']} ({confidence['score']:.2f}). "
            f"{confidence['explanation']}"
        )
    else:
        trace.evidence_summary = "No relevant evidence found in available sources."

    # ── Step 6: Generate answer ───────────────────────────
    answer_result = generate_answer(
        query=query,
        context_chunks=all_chunks,
        force_fallback=force_fallback,
    )

    trace.answer = answer_result["answer"]
    trace.answer_mode = answer_result["mode"]
    trace.sources = all_sources

    # Build decision explanation
    trace.decision_explanation = (
        f"Intent classified as '{intent}' → action '{action}' selected because: {reason} "
        f"Found {len(all_chunks)} evidence chunks. "
        f"Evidence quality: {confidence['label']}. "
        f"Answer mode: {answer_result['mode']} (model: {answer_result['model']})."
    )

    trace.elapsed_ms = max(round((time.perf_counter() - start_time) * 1000, 2), 0.01)

    return trace
