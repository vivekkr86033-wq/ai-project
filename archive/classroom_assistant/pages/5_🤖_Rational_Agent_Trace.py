"""
5_🤖_Rational_Agent_Trace.py — Visualize the agent's decision process.
"""

import streamlit as st
from src.rational_agent import run_agent, INTENTS, ACTIONS


def render():
    st.markdown("## 🤖 Rational Agent Trace")
    st.markdown(
        "See exactly how the AI assistant makes decisions. "
        "Each query goes through a 6-step rational agent cycle."
    )

    # ── Agent Cycle Diagram ───────────────────────────────
    with st.expander("📊 Agent Cycle Overview", expanded=False):
        st.markdown("""
        ```
        ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
        │ 1. OBSERVE   │ ──▶ │ 2. CLASSIFY  │ ──▶ │ 3. IDENTIFY  │
        │   question   │     │   intent     │     │  goal &      │
        │   + context  │     │              │     │  constraints │
        └─────────────┘     └──────────────┘     └──────────────┘
               ▲                                         │
               │                                         ▼
        ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
        │ 6. RETURN    │ ◀── │ 5. EVALUATE  │ ◀── │ 4. SELECT    │
        │   answer +   │     │   evidence   │     │   action     │
        │   sources    │     │              │     │              │
        └─────────────┘     └──────────────┘     └──────────────┘
        ```
        """)

        st.markdown("**Available Intents:**")
        for intent_id, info in INTENTS.items():
            st.markdown(f"- `{intent_id}`: {info['description']}")

        st.markdown("**Available Actions:**")
        for action_id, desc in ACTIONS.items():
            st.markdown(f"- `{action_id}`: {desc}")

    # ── Interactive trace ─────────────────────────────────
    st.markdown("### 🔍 Run a Traced Query")

    query = st.text_input("Enter a question to trace:", placeholder="e.g., When is the AI201 final project due?")

    if st.button("▶️ Run Agent", type="primary") and query:
        with st.spinner("Running agent cycle…"):
            trace = run_agent(query, force_fallback=True)

        # Display each step
        st.markdown("---")

        # Step 1: Observe
        with st.expander("**Step 1: 👁️ Observe**", expanded=True):
            st.markdown(trace.observation)

        # Step 2: Classify
        with st.expander("**Step 2: 🏷️ Classify Intent**", expanded=True):
            st.markdown(f"**Classified Intent:** `{trace.classified_intent}`")
            st.markdown("**Intent Scores:**")
            scores = trace.intent_scores
            if scores:
                max_score = max(scores.values()) if scores.values() else 1
                for intent, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                    bar_width = score / max(max_score, 1)
                    st.progress(bar_width, text=f"{intent}: {score}")

        # Step 3: Identify Goal
        with st.expander("**Step 3: 🎯 Identify Goal & Constraints**", expanded=True):
            st.markdown(f"**Goal:** {trace.goal}")
            st.markdown("**Constraints:**")
            for c in trace.constraints:
                st.markdown(f"- {c}")

        # Step 4: Select Action
        with st.expander("**Step 4: ⚡ Select Action**", expanded=True):
            st.markdown(f"**Selected Action:** `{trace.selected_action}`")
            st.markdown(f"**Reason:** {trace.action_reason}")

        # Step 5: Evaluate Evidence
        with st.expander("**Step 5: 📊 Evaluate Evidence**", expanded=True):
            st.markdown(trace.evidence_summary)

            confidence = trace.confidence
            score = confidence.get("score", 0)
            label = confidence.get("label", "Unknown")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Confidence Score", f"{score:.3f}")
            with col2:
                st.metric("Confidence Label", label)

            if trace.retrieval_results:
                st.markdown(f"**Retrieved {len(trace.retrieval_results)} evidence chunks:**")
                for i, r in enumerate(trace.retrieval_results[:5], 1):
                    st.markdown(
                        f"  {i}. `{r['doc_name']}` ({r['page_or_section']}) — "
                        f"sim: {r['similarity']:.4f}"
                    )
                    st.caption(f"    {r['text_preview']}")

        # Step 6: Answer
        with st.expander("**Step 6: 💬 Return Answer**", expanded=True):
            st.markdown(trace.answer)
            if trace.sources:
                st.markdown("**Sources:**")
                for s in trace.sources:
                    st.markdown(f"- 📄 {s}")
            st.caption(f"Mode: `{trace.answer_mode}` | Time: {trace.elapsed_ms:.0f}ms")

        # Decision explanation
        st.markdown("---")
        st.markdown("### 📋 Decision Summary")
        st.info(trace.decision_explanation)

        # Save trace
        if "agent_traces" not in st.session_state:
            st.session_state.agent_traces = []
        st.session_state.agent_traces.append(trace.to_dict())

    # ── History of traces ─────────────────────────────────
    if st.session_state.get("agent_traces"):
        st.markdown("---")
        st.markdown("### 📜 Trace History (this session)")
        traces = st.session_state.agent_traces
        for i, t in enumerate(reversed(traces[-10:]), 1):
            st.caption(
                f"{i}. **\"{t['question'][:60]}…\"** → Intent: `{t['classified_intent']}` "
                f"→ Action: `{t['selected_action']}` → {t['elapsed_ms']:.0f}ms"
            )


render()
