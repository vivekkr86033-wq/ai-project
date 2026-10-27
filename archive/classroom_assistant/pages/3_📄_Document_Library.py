"""
3_📄_Document_Library.py — Upload, manage, and index learning documents.
"""

import streamlit as st
from pathlib import Path
from src import document_processor as dp
from src.config import DOCS_DIR


def render():
    st.markdown("## 📄 Document Library")
    st.markdown(
        "Upload PDF, TXT, or Markdown learning documents. "
        "Documents are chunked, embedded, and indexed for semantic search."
    )

    # ── Upload section ────────────────────────────────────
    st.markdown("### ⬆️ Upload Documents")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=["pdf", "txt", "md", "markdown"],
        accept_multiple_files=True,
        key="doc_uploader",
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            save_path = DOCS_DIR / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ Uploaded: **{uploaded_file.name}**")

    # ── Document list ─────────────────────────────────────
    st.markdown("### 📂 Uploaded Documents")

    docs = dp.list_documents()

    if docs:
        for doc in docs:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                icon = {"pdf": "📕", ".txt": "📄", ".md": "📝"}.get(doc["type"], "📄")
                # Fix icon lookup
                icon = "📕" if doc["type"] == ".pdf" else ("📝" if doc["type"] in (".md", ".markdown") else "📄")
                st.markdown(f"{icon} **{doc['name']}**")
            with col2:
                st.caption(f"{doc['size_kb']} KB")
            with col3:
                st.caption(doc["type"].upper())
            with col4:
                if st.button("🗑️", key=f"del_{doc['name']}", help=f"Delete {doc['name']}"):
                    dp.delete_document(doc["name"])
                    st.success(f"Deleted {doc['name']}")
                    st.rerun()
    else:
        st.info(
            "No documents uploaded yet. Upload PDF, TXT, or Markdown files above "
            "to build the knowledge base."
        )

    # ── Index management ──────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔍 Index Management")

    meta = dp.get_index_meta()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 Indexed Documents", meta.get("num_docs", 0))
    with col2:
        st.metric("🧩 Total Chunks", meta.get("num_chunks", 0))
    with col3:
        indexed_names = meta.get("doc_names", [])
        st.metric("📚 Document Names", len(indexed_names))

    if indexed_names:
        with st.expander("Indexed documents"):
            for name in indexed_names:
                st.markdown(f"- {name}")

    col_build, col_info = st.columns([1, 2])
    with col_build:
        if st.button("🔨 Build / Rebuild Index", use_container_width=True, type="primary"):
            if not docs:
                st.warning("No documents to index. Upload documents first.")
            else:
                progress_bar = st.progress(0, text="Indexing documents…")
                status_text = st.empty()

                def progress_cb(current, total, name):
                    progress_bar.progress(
                        current / total,
                        text=f"Processing {name} ({current}/{total})"
                    )
                    status_text.caption(f"Extracting and embedding: {name}")

                try:
                    result = dp.build_index(progress_callback=progress_cb)
                    progress_bar.progress(1.0, text="Done!")
                    st.success(
                        f"✅ Index built: {result['num_docs']} documents, "
                        f"{result['num_chunks']} chunks"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Indexing failed: {e}")

    with col_info:
        st.caption(
            "Building the index extracts text from all documents, splits into chunks, "
            "computes embeddings using sentence-transformers, and stores the index for "
            "fast semantic retrieval."
        )

    # ── Test search ───────────────────────────────────────
    if meta.get("num_chunks", 0) > 0:
        st.markdown("---")
        st.markdown("### 🔎 Test Document Search")

        search_query = st.text_input("Enter a search query to test retrieval:", key="doc_search")

        if search_query:
            with st.spinner("Searching…"):
                results = dp.retrieve(search_query)

            if results:
                st.markdown(f"**Found {len(results)} results:**")
                for i, r in enumerate(results, 1):
                    with st.expander(
                        f"Result {i}: {r['doc_name']} — "
                        f"Similarity: {r['similarity']:.4f}"
                    ):
                        st.caption(f"Page/Section: {r.get('page_or_section', 'N/A')}")
                        st.markdown(r["text"][:500])
            else:
                st.info("No results found. Try a different query.")


render()
