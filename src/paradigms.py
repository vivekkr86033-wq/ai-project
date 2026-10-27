"""
paradigms.py — AI Paradigms Evaluator and Comparison Module.

Provides structured comparisons of major AI paradigms with classroom
applications, and a task-based recommender.

All comparisons are conceptual (based on established knowledge);
they are NOT measured benchmark results.
"""

from typing import Optional


# ── Paradigm Definitions ──────────────────────────────────

PARADIGMS: dict[str, dict] = {
    "symbolic_rule_based": {
        "name": "Symbolic / Rule-Based AI",
        "operating_principle": (
            "Uses explicitly programmed rules (if-then-else), logic, and knowledge graphs "
            "to reason. Decisions are made by matching inputs to predefined rules."
        ),
        "strengths": [
            "Fully transparent and explainable decisions",
            "Deterministic and predictable behavior",
            "Easy to audit and verify",
            "No training data required",
            "Works well for structured, well-defined domains",
        ],
        "limitations": [
            "Cannot handle ambiguity or novel situations",
            "Rules must be manually authored — does not scale",
            "Brittle when inputs fall outside defined rules",
            "No learning from data",
        ],
        "classroom_applications": [
            "Enforcing classroom rules (e.g., late submission penalties)",
            "Automated grading of structured assignments (multiple choice)",
            "Schedule conflict detection",
            "Prerequisite checking",
        ],
        "computational_cost": "Very Low",
        "recommendation": (
            "Best for well-defined, rule-based tasks where transparency is critical. "
            "Ideal for policy enforcement and structured validation in education."
        ),
    },
    "classical_ml": {
        "name": "Classical Machine Learning",
        "operating_principle": (
            "Learns patterns from structured/tabular data using algorithms like "
            "decision trees, SVMs, logistic regression, and random forests. "
            "Requires feature engineering and labeled datasets."
        ),
        "strengths": [
            "Handles structured data efficiently",
            "Interpretable models (e.g., decision trees)",
            "Relatively low computational requirements",
            "Well-understood mathematical foundations",
            "Good performance on tabular data",
        ],
        "limitations": [
            "Requires manual feature engineering",
            "Struggles with unstructured data (images, text)",
            "Performance limited by feature quality",
            "Needs labeled training data",
        ],
        "classroom_applications": [
            "Predicting student performance from grades and attendance (with authorization)",
            "Identifying at-risk students based on engagement metrics",
            "Clustering students by learning style",
            "Automated essay scoring (basic features)",
        ],
        "computational_cost": "Low to Moderate",
        "recommendation": (
            "Best for structured data analysis tasks in education. "
            "Use when you have tabular data and need interpretable predictions. "
            "Note: Student data usage requires proper authorization and privacy safeguards."
        ),
    },
    "deep_learning": {
        "name": "Deep Learning",
        "operating_principle": (
            "Uses multi-layer neural networks to learn hierarchical representations "
            "directly from raw data. Excels at unstructured data like images, audio, and text."
        ),
        "strengths": [
            "Automatic feature learning from raw data",
            "State-of-the-art on images, audio, video, and text tasks",
            "Scales well with more data and compute",
            "Transfer learning enables reuse across tasks",
        ],
        "limitations": [
            "Requires large datasets for training",
            "Computationally expensive (GPU/TPU needed)",
            "Often acts as a black box — limited interpretability",
            "Risk of overfitting on small datasets",
            "Energy-intensive training process",
        ],
        "classroom_applications": [
            "Handwriting recognition for digitizing student work",
            "Speech-to-text for lecture transcription",
            "Image classification for lab experiment analysis",
            "Sentiment analysis of student feedback",
        ],
        "computational_cost": "High",
        "recommendation": (
            "Best for tasks involving unstructured data where accuracy is paramount. "
            "Consider cost and interpretability trade-offs in educational settings."
        ),
    },
    "generative_ai_llm": {
        "name": "Generative AI / Large Language Models",
        "operating_principle": (
            "Pre-trained on massive text corpora using transformer architectures. "
            "Generates human-like text, can summarize, translate, explain, and converse. "
            "Uses patterns learned during pre-training."
        ),
        "strengths": [
            "Versatile — handles many NLP tasks without task-specific training",
            "Excellent natural language understanding and generation",
            "Can explain concepts at various complexity levels",
            "Supports interactive, conversational interfaces",
        ],
        "limitations": [
            "Can hallucinate — generates plausible but incorrect information",
            "No guaranteed factual accuracy without grounding",
            "High computational cost for training and inference",
            "Privacy concerns with data sent to external APIs",
            "Difficult to audit and verify outputs",
        ],
        "classroom_applications": [
            "Tutoring and concept explanation",
            "Generating practice questions and study materials",
            "Summarizing lecture notes",
            "Providing writing feedback",
        ],
        "computational_cost": "Very High (training) / Moderate-High (inference)",
        "recommendation": (
            "Powerful for educational content generation and tutoring, but must be "
            "grounded with verified sources to prevent misinformation. "
            "Best used with RAG for factual tasks."
        ),
    },
    "rag": {
        "name": "Retrieval-Augmented Generation (RAG)",
        "operating_principle": (
            "Combines a retrieval system (searching a document store) with a generative model. "
            "First retrieves relevant documents/passages, then generates answers grounded "
            "in the retrieved context. Reduces hallucination by anchoring responses in evidence."
        ),
        "strengths": [
            "Grounds LLM outputs in verifiable sources",
            "Reduces hallucination compared to pure LLM",
            "Knowledge can be updated by changing the document store (no retraining)",
            "Provides source attribution for answers",
            "Works with domain-specific, private knowledge bases",
        ],
        "limitations": [
            "Quality depends on retrieval accuracy",
            "Still requires an LLM for generation (or uses extractive fallback)",
            "Chunking and embedding quality affect results",
            "Complex pipeline to maintain",
        ],
        "classroom_applications": [
            "Answering questions from course materials with citations",
            "Searching syllabus and lecture notes semantically",
            "Providing evidence-based tutoring from uploaded resources",
            "This application is a RAG system",
        ],
        "computational_cost": "Moderate (retrieval) + LLM cost (generation)",
        "recommendation": (
            "The recommended approach for educational Q&A systems. "
            "Combines the flexibility of LLMs with the accuracy of document retrieval. "
            "This Classroom AI Assistant uses RAG as its primary paradigm."
        ),
    },
    "agentic_ai": {
        "name": "Agentic AI",
        "operating_principle": (
            "AI systems that can observe, reason, plan, and take actions autonomously. "
            "Uses an explicit cycle: perceive environment → reason about goals → "
            "select actions → execute → evaluate results. May use tools, APIs, or "
            "other AI models as sub-components."
        ),
        "strengths": [
            "Can handle multi-step, complex tasks",
            "Adapts strategy based on context and results",
            "Can compose multiple AI techniques (RAG, LLM, rules)",
            "Transparent decision-making when designed well",
        ],
        "limitations": [
            "Complex to design and test",
            "Autonomy must be carefully bounded",
            "Errors can compound across steps",
            "Requires clear goal specification and constraints",
            "Current systems have limited true reasoning ability",
        ],
        "classroom_applications": [
            "Intelligent tutoring systems with adaptive behavior",
            "This assistant's rational agent (observe → classify → act → evaluate)",
            "Automated assignment feedback pipelines",
            "Personalized learning path generation",
        ],
        "computational_cost": "Variable (depends on sub-components used)",
        "recommendation": (
            "Promising for complex educational workflows but must be designed with "
            "clear boundaries. This assistant implements a transparent, bounded agent "
            "cycle rather than claiming unrestricted autonomy."
        ),
    },
}


