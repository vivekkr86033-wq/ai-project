"""
4_🎯_Learning_Workflows.py — Interactive learning support workflows.
"""

import streamlit as st
from src import knowledge_base as kb
from src.learning_workflows import (
    explain_topic,
    generate_quiz,
    create_revision_plan,
    find_relevant_documents,
    explain_assignment,
    refer_to_teacher,
)


def render():
    st.markdown("## 🎯 Learning Workflows")
    st.markdown("Interactive tools to support your learning journey.")

    workflow = st.selectbox(
        "Choose a workflow:",
        [
            "📖 Topic Explanation",
            "📝 Practice Quiz",
            "📅 Revision Plan",
            "🔍 Find Documents",
            "📋 Assignment Help",
            "👨‍🏫 Ask a Teacher",
        ],
        key="workflow_selector",
    )

    courses = kb.load_courses()
    course_options = {c["name"]: c["id"] for c in courses}

    st.markdown("---")

    # ── Topic Explanation ─────────────────────────────────
    if workflow == "📖 Topic Explanation":
        st.markdown("### 📖 Explain a Topic")
        st.caption("Get a structured explanation at your chosen level.")

        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("Topic to explain:", placeholder="e.g., Sorting Algorithms")
        with col2:
            level = st.select_slider(
                "Complexity level:",
                options=["beginner", "intermediate", "advanced"],
                value="beginner",
            )

        selected_course = st.selectbox(
            "Filter by course (optional):",
            ["All Courses"] + list(course_options.keys()),
            key="explain_course",
        )
        course_id = course_options.get(selected_course)

        if st.button("🔍 Explain", type="primary") and topic:
            with st.spinner("Generating explanation…"):
                result = explain_topic(topic, level, course_id)

            if result.get("syllabus_match"):
                st.success(f"Topic found in syllabus: {', '.join(result['syllabus_match'])}")
            else:
                st.warning("Topic not found in any loaded syllabus.")

            st.markdown(result["explanation"])

            if result.get("document_sources"):
                st.caption(f"📚 Sources: {', '.join(set(result['document_sources']))}")

    # ── Practice Quiz ─────────────────────────────────────
    elif workflow == "📝 Practice Quiz":
        st.markdown("### 📝 Generate Practice Quiz")

        col1, col2 = st.columns(2)
        with col1:
            quiz_topic = st.text_input("Topic:", placeholder="e.g., Data Structures")
        with col2:
            num_q = st.slider("Number of questions:", 3, 7, 5)

        selected_course = st.selectbox(
            "Filter by course (optional):",
            ["All Courses"] + list(course_options.keys()),
            key="quiz_course",
        )
        course_id = course_options.get(selected_course)

        if st.button("📝 Generate Quiz", type="primary") and quiz_topic:
            with st.spinner("Creating quiz…"):
                result = generate_quiz(quiz_topic, num_q, course_id)

            st.markdown(f"**Quiz: {quiz_topic}** — {result['num_questions']} questions")

            for q in result["questions"]:
                with st.expander(f"Question {q['number']} ({q['type'].replace('_', ' ').title()})"):
                    st.markdown(q["question"])
                    st.caption(f"Source topic: {q['source_topic']}")

            if result.get("sources"):
                st.caption(f"📚 Based on: {', '.join(result['sources'])}")
            st.info(result.get("note", ""))

    # ── Revision Plan ─────────────────────────────────────
    elif workflow == "📅 Revision Plan":
        st.markdown("### 📅 Create Revision Plan")

        col1, col2 = st.columns(2)
        with col1:
            selected_course = st.selectbox(
                "Select course:",
                list(course_options.keys()),
                key="revision_course",
            )
            course_id = course_options.get(selected_course)
        with col2:
            exam_date = st.date_input("Exam date:")

        if st.button("📅 Generate Plan", type="primary"):
            with st.spinner("Creating revision plan…"):
                result = create_revision_plan(
                    course_id=course_id,
                    exam_date=exam_date.strftime("%Y-%m-%d"),
                )

            if result.get("error"):
                st.error(result["error"])
            else:
                st.success(
                    f"Plan created: {result['total_topics']} topics over "
                    f"{result['days_available']} days until {result['exam_date']}"
                )

                for day in result["plan"]:
                    with st.expander(
                        f"Day {day['day_number']} — {day['date']} ({day['activity']})"
                    ):
                        for topic in day["topics"]:
                            st.markdown(f"- {topic}")

                st.markdown("**💡 Study Tips:**")
                for tip in result.get("tips", []):
                    st.markdown(f"- {tip}")

    # ── Find Documents ────────────────────────────────────
    elif workflow == "🔍 Find Documents":
        st.markdown("### 🔍 Find Relevant Learning Documents")

        search_query = st.text_input("What are you looking for?", placeholder="e.g., neural networks tutorial")

        if st.button("🔍 Search", type="primary") and search_query:
            with st.spinner("Searching…"):
                result = find_relevant_documents(search_query)

            if result["found"]:
                st.success(f"Found {result['total_matches']} relevant passages in documents.")
                for doc_name, sections in result["documents"].items():
                    with st.expander(f"📄 {doc_name} ({len(sections)} matches)"):
                        for sec in sections:
                            st.markdown(f"**Section:** {sec['section']} — Relevance: {sec['relevance']}")
                            st.markdown(f"> {sec['preview']}…")
                            st.markdown("---")
            else:
                st.warning(result.get("suggestion", "No results found."))
                st.info(f"Documents in library: {result['available_documents']}")

    # ── Assignment Help ───────────────────────────────────
    elif workflow == "📋 Assignment Help":
        st.markdown("### 📋 Assignment Guidance")
        st.caption("Get help understanding assignment requirements.")

        selected_course = st.selectbox(
            "Select course:",
            list(course_options.keys()),
            key="assignment_course",
        )
        course_id = course_options.get(selected_course)

        course = kb.get_course_by_id(course_id)
        assignments = course.get("assignments", []) if course else []
        assignment_names = ["All Assignments"] + [a["title"] for a in assignments]

        selected_assignment = st.selectbox(
            "Select assignment:",
            assignment_names,
            key="assignment_select",
        )

        if st.button("📋 Get Guidance", type="primary"):
            title = "" if selected_assignment == "All Assignments" else selected_assignment
            with st.spinner("Loading…"):
                result = explain_assignment(course_id, title)

            if result.get("error"):
                st.error(result["error"])
                if result.get("available_assignments"):
                    st.info(f"Available: {', '.join(result['available_assignments'])}")
            else:
                for a in result.get("assignments", []):
                    with st.expander(f"📝 {a['title']}", expanded=True):
                        st.markdown(f"**Description:** {a['description']}")
                        st.markdown(f"**Deadline:** `{a['deadline']}`")
                        st.markdown(f"**Max Marks:** {a['max_marks']}")
                        st.markdown("**Guidance:**")
                        for g in a["guidance"]:
                            st.markdown(f"- {g}")

                st.warning(result.get("note", ""))

    # ── Refer to Teacher ──────────────────────────────────
    elif workflow == "👨‍🏫 Ask a Teacher":
        st.markdown("### 👨‍🏫 Refer to Teacher")
        st.caption("For administrative questions that require human assistance.")

        question = st.text_area(
            "What would you like to ask?",
            placeholder="e.g., Can I get an extension on my assignment?",
        )

        if st.button("📨 Get Referral Info", type="primary") and question:
            result = refer_to_teacher(question)

            st.info(result["message"])

            st.markdown("**👨‍🏫 Instructor Contact Information:**")
            for instr in result["instructors"]:
                st.markdown(f"- **{instr['instructor']}** — {instr['course']} — {instr['schedule']}")

            st.markdown("**💡 Suggestions:**")
            for s in result["suggestions"]:
                st.markdown(f"- {s}")


render()
