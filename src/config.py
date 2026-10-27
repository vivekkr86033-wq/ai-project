"""
config.py — Central configuration for the Classroom AI Assistant & Smart Energy Planner.
Reads from .env file and provides typed constants and dynamic accessors for all settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env", override=True)
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# ── Paths ──────────────────────────────────────────────────
DATA_DIR = _project_root / "data"
DOCS_DIR = DATA_DIR / "documents"
INDEX_DIR = DATA_DIR / "index"
COURSE_DB_PATH = DATA_DIR / "courses.json"
RULES_DB_PATH = DATA_DIR / "rules.json"
TEST_DATA_DIR = _project_root / "tests" / "test_data"

# Ensure directories exist
for d in [DATA_DIR, DOCS_DIR, INDEX_DIR, TEST_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Base Environment Defaults ──────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower().strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo").strip()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))


# ── Dynamic accessors & security helpers ──────────────────
def reload_config() -> None:
    """Reload configuration from .env file into environment and module variables."""
    global LLM_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL
    global RETRIEVAL_TOP_K, CHUNK_SIZE, CHUNK_OVERLAP
    load_dotenv(_project_root / ".env", override=True)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower().strip()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo").strip()
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))


def get_llm_provider() -> str:
    """Return the currently configured LLM provider name (e.g. 'openai' or 'none')."""
    return os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower().strip()


def get_openai_api_key() -> str:
    """Return the OpenAI API key securely from environment."""
    return os.getenv("OPENAI_API_KEY", OPENAI_API_KEY).strip()


def get_openai_model() -> str:
    """Return the configured OpenAI model name."""
    return os.getenv("OPENAI_MODEL", OPENAI_MODEL).strip()


def mask_api_key(key: str | None = None) -> str:
    """
    Safely mask an API key for UI/logging display. Never reveals the full secret.
    """
    target = key if key is not None else get_openai_api_key()
    if not target or target == "your-openai-api-key-here":
        return "Not configured"
    if len(target) <= 8:
        return "••••••••"
    return f"{target[:3]}••••{target[-4:]}"


def llm_available() -> bool:
    """Return True if a real LLM provider is configured with a valid key."""
    provider = get_llm_provider()
    key = get_openai_api_key()
    if provider == "openai" and bool(key) and key != "your-openai-api-key-here":
        return True
    return False


__all__ = [
    "DATA_DIR",
    "DOCS_DIR",
    "INDEX_DIR",
    "COURSE_DB_PATH",
    "RULES_DB_PATH",
    "TEST_DATA_DIR",
    "LLM_PROVIDER",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "EMBEDDING_MODEL",
    "RETRIEVAL_TOP_K",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "get_llm_provider",
    "get_openai_api_key",
    "get_openai_model",
    "mask_api_key",
    "llm_available",
    "reload_config",
]
