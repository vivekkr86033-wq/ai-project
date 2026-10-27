"""
6_🧠_AI_Paradigms.py — AI Paradigms comparison and task recommender.
"""

import streamlit as st
from src.paradigms import (
    get_all_paradigms,
    get_comparison_table,
    get_task_recommendations,
    recommend_for_task,
)


def render():
    st.markdown("## 🧠 Modern AI Paradigms")
    st.markdown(
        "Compare major AI paradigms and understand which is best suited for different classroom tasks. "
        "All comparisons are **conceptual** — they reflect established knowledge, not measured benchmarks."
    )

    tab1, tab2 = st.tabs(["📊 Paradigm Comparison", "🎯 Task Recommender"])

    # ── Comparison Tab ────────────────────────────────────
    with tab1:
        paradigms = get_all_paradigms()

        # Overview table
        st.markdown("### Overview")
        table_data = get_comparison_table()
        cols = st.columns(len(table_data))

        # Display as cards
        for i, row in enumerate(table_data):
            # Cost badge color
            cost_color = {
                "Very Low": "🟢",
                "Low to Moderate": "🟡",
                "Moderate (retrieval) + LLM cost (generation)": "🟠",
                "High": "🔴",
                "Very High (training) / Moderate-High (inference)": "🔴",
                "Variable (depends on sub-components used)": "🔵",
            }.get(row["cost"], "⚪")

            with st.expander(f"**{row['name']}** {cost_color} {row['cost']}"):
                paradigm = paradigms[row["id"]]

                st.markdown("**Operating Principle:**")
                st.markdown(paradigm["operating_principle"])

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**✅ Strengths:**")
                    for s in paradigm["strengths"]:
                        st.markdown(f"- {s}")

                with col2:
                    st.markdown("**⚠️ Limitations:**")
                    for l in paradigm["limitations"]:
                        st.markdown(f"- {l}")

                st.markdown("**🏫 Classroom Applications:**")
                for app in paradigm["classroom_applications"]:
                    st.markdown(f"- {app}")

                st.markdown(f"**💰 Computational Cost:** {paradigm['computational_cost']}")

                st.info(f"**Recommendation:** {paradigm['recommendation']}")

        # Side-by-side comparison
        st.markdown("---")
        st.markdown("### Side-by-Side Comparison")

        paradigm_names = {pid: p["name"] for pid, p in paradigms.items()}
        col1, col2 = st.columns(2)
        with col1:
            p1 = st.selectbox("Paradigm A:", list(paradigm_names.values()), index=0, key="cmp_a")
        with col2:
            p2 = st.selectbox("Paradigm B:", list(paradigm_names.values()), index=4, key="cmp_b")

        # Find IDs
        p1_id = [k for k, v in paradigm_names.items() if v == p1][0]
        p2_id = [k for k, v in paradigm_names.items() if v == p2][0]

        p1_data = paradigms[p1_id]
        p2_data = paradigms[p2_id]

        comparison_cols = st.columns(2)
        with comparison_cols[0]:
            st.markdown(f"#### {p1_data['name']}")
            st.markdown(f"**Cost:** {p1_data['computational_cost']}")
            st.markdown(f"**Strengths:** {len(p1_data['strengths'])}")
            st.markdown(f"**Limitations:** {len(p1_data['limitations'])}")
            st.markdown(f"**Classroom Apps:** {len(p1_data['classroom_applications'])}")
            st.caption(p1_data["recommendation"])

        with comparison_cols[1]:
            st.markdown(f"#### {p2_data['name']}")
            st.markdown(f"**Cost:** {p2_data['computational_cost']}")
            st.markdown(f"**Strengths:** {len(p2_data['strengths'])}")
            st.markdown(f"**Limitations:** {len(p2_data['limitations'])}")
            st.markdown(f"**Classroom Apps:** {len(p2_data['classroom_applications'])}")
            st.caption(p2_data["recommendation"])

        st.caption(
            "⚠️ These comparisons are conceptual and based on established AI knowledge. "
            "They are NOT measured benchmark results from controlled experiments."
        )

    # ── Task Recommender Tab ──────────────────────────────
    with tab2:
        st.markdown("### 🎯 Task-Based Paradigm Selector")
        st.markdown("Select a classroom task to see which AI paradigm is most suitable.")

        tasks = get_task_recommendations()

        task_display = {tid: t["task"] for tid, t in tasks.items()}
        selected_task = st.selectbox(
            "Choose a task:",
            list(task_display.values()),
            key="task_selector",
        )

        # Find task ID
        selected_id = [tid for tid, t in tasks.items() if t["task"] == selected_task][0]

        result = recommend_for_task(selected_id)

        if result:
            st.markdown("---")

            # Recommendation card
            paradigm_info = result.get("paradigm_details", {})

            st.success(f"**Recommended Paradigm:** {paradigm_info.get('name', result['recommended_paradigm'])}")

            st.markdown("**Reasoning:**")
            st.markdown(result["reasoning"])

            st.markdown("**About this paradigm:**")
            st.markdown(paradigm_info.get("operating_principle", ""))

            if result.get("alternatives"):
                st.markdown("**Alternative paradigms to consider:**")
                for alt in result["alternatives"]:
                    alt_data = paradigms.get(alt, {})
                    st.markdown(f"- {alt_data.get('name', alt)}")

            st.caption(
                "These recommendations are based on general AI principles and task characteristics. "
                "Actual suitability depends on data availability, computational resources, and specific requirements."
            )

        # All tasks overview
        st.markdown("---")
        st.markdown("### All Task Recommendations")
        for tid, task in tasks.items():
            p_data = paradigms.get(task["recommended_paradigm"], {})
            st.markdown(
                f"- **{task['task']}** → "
                f"*{p_data.get('name', task['recommended_paradigm'])}*"
            )


render()
