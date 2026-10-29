"""
Smart Home Energy Management package.
Exposes common utilities and configuration helpers.
"""

from src.config import (
    SUPPORTED_PROVIDERS,
    validate_provider,
    get_llm_provider,
    get_openai_api_key,
    get_openai_model,
    get_gemini_api_key,
    get_gemini_model,
    get_active_model,
    get_active_api_key,
    get_active_masked_api_key,
    mask_api_key,
    llm_available,
    check_gemini_connection,
    reload_config,
)

__all__ = [
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
