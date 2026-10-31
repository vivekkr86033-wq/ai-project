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
from src.ui_theme import (
    inject_custom_css,
    apply_plotly_theme,
    render_hero_banner,
    render_kpi_card,
    render_interactive_energy_topology,
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
    "inject_custom_css",
    "apply_plotly_theme",
    "render_hero_banner",
    "render_kpi_card",
    "render_interactive_energy_topology",
]
