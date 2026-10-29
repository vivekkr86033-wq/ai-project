"""
config.py — Central configuration for the Classroom AI Assistant & Smart Energy Planner.
Reads from .env file and provides typed constants and dynamic accessors for all settings.
"""

import os
import re
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))


# ── Dynamic accessors & security helpers ──────────────────
def reload_config() -> None:
    """Reload configuration from .env file into environment and module variables."""
    global LLM_PROVIDER, OPENAI_API_KEY, OPENAI_MODEL, GEMINI_API_KEY, GEMINI_MODEL, EMBEDDING_MODEL
    global RETRIEVAL_TOP_K, CHUNK_SIZE, CHUNK_OVERLAP
    load_dotenv(_project_root / ".env", override=True)
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower().strip()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo").strip()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))


SUPPORTED_PROVIDERS = ("gemini", "openai", "none")


def get_llm_provider() -> str:
    """Return the currently configured LLM provider name (e.g. 'gemini', 'openai', or 'none')."""
    return os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower().strip()


def validate_provider(provider: str | None = None) -> tuple[bool, str]:
    """Validate that the configured LLM provider is officially supported."""
    p = provider if provider is not None else get_llm_provider()
    if p in SUPPORTED_PROVIDERS:
        return True, ""
    return False, f"Unsupported LLM provider '{p}'. Supported providers are: {', '.join(SUPPORTED_PROVIDERS)}."


def get_openai_api_key() -> str:
    """Return the OpenAI API key securely from environment."""
    return os.getenv("OPENAI_API_KEY", OPENAI_API_KEY).strip()


def get_openai_model() -> str:
    """Return the configured OpenAI model name."""
    return os.getenv("OPENAI_MODEL", OPENAI_MODEL).strip()


def get_gemini_api_key() -> str:
    """Return the Google Gemini API key securely from environment, sanitizing typos/quotes."""
    key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY).strip()
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1].strip()
    # Auto-sanitize accidental paste typo where a stray 'P' is placed before 'AQ.'
    if key.startswith("PAQ.") and len(key) == 54:
        key = key[1:]
    return key


def get_gemini_model() -> str:
    """Return the configured Gemini model name."""
    model = os.getenv("GEMINI_MODEL", GEMINI_MODEL).strip()
    return model or "gemini-3.8-flash"


def get_active_model() -> str:
    """Return the model name for the active LLM provider."""
    provider = get_llm_provider()
    if provider == "gemini":
        return get_gemini_model()
    elif provider == "openai":
        return get_openai_model()
    return "none"


def get_active_api_key() -> str:
    """Return the API key for the active LLM provider."""
    provider = get_llm_provider()
    if provider == "gemini":
        return get_gemini_api_key()
    elif provider == "openai":
        return get_openai_api_key()
    return ""


def mask_api_key(key: str | None = None, provider: str | None = None) -> str:
    """
    Safely mask an API key for UI/logging display. Never reveals the full secret.
    """
    if key is not None:
        target = key
    elif provider == "gemini":
        target = get_gemini_api_key()
    elif provider == "openai":
        target = get_openai_api_key()
    else:
        # Default for backwards compatibility
        target = get_openai_api_key()

    if not target or target in ("your-openai-api-key-here", "your-gemini-api-key-here"):
        return "Not configured"
    if len(target) <= 8:
        return "••••••••"
    return f"{target[:3]}••••{target[-4:]}"


def get_active_masked_api_key() -> str:
    """Return the safely masked API key for the currently active provider."""
    provider = get_llm_provider()
    if provider == "gemini":
        return mask_api_key(get_gemini_api_key())
    elif provider == "openai":
        return mask_api_key(get_openai_api_key())
    return "Not configured"


def llm_available() -> bool:
    """Return True if a real LLM provider is configured with a valid key."""
    provider = get_llm_provider()
    if provider == "gemini":
        key = get_gemini_api_key()
        return bool(key) and key != "your-gemini-api-key-here"
    elif provider == "openai":
        key = get_openai_api_key()
        return bool(key) and key != "your-openai-api-key-here"
    return False


def check_gemini_connection() -> tuple[bool, str]:
    """
    Test live connectivity to the configured Gemini model.
    Returns: (success: bool, sanitized_message: str)
    Guarantees API keys are never exposed in return strings.
    """
    api_key = get_gemini_api_key()
    model = get_gemini_model() or "gemini-3.8-flash"
    if not api_key:
        return False, "GEMINI_API_KEY is not configured in .env."

    try:
        from google import genai
        client = genai.Client(api_key=api_key, http_options={"timeout": 10000})
        try:
            res = client.models.generate_content(
                model=model,
                contents="Say 'OK'",
            )
            if res.text:
                return True, f"Connection verified: Model '{model}' responded successfully."
            return False, f"Model '{model}' returned an empty response."
        except Exception as e_model:
            err_m = str(e_model)
            if "503" in err_m or "UNAVAILABLE" in err_m:
                try:
                    alt_res = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents="Say 'OK'",
                    )
                    if alt_res.text:
                        return True, f"Model '{model}' is experiencing temporary high demand (503). Automatic model fallback to 'gemini-3.5-flash' is ACTIVE and responding."
                except Exception:
                    pass
            raise e_model
    except Exception as e:
        err_text = str(e)
        extracted = ""
        m = re.search(r"'message':\s*'([^']+)'", err_text)
        if m:
            extracted = m.group(1)
        elif hasattr(e, "message"):
            extracted = getattr(e, "message", "")
        else:
            extracted = err_text[:200]
        sanitized = re.sub(r"AQ\.[0-9A-Za-z\-_]{40,}", "[REDACTED]", extracted)
        sanitized = re.sub(r"AIza[0-9A-Za-z\-_]{35}", "[REDACTED]", sanitized)
        if api_key in sanitized:
            sanitized = sanitized.replace(api_key, "[REDACTED]")
        return False, f"{type(e).__name__}: {sanitized}"


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
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "EMBEDDING_MODEL",
    "RETRIEVAL_TOP_K",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "SUPPORTED_PROVIDERS",
    "validate_provider",
    "get_llm_provider",
    "get_openai_api_key",
    "get_openai_model",
    "get_gemini_api_key",
    "get_gemini_model",
    "get_active_model",
    "get_active_api_key",
    "get_active_masked_api_key",
    "mask_api_key",
    "llm_available",
    "check_gemini_connection",
    "reload_config",
]
