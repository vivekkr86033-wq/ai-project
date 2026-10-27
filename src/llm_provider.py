"""
llm_provider.py — Configurable LLM interface with extractive fallback.

When no API key is set (LLM_PROVIDER=none), the system uses a deterministic
extractive fallback that selects and concatenates the most relevant passages
from retrieved context. This ensures the application is demonstrable without
any paid API access.

When an API key is provided, it calls the configured LLM for generation using
the official OpenAI Python SDK.
"""

from typing import Optional, List, Dict, Any
from src.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    llm_available,
    get_llm_provider,
    get_openai_api_key,
    get_openai_model,
    mask_api_key,
    reload_config,
)


# ── Extractive Fallback ──────────────────────────────────


def _extractive_answer(query: str, context_chunks: list[dict]) -> dict:
    """
    Deterministic extractive fallback: select the best passages from
    retrieved chunks and compose an answer without any LLM.

    Returns: {answer, mode, model, sources}
    """
    if not context_chunks:
        return {
            "answer": (
                "I could not find relevant information in the available documents or course data "
                "to answer your question. Could you rephrase or provide more detail? "
                "If this is an administrative question, please contact your instructor."
            ),
            "mode": "fallback_extractive",
            "model": "none",
            "sources": [],
        }

    # Sort by similarity (highest first)
    sorted_chunks = sorted(context_chunks, key=lambda c: c.get("similarity", 0), reverse=True)

    # Take top passages
    top = sorted_chunks[:3]
    passages = []
    sources = []
    for i, chunk in enumerate(top, 1):
        source = chunk.get("doc_name", "structured data")
        page = chunk.get("page_or_section", "")
        text = chunk.get("text", "").strip()
        # Trim very long passages
        if len(text) > 600:
            text = text[:600] + "…"
        source_label = f"[{source}"
        if page:
            source_label += f", {page}"
        source_label += "]"
        passages.append(f"**Passage {i}** {source_label}:\n> {text}")

        label = f"{source} ({page})" if page else source
        if label not in sources:
            sources.append(label)

    answer_parts = [
        "Based on the available documents, here are the most relevant passages:\n",
        "\n\n".join(passages),
        "\n\n*Note: This answer was generated using **extractive fallback mode** (no LLM). "
        "The passages above are quoted directly from the source documents. "
        "For AI-generated summaries, configure an LLM provider in Settings.*",
    ]

    return {
        "answer": "\n".join(answer_parts),
        "mode": "fallback_extractive",
        "model": "none",
        "sources": sources,
    }


# ── LLM-based generation ─────────────────────────────────


def _llm_answer(query: str, context_chunks: list[dict], system_prompt: str = "") -> dict:
    """Call the configured LLM with retrieved context."""
    provider = get_llm_provider()
    if provider == "openai":
        return _openai_answer(query, context_chunks, system_prompt)
    return _extractive_answer(query, context_chunks)


