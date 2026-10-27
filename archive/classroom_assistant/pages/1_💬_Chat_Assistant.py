"""
1_💬_Chat_Assistant.py — Main chat interface with RAG-powered Q&A.
"""

import streamlit as st
from src.rational_agent import run_agent
from src.llm_provider import compute_confidence


def render():
    st.markdown("## 💬 Chat Assistant")
    st.markdown(
        "Ask questions about courses, assignments, schedules, rules, or uploaded learning materials. "
        "The assistant uses a rational agent with RAG to find answers."
    )

    # Initialize conversation history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Mode selector
    col1, col2 = st.columns([3, 1])
    with col2:
        force_fallback = st.toggle(
            "Extractive Mode",
            value=True,
            help="When ON, answers are extracted directly from documents (no LLM API needed). "
                 "When OFF, uses the configured LLM if available.",
        )

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🎓" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("📚 Sources & Evidence", expanded=False):
                    confidence = msg.get("confidence", {})
                    score = confidence.get("score", 0)
                    label = confidence.get("label", "Unknown")
                    explanation = confidence.get("explanation", "")

                    # Confidence indicator
                    if score >= 0.7:
                        st.success(f"**{label}** — Score: {score:.2f}")
                    elif score >= 0.45:
                        st.warning(f"**{label}** — Score: {score:.2f}")
                    else:
                        st.error(f"**{label}** — Score: {score:.2f}")
                    st.caption(explanation)

                    st.markdown("**Sources:**")
                    for src in msg["sources"]:
                        st.markdown(f"- 📄 {src}")

                    st.caption(f"Mode: `{msg.get('mode', 'unknown')}` | Action: `{msg.get('action', 'unknown')}`")

    # Chat input
    user_input = st.chat_input("Ask a question about your courses…")

    if user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Run agent
        with st.chat_message("assistant", avatar="🎓"):
            with st.spinner("Thinking…"):
                trace = run_agent(user_input, force_fallback=force_fallback)

            st.markdown(trace.answer)

            # Source expander
            confidence = trace.confidence
            with st.expander("📚 Sources & Evidence", expanded=False):
                score = confidence.get("score", 0)
                label = confidence.get("label", "Unknown")
                explanation = confidence.get("explanation", "")

                if score >= 0.7:
                    st.success(f"**{label}** — Score: {score:.2f}")
                elif score >= 0.45:
                    st.warning(f"**{label}** — Score: {score:.2f}")
                else:
                    st.error(f"**{label}** — Score: {score:.2f}")
                st.caption(explanation)

                if trace.sources:
                    st.markdown("**Sources:**")
                    for src in trace.sources:
                        st.markdown(f"- 📄 {src}")

                st.caption(
                    f"Mode: `{trace.answer_mode}` | "
                    f"Action: `{trace.selected_action}` | "
                    f"Intent: `{trace.classified_intent}` | "
                    f"Time: {trace.elapsed_ms:.0f}ms"
                )

        # Save to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": trace.answer,
            "sources": trace.sources,
            "confidence": trace.confidence,
            "mode": trace.answer_mode,
            "action": trace.selected_action,
        })

        # Store latest trace for agent trace page
        if "agent_traces" not in st.session_state:
            st.session_state.agent_traces = []
        st.session_state.agent_traces.append(trace.to_dict())

    # Sidebar quick actions
    with st.sidebar:
        st.markdown("### 💡 Try asking:")
        examples = [
            "What is the schedule for CS101?",
            "What is the attendance policy?",
            "When is Assignment 1 due for CS101?",
            "What topics does AI201 cover?",
            "Can I eat in the computer lab?",
            "Who teaches Linear Algebra?",
        ]
        for ex in examples:
            st.caption(f"• {ex}")

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


render()
