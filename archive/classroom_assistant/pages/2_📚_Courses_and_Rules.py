"""
2_📚_Courses_and_Rules.py — View and edit courses and classroom rules.
"""

import json
import streamlit as st
from src import knowledge_base as kb


def render():
    st.markdown("## 📚 Courses & Classroom Rules")

    tab1, tab2 = st.tabs(["📖 Courses", "📋 Classroom Rules"])

    # ── Courses Tab ───────────────────────────────────────
    with tab1:
        courses = kb.load_courses()

        if not courses:
            st.info("No courses loaded. Default courses will be created.")
            courses = kb.load_courses()

        for i, course in enumerate(courses):
            with st.expander(f"🎓 {course['name']} ({course['id']})", expanded=(i == 0)):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Description:** {course['description']}")
                    st.markdown(f"**Instructor:** {course.get('instructor', 'N/A')}")
                    st.markdown(f"**Schedule:** {course.get('schedule', 'N/A')}")

                with col2:
                    num_assignments = len(course.get("assignments", []))
                    num_topics = len(course.get("syllabus", []))
                    st.metric("Syllabus Topics", num_topics)
                    st.metric("Assignments", num_assignments)

                # Syllabus
                st.markdown("**📋 Syllabus:**")
                for topic in course.get("syllabus", []):
                    st.markdown(f"  - {topic}")

                # Assignments
                if course.get("assignments"):
                    st.markdown("**📝 Assignments:**")
                    for a in course["assignments"]:
                        deadline_str = a.get("deadline", "N/A")
                        st.markdown(
                            f"  - **{a['title']}** — Due: `{deadline_str}` "
                            f"— Max Marks: {a.get('max_marks', 'N/A')}\n"
                            f"    > {a['description']}"
                        )

        # Edit courses (JSON editor)
        st.markdown("---")
        st.markdown("### ✏️ Edit Course Data")
        st.caption("Edit the JSON below and click Save to update courses.")

        course_json = st.text_area(
            "Course Data (JSON)",
            value=json.dumps(courses, indent=2, ensure_ascii=False),
            height=300,
            key="course_editor",
        )

        col_save, col_reset = st.columns(2)
        with col_save:
            if st.button("💾 Save Changes", key="save_courses", use_container_width=True):
                try:
                    parsed = json.loads(course_json)
                    kb.save_courses(parsed)
                    st.success("✅ Courses updated successfully!")
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {e}")

        with col_reset:
            if st.button("🔄 Reset to Defaults", key="reset_courses", use_container_width=True):
                kb.save_courses(kb._DEFAULT_COURSES)
                st.success("✅ Courses reset to defaults.")
                st.rerun()

    # ── Rules Tab ─────────────────────────────────────────
    with tab2:
        rules = kb.load_rules()

        st.markdown("### Current Classroom Rules")
        for rule in rules:
            st.markdown(f"**{rule['id']}:** {rule['rule']}")

        st.markdown("---")
        st.markdown("### ✏️ Edit Rules")

        rules_json = st.text_area(
            "Rules Data (JSON)",
            value=json.dumps(rules, indent=2, ensure_ascii=False),
            height=250,
            key="rules_editor",
        )

        col_save_r, col_reset_r = st.columns(2)
        with col_save_r:
            if st.button("💾 Save Rules", key="save_rules", use_container_width=True):
                try:
                    parsed = json.loads(rules_json)
                    kb.save_rules(parsed)
                    st.success("✅ Rules updated successfully!")
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {e}")

        with col_reset_r:
            if st.button("🔄 Reset Rules", key="reset_rules", use_container_width=True):
                kb.save_rules(kb._DEFAULT_RULES)
                st.success("✅ Rules reset to defaults.")
                st.rerun()


render()