# ── Task Recommender ──────────────────────────────────────

TASK_RECOMMENDATIONS: dict[str, dict] = {
    "enforce_rule": {
        "task": "Enforcing a classroom rule (e.g., late submission penalty)",
        "recommended_paradigm": "symbolic_rule_based",
        "reasoning": (
            "Rule enforcement is deterministic and well-defined. Symbolic AI provides "
            "transparent, auditable decisions. An ML model is unnecessary for tasks with "
            "clear if-then logic."
        ),
        "alternatives": ["classical_ml"],
    },
    "predict_performance": {
        "task": "Predicting student performance from authorized data",
        "recommended_paradigm": "classical_ml",
        "reasoning": (
            "Student performance data is typically tabular (grades, attendance, engagement). "
            "Classical ML models like random forests or logistic regression handle this well "
            "and provide interpretable results. Deep learning is overkill for tabular data."
        ),
        "alternatives": ["deep_learning"],
    },
    "explain_concept": {
        "task": "Explaining a concept to a student",
        "recommended_paradigm": "rag",
        "reasoning": (
            "RAG combines the ability to search course materials for accurate information "
            "with natural language generation for clear explanations. Pure LLM risks "
            "hallucination; RAG grounds the explanation in course documents."
        ),
        "alternatives": ["generative_ai_llm"],
    },
    "search_syllabus": {
        "task": "Searching a syllabus for a topic",
        "recommended_paradigm": "rag",
        "reasoning": (
            "Semantic search (the retrieval component of RAG) can find relevant topics "
            "even when exact keywords don't match. For a simple keyword match, even "
            "rule-based search works, but embeddings handle semantic similarity better."
        ),
        "alternatives": ["symbolic_rule_based"],
    },
    "plan_revision": {
        "task": "Planning a revision schedule",
        "recommended_paradigm": "agentic_ai",
        "reasoning": (
            "Revision planning requires multiple steps: analyzing syllabus topics, "
            "assessing time constraints, distributing topics, and adapting the plan. "
            "An agent can orchestrate these steps, using rule-based scheduling logic "
            "and RAG for content retrieval."
        ),
        "alternatives": ["symbolic_rule_based", "rag"],
    },
    "generate_quiz": {
        "task": "Generating practice quiz questions",
        "recommended_paradigm": "rag",
        "reasoning": (
            "Questions should be grounded in actual course material. RAG retrieves "
            "relevant content and either an LLM generates diverse questions or "
            "templates are filled with retrieved concepts (extractive fallback)."
        ),
        "alternatives": ["generative_ai_llm"],
    },
    "grade_essay": {
        "task": "Grading a student essay",
        "recommended_paradigm": "deep_learning",
        "reasoning": (
            "Essay grading requires understanding natural language at a deep level. "
            "Fine-tuned deep learning models (or LLMs) can assess coherence, argument "
            "quality, and writing mechanics. Classical ML can handle surface features "
            "but misses semantic depth."
        ),
        "alternatives": ["generative_ai_llm", "classical_ml"],
    },
}


# ── Public API ────────────────────────────────────────────

def get_all_paradigms() -> dict:
    """Return all paradigm definitions."""
    return PARADIGMS


def get_paradigm(paradigm_id: str) -> Optional[dict]:
    return PARADIGMS.get(paradigm_id)


def get_comparison_table() -> list[dict]:
    """Return paradigms in a flat list suitable for table display."""
    rows = []
    for pid, p in PARADIGMS.items():
        rows.append({
            "id": pid,
            "name": p["name"],
            "principle": p["operating_principle"][:120] + "…",
            "strengths": len(p["strengths"]),
            "limitations": len(p["limitations"]),
            "cost": p["computational_cost"],
            "classroom_apps": len(p["classroom_applications"]),
        })
    return rows


def get_task_recommendations() -> dict:
    """Return all task recommendations."""
    return TASK_RECOMMENDATIONS


def recommend_for_task(task_id: str) -> Optional[dict]:
    """Get recommendation for a specific task."""
    rec = TASK_RECOMMENDATIONS.get(task_id)
    if rec:
        result = rec.copy()
        result["paradigm_details"] = PARADIGMS.get(rec["recommended_paradigm"], {})
        return result
    return None