def _openai_answer(query: str, context_chunks: list[dict], system_prompt: str = "") -> dict:
    """Execute text generation via the official OpenAI Python SDK client."""
    api_key = get_openai_api_key()
    model = get_openai_model() or "gpt-3.5-turbo"

    # Check for missing API credentials
    if not api_key or api_key == "your-openai-api-key-here":
        fallback = _extractive_answer(query, context_chunks)
        fallback["answer"] = (
            "⚠️ **OpenAI Configuration Notice:** No valid `OPENAI_API_KEY` was detected in `.env`.\n\n"
            "To activate OpenAI synthesis, please set your key in the project root `.env` file:\n"
            "```env\nLLM_PROVIDER=openai\nOPENAI_API_KEY=sk-...\nOPENAI_MODEL=gpt-3.5-turbo\n```\n\n"
            f"Displaying extracted source context below:\n\n{fallback['answer']}"
        )
        fallback["error"] = "Missing OPENAI_API_KEY in environment."
        return fallback

    try:
        from openai import (
            OpenAI,
            AuthenticationError,
            RateLimitError,
            NotFoundError,
            APIConnectionError,
            OpenAIError,
        )
    except ImportError:
        fallback = _extractive_answer(query, context_chunks)
        fallback["answer"] = (
            "⚠️ The `openai` Python package is not installed in the environment.\n\n"
            f"{fallback['answer']}"
        )
        fallback["error"] = "Missing openai package."
        return fallback

    # Build context string
    context_parts = []
    sources = []
    for i, chunk in enumerate(context_chunks, 1):
        source = chunk.get("doc_name", "database")
        page = chunk.get("page_or_section", "")
        ref = f"[Source: {source}"
        if page:
            ref += f", {page}"
        ref += "]"
        context_parts.append(f"--- Document {i} {ref} ---\n{chunk.get('text', '')}")

        label = f"{source} ({page})" if page else source
        if label not in sources:
            sources.append(label)

    context_text = "\n\n".join(context_parts) if context_parts else "No specific documents or database records retrieved."

    default_system = (
        "You are a helpful Classroom AI Assistant. Answer the student's question "
        "based ONLY on the provided context documents. Prioritize the supplied educational context, "
        "avoid inventing facts, and clearly state when the context is insufficient. "
        "Always cite the source document names and page/section references. Never fabricate information."
    )

    messages = [
        {"role": "system", "content": system_prompt or default_system},
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query}"},
    ]

    try:
        client = OpenAI(api_key=api_key, timeout=25.0)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        answer_text = response.choices[0].message.content
        return {
            "answer": answer_text,
            "mode": "llm",
            "model": model,
            "sources": sources,
        }
    except AuthenticationError:
        error_msg = "Invalid or expired OpenAI API key. Please verify your OPENAI_API_KEY in .env."
    except RateLimitError:
        error_msg = "OpenAI rate limit or usage quota exceeded. Please check your OpenAI billing plan."
    except NotFoundError:
        error_msg = f"Configured model '{model}' was not found or is unavailable for your account."
    except APIConnectionError:
        error_msg = "Network connection to OpenAI API failed. Please check your internet connection."
    except OpenAIError as e:
        error_msg = f"OpenAI API error ({type(e).__name__})."
    except Exception as e:
        error_msg = f"Unexpected generation error ({type(e).__name__})."

    # Fall back safely to extractive mode
    fallback = _extractive_answer(query, context_chunks)
    fallback["answer"] = (
        f"⚠️ **LLM Generation Notice:** {error_msg}\n\n"
        f"Falling back to extractive mode:\n\n{fallback['answer']}"
    )
    fallback["error"] = error_msg
    fallback["sources"] = sources
    return fallback


# ── Public API ────────────────────────────────────────────


def generate_answer(
    query: str,
    context_chunks: list[dict],
    system_prompt: str = "",
    force_fallback: bool = False,
) -> dict:
    """
    Generate an answer for a query given retrieved context chunks.

    Returns dict:
        answer: str — the answer text
        mode: str — "llm" or "fallback_extractive"
        model: str — model name or "none"
        sources: list[str] — cited sources
    """
    if force_fallback or not llm_available():
        return _extractive_answer(query, context_chunks)
    return _llm_answer(query, context_chunks, system_prompt)


def compute_confidence(chunks: list[dict]) -> dict:
    """
    Compute a retrieval-quality indicator from chunk similarities.
    This is NOT an LLM confidence score — it reflects how well
    the query matched available documents.

    Returns: {score: float 0-1, label: str, explanation: str}
    """
    if not chunks:
        return {
            "score": 0.0,
            "label": "No Evidence",
            "explanation": "No matching documents were found for this query.",
        }

    similarities = [c.get("similarity", 0) for c in chunks]
    top_sim = max(similarities)
    avg_sim = sum(similarities) / len(similarities)

    # Weighted score: 60% top match, 40% average
    score = 0.6 * top_sim + 0.4 * avg_sim
    score = min(max(score, 0.0), 1.0)

    if score >= 0.7:
        label = "Strong Evidence"
        explanation = "Multiple highly relevant passages were found."
    elif score >= 0.45:
        label = "Moderate Evidence"
        explanation = "Some relevant passages were found, but coverage may be partial."
    elif score >= 0.2:
        label = "Weak Evidence"
        explanation = "Only loosely related passages were found. The answer may be incomplete."
    else:
        label = "Insufficient Evidence"
        explanation = "Very little relevant content was found. Consider rephrasing or uploading more documents."

    return {"score": round(score, 3), "label": label, "explanation": explanation}


__all__ = [
    "generate_answer",
    "compute_confidence",
    "get_llm_provider",
    "get_openai_api_key",
    "get_openai_model",
    "llm_available",
    "mask_api_key",
    "reload_config",
]
