"""
7_⚙️_Evaluation_and_Settings.py — Evaluation runner and app settings.
"""

import streamlit as st
import json
from src.config import (
    LLM_PROVIDER, OPENAI_MODEL, EMBEDDING_MODEL,
    RETRIEVAL_TOP_K, CHUNK_SIZE, CHUNK_OVERLAP, llm_available,
)
from src.evaluation import (
    run_full_evaluation,
    evaluate_intent_classification,
    evaluate_database_lookups,
    evaluate_source_attribution,
    evaluate_missing_evidence_handling,
    evaluate_retrieval_recall,
    TEST_DATASET,
)


def render():
    st.markdown("## ⚙️ Evaluation & Settings")

    tab1, tab2, tab3 = st.tabs(["📊 Evaluation", "⚙️ Settings", "📋 Test Dataset"])

    # ── Evaluation Tab ────────────────────────────────────
    with tab1:
        st.markdown("### 📊 System Evaluation")
        st.markdown(
            "Run tests to evaluate intent classification, database lookups, "
            "source attribution, and missing-evidence handling. "
            "All metrics are computed from actual test runs — no invented scores."
        )

        col1, col2 = st.columns([1, 2])
        with col1:
            run_all = st.button("▶️ Run Full Evaluation", type="primary", use_container_width=True)
        with col2:
            st.caption(
                "This runs all test cases and computes accuracy metrics. "
                "Takes a few seconds."
            )

        if run_all:
            with st.spinner("Running evaluation suite…"):
                results = run_full_evaluation()

            st.success(f"✅ Evaluation complete in {results['elapsed_seconds']:.1f}s")

            # Summary metrics
            st.markdown("### Results Summary")

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                ic = results["intent_classification"]
                st.metric(
                    "Intent Accuracy",
                    f"{ic['accuracy']:.0%}",
                    help=f"{ic['correct']}/{ic['total']} correct",
                )
            with m2:
                db = results["database_lookups"]
                st.metric(
                    "DB Lookup Accuracy",
                    f"{db['accuracy']:.0%}",
                    help=f"{db['correct']}/{db['total']} correct",
                )
            with m3:
                sa = results["source_attribution"]
                st.metric(
                    "Source Attribution",
                    f"{sa['rate']:.0%}",
                    help=f"{sa['attributed']}/{sa['total']} attributed",
                )
            with m4:
                me = results["missing_evidence"]
                st.metric(
                    "Graceful Handling",
                    f"{me['rate']:.0%}",
                    help=f"{me['graceful']}/{me['total']} graceful",
                )

            # Retrieval recall
            rr = results["retrieval_recall"]
            if rr.get("status") == "skipped":
                st.info(f"📝 Retrieval Recall: {rr['reason']}")
            else:
                st.metric(
                    f"Retrieval Recall@{rr['metric'].split('@')[1]}",
                    f"{rr['recall']:.0%}",
                )

            # Detailed results
            st.markdown("---")
            st.markdown("### Detailed Results")

            with st.expander("🏷️ Intent Classification Details"):
                for d in ic["details"]:
                    icon = "✅" if d["correct"] else "❌"
                    st.markdown(
                        f"{icon} **{d['id']}**: \"{d['question']}\" → "
                        f"Expected: `{d['expected']}`, Got: `{d['predicted']}`"
                    )

            with st.expander("🔍 Database Lookup Details"):
                for d in db["details"]:
                    icon = "✅" if d["correct"] else "❌"
                    st.markdown(
                        f"{icon} **{d['id']}**: \"{d['question']}\""
                    )
                    if d.get("missing_terms"):
                        st.caption(f"  Missing: {d['missing_terms']}")

            with st.expander("📚 Source Attribution Details"):
                for d in sa["details"]:
                    icon = "✅" if d["has_attribution"] else "❌"
                    st.markdown(
                        f"{icon} **{d['id']}**: Sources: {d['actual_sources'][:3]}"
                    )

            with st.expander("⚠️ Missing Evidence Details"):
                for d in me["details"]:
                    icon = "✅" if d["graceful"] else "❌"
                    st.markdown(
                        f"{icon} \"{d['question']}\" → "
                        f"Confidence: {d['confidence_label']} ({d['confidence_score']:.2f})"
                    )

            # Raw JSON
            with st.expander("📄 Raw Results (JSON)"):
                st.json(results)

        # Individual test buttons
        st.markdown("---")
        st.markdown("### Run Individual Tests")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏷️ Intent Classification", use_container_width=True):
                with st.spinner("Testing…"):
                    result = evaluate_intent_classification()
                st.metric("Accuracy", f"{result['accuracy']:.0%}")
                for d in result["details"]:
                    icon = "✅" if d["correct"] else "❌"
                    st.caption(f"{icon} {d['id']}: {d['predicted']}")

        with col2:
            if st.button("📚 Source Attribution", use_container_width=True):
                with st.spinner("Testing…"):
                    result = evaluate_source_attribution()
                st.metric("Attribution Rate", f"{result['rate']:.0%}")

        with col3:
            if st.button("⚠️ Missing Evidence", use_container_width=True):
                with st.spinner("Testing…"):
                    result = evaluate_missing_evidence_handling()
                st.metric("Graceful Rate", f"{result['rate']:.0%}")

    # ── Settings Tab ──────────────────────────────────────
    with tab2:
        st.markdown("### ⚙️ Application Settings")

        st.markdown("#### LLM Configuration")

        status_col1, status_col2 = st.columns(2)
        with status_col1:
            if llm_available():
                st.success(f"✅ LLM Provider: **{LLM_PROVIDER}** (Model: {OPENAI_MODEL})")
            else:
                st.warning("⚠️ No LLM configured — using **extractive fallback** mode")
                st.caption("Answers are extracted directly from documents. No API calls are made.")

        with status_col2:
            st.info(f"Embedding Model: `{EMBEDDING_MODEL}`")

        st.markdown("#### Current Settings")
        settings_data = {
            "LLM Provider": LLM_PROVIDER,
            "LLM Model": OPENAI_MODEL if LLM_PROVIDER == "openai" else "N/A",
            "LLM Available": str(llm_available()),
            "Embedding Model": EMBEDDING_MODEL,
            "Retrieval Top-K": str(RETRIEVAL_TOP_K),
            "Chunk Size (words)": str(CHUNK_SIZE),
            "Chunk Overlap (words)": str(CHUNK_OVERLAP),
        }

        for key, val in settings_data.items():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"**{key}:**")
            with col2:
                st.code(val)

        st.markdown("---")
        st.markdown("#### How to Configure")
        st.markdown("""
        1. Copy `.env.example` to `.env` in the project root
        2. Edit the values:
           - Set `LLM_PROVIDER=openai` for OpenAI integration
           - Set `OPENAI_API_KEY=your-key-here`
           - Adjust `RETRIEVAL_TOP_K`, `CHUNK_SIZE`, etc. as needed
        3. Restart the Streamlit app

        **The app works fully without any API key** using extractive fallback mode,
        which quotes relevant passages directly from source documents.
        """)

        st.markdown("#### Privacy Notice")
        st.info(
            "🔒 When LLM_PROVIDER=none (default), **no data leaves your machine**. "
            "All processing is done locally using sentence-transformers. "
            "When using OpenAI, query text and retrieved context are sent to the API. "
            "No private student information is uploaded without your authorization."
        )

    # ── Test Dataset Tab ──────────────────────────────────
    with tab3:
        st.markdown("### 📋 Test Dataset")
        st.markdown(f"**{len(TEST_DATASET)} test cases** for evaluation.")

        for test in TEST_DATASET:
            with st.expander(f"**{test['id']}**: {test['question']}"):
                st.markdown(f"**Expected Intent:** `{test['expected_intent']}`")
                st.markdown(f"**Expected Action:** `{test['expected_action']}`")
                st.markdown(f"**Category:** `{test['category']}`")
                if test["expected_answer_contains"]:
                    st.markdown(f"**Expected Terms:** {test['expected_answer_contains']}")
                st.markdown(f"**Source:** {test['supporting_source']}")


render()
