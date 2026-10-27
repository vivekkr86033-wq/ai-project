"""
document_processor.py — Parse, chunk, embed, and index uploaded documents.

Supports PDF, TXT, and Markdown files. Uses sentence-transformers for
embedding and a simple numpy-based cosine-similarity index.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Optional

import numpy as np

from src.config import DOCS_DIR, INDEX_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, RETRIEVAL_TOP_K

# ── Lazy model loading ────────────────────────────────────

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


# ── Text extraction ───────────────────────────────────────

def extract_text_from_pdf(path: Path) -> list[dict]:
    """Return list of {'page': int, 'text': str} dicts."""
    from PyPDF2 import PdfReader
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": i + 1, "text": text})
    return pages


def extract_text_from_txt(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [{"page": 1, "text": text}]


def extract_text_from_md(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    # Split by top-level headings as "sections"
    sections = re.split(r"(?m)^(#{1,2}\s+.+)$", text)
    results = []
    current_section = "Introduction"
    for i, sec in enumerate(sections):
        stripped = sec.strip()
        if re.match(r"^#{1,2}\s+", stripped):
            current_section = stripped.lstrip("#").strip()
        elif stripped:
            results.append({"page": current_section, "text": stripped})
    if not results and text.strip():
        results.append({"page": "Full Document", "text": text})
    return results


def extract_text(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    elif suffix == ".txt":
        return extract_text_from_txt(path)
    elif suffix in (".md", ".markdown"):
        return extract_text_from_md(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


# ── Chunking ──────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping word-level chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ── Document processing ──────────────────────────────────

def process_document(path: Path) -> list[dict]:
    """Extract text, chunk it, and return metadata-enriched chunks."""
    pages = extract_text(path)
    doc_chunks = []
    for page_info in pages:
        page_label = page_info["page"]
        text = page_info["text"]
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            doc_chunks.append({
                "doc_name": path.name,
                "doc_path": str(path),
                "page_or_section": str(page_label),
                "chunk_index": i,
                "text": chunk,
            })
    return doc_chunks


# ── Index management ─────────────────────────────────────

_CHUNKS_FILE = INDEX_DIR / "chunks.json"
_EMBEDDINGS_FILE = INDEX_DIR / "embeddings.npy"
_META_FILE = INDEX_DIR / "index_meta.json"


def _file_hash(path: Path) -> str:
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_index(progress_callback=None) -> dict:
    """
    Scan DOCS_DIR, process all supported files, compute embeddings,
    and save index to disk.

    Returns summary dict: {num_docs, num_chunks, doc_names}.
    """
    supported = {".pdf", ".txt", ".md", ".markdown"}
    doc_files = [f for f in DOCS_DIR.iterdir() if f.suffix.lower() in supported]

    all_chunks: list[dict] = []
    doc_names = []

    for i, doc_path in enumerate(doc_files):
        doc_names.append(doc_path.name)
        chunks = process_document(doc_path)
        all_chunks.extend(chunks)
        if progress_callback:
            progress_callback(i + 1, len(doc_files), doc_path.name)

    if not all_chunks:
        # Save empty index
        _save_index([], np.array([]))
        return {"num_docs": 0, "num_chunks": 0, "doc_names": []}

    # Compute embeddings
    model = _get_model()
    texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    _save_index(all_chunks, embeddings)

    meta = {"num_docs": len(doc_names), "num_chunks": len(all_chunks), "doc_names": doc_names}
    with open(_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta


def _save_index(chunks: list[dict], embeddings: np.ndarray) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with open(_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    if embeddings.size > 0:
        np.save(str(_EMBEDDINGS_FILE), embeddings)
    elif _EMBEDDINGS_FILE.exists():
        _EMBEDDINGS_FILE.unlink()


def load_index() -> tuple[list[dict], Optional[np.ndarray]]:
    """Load the chunk store and embedding matrix from disk."""
    if not _CHUNKS_FILE.exists():
        return [], None
    with open(_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    emb = None
    if _EMBEDDINGS_FILE.exists():
        emb = np.load(str(_EMBEDDINGS_FILE))
    return chunks, emb


def get_index_meta() -> dict:
    if _META_FILE.exists():
        with open(_META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"num_docs": 0, "num_chunks": 0, "doc_names": []}


# ── Retrieval ─────────────────────────────────────────────

def retrieve(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[dict]:
    """
    Retrieve the top-k most relevant chunks for a query.
    Returns list of dicts with chunk metadata + similarity score.
    """
    chunks, embeddings = load_index()
    if not chunks or embeddings is None or embeddings.size == 0:
        return []

    model = _get_model()
    query_emb = model.encode([query], convert_to_numpy=True)[0]

    # Cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normed = embeddings / norms

    q_norm = np.linalg.norm(query_emb)
    if q_norm > 0:
        query_normed = query_emb / q_norm
    else:
        query_normed = query_emb

    similarities = normed @ query_normed
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        chunk = chunks[idx].copy()
        chunk["similarity"] = float(similarities[idx])
        results.append(chunk)
    return results


def keyword_search(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[dict]:
    """
    Simple keyword-based fallback retrieval (no embeddings needed).
    Uses term overlap scoring.
    """
    chunks, _ = load_index()
    if not chunks:
        return []

    query_terms = set(query.lower().split())
    scored = []
    for chunk in chunks:
        text_terms = set(chunk["text"].lower().split())
        overlap = len(query_terms & text_terms)
        if overlap > 0:
            score = overlap / max(len(query_terms), 1)
            c = chunk.copy()
            c["similarity"] = round(score, 4)
            scored.append(c)

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def list_documents() -> list[dict]:
    """List all documents in DOCS_DIR with metadata."""
    supported = {".pdf", ".txt", ".md", ".markdown"}
    docs = []
    for f in sorted(DOCS_DIR.iterdir()):
        if f.suffix.lower() in supported:
            docs.append({
                "name": f.name,
                "path": str(f),
                "size_kb": round(f.stat().st_size / 1024, 1),
                "type": f.suffix.lower(),
            })
    return docs


def delete_document(filename: str) -> bool:
    """Delete a document from DOCS_DIR."""
    path = DOCS_DIR / filename
    if path.exists():
        path.unlink()
        return True
    return False
