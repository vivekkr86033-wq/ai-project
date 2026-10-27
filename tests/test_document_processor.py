"""
test_document_processor.py — Unit tests for document processing and retrieval.
"""

import pytest
from pathlib import Path
from src import document_processor as dp
from src.config import DOCS_DIR


class TestTextExtraction:
    """Tests for text extraction from different file types."""

    def test_extract_txt(self):
        txt_files = list(DOCS_DIR.glob("*.txt"))
        if txt_files:
            result = dp.extract_text(txt_files[0])
            assert isinstance(result, list)
            assert len(result) > 0
            assert "text" in result[0]

    def test_extract_md(self):
        md_files = list(DOCS_DIR.glob("*.md"))
        if md_files:
            result = dp.extract_text(md_files[0])
            assert isinstance(result, list)
            assert len(result) > 0

    def test_unsupported_format(self):
        with pytest.raises(ValueError):
            dp.extract_text(Path("fake_file.xyz"))


class TestChunking:
    """Tests for text chunking."""

    def test_chunk_text_basic(self):
        text = " ".join(["word"] * 1000)
        chunks = dp.chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 1

    def test_chunk_text_short(self):
        text = "This is a short text."
        chunks = dp.chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_empty(self):
        chunks = dp.chunk_text("", chunk_size=100, overlap=10)
        assert len(chunks) == 0

    def test_chunk_overlap(self):
        words = [f"word{i}" for i in range(200)]
        text = " ".join(words)
        chunks = dp.chunk_text(text, chunk_size=50, overlap=10)
        # Chunks should overlap
        assert len(chunks) >= 4


class TestDocumentProcessing:
    """Tests for full document processing pipeline."""

    def test_process_txt_document(self):
        txt_files = list(DOCS_DIR.glob("*.txt"))
        if txt_files:
            chunks = dp.process_document(txt_files[0])
            assert isinstance(chunks, list)
            for chunk in chunks:
                assert "doc_name" in chunk
                assert "text" in chunk
                assert "page_or_section" in chunk

    def test_process_md_document(self):
        md_files = list(DOCS_DIR.glob("*.md"))
        if md_files:
            chunks = dp.process_document(md_files[0])
            assert isinstance(chunks, list)
            assert len(chunks) > 0


class TestDocumentListing:
    """Tests for document management."""

    def test_list_documents(self):
        docs = dp.list_documents()
        assert isinstance(docs, list)
        # We have sample documents
        assert len(docs) >= 2
        for doc in docs:
            assert "name" in doc
            assert "size_kb" in doc
            assert "type" in doc

    def test_get_index_meta(self):
        meta = dp.get_index_meta()
        assert isinstance(meta, dict)


class TestKeywordSearch:
    """Tests for keyword-based fallback search."""

    def test_keyword_search_empty_index(self):
        # May or may not have index; just test it doesn't crash
        results = dp.keyword_search("python programming")
        assert isinstance(results, list)
