"""
test_provider_regression.py — Regression tests for LLM provider imports, configuration,
secret safety, and fallback behavior.
"""

import os
from unittest.mock import patch, MagicMock
import pytest


class TestProviderImports:
    """Verifies get_llm_provider and helpers can be imported from all public locations."""

    def test_import_from_src_config(self):
        from src.config import get_llm_provider, llm_available, get_openai_model, mask_api_key
        assert callable(get_llm_provider)
        assert callable(llm_available)
        assert callable(get_openai_model)
        assert callable(mask_api_key)

    def test_import_from_src_llm_provider(self):
        from src.llm_provider import get_llm_provider, llm_available, get_openai_model, mask_api_key
        assert callable(get_llm_provider)
        assert callable(llm_available)
        assert callable(get_openai_model)
        assert callable(mask_api_key)

    def test_import_from_src_package(self):
        from src import get_llm_provider, llm_available, get_openai_model, mask_api_key
        assert callable(get_llm_provider)
        assert callable(llm_available)
        assert callable(get_openai_model)
        assert callable(mask_api_key)


class TestKeyMaskingAndSecurity:
    """Ensures API keys are never exposed in logs, exceptions, or UI."""

    def test_mask_api_key_empty_or_default(self):
        from src.config import mask_api_key
        assert mask_api_key("") == "Not configured"
        assert mask_api_key(None) in ["Not configured", "••••••••"]
        assert mask_api_key("your-openai-api-key-here") == "Not configured"

    def test_mask_api_key_secret_masking(self):
        from src.config import mask_api_key
        secret = "sk-proj-1234567890abcdefghijklmnop"
        masked = mask_api_key(secret)
        assert secret not in masked
        assert masked.startswith("sk-")
        assert masked.endswith("mnop")
        assert "••••" in masked

    def test_gitignore_protects_env(self):
        """Verify .env is excluded by .gitignore."""
        with open(".gitignore", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
        assert ".env" in lines
        assert "*.env" in lines

    def test_env_example_has_no_secrets(self):
        """Verify .env.example contains no real API keys."""
        with open(".env.example", "r", encoding="utf-8") as f:
            content = f.read()
        assert "sk-proj-" not in content
        assert "sk-" not in content or "your-openai-api-key-here" in content


class TestProviderConfigurationAndFallback:
    """Tests provider behavior with none, openai, missing key, and custom models."""

    def test_provider_none_is_deterministic(self):
        from src.energy_assistant import generate_energy_explanation
        with patch("src.config.get_llm_provider", return_value="none"):
            with patch("src.config.llm_available", return_value=False):
                res = generate_energy_explanation("Explain my EV charging schedule")
                assert res["mode"] == "grounded_extractive"
                assert res["model"] == "rule_grounded_fallback"
                assert "Electric Vehicle" in res["answer"]

    def test_provider_openai_missing_key_gives_clear_notice(self):
        from src.energy_assistant import generate_energy_explanation
        with patch("src.config.get_llm_provider", return_value="openai"):
            with patch("src.config.llm_available", return_value=False):
                res = generate_energy_explanation("Explain my EV charging schedule")
                assert res["mode"] == "grounded_extractive"
                assert "OpenAI Configuration Notice" in res["answer"]
                assert "OPENAI_API_KEY" in res["answer"]

    def test_custom_openai_model_passed_dynamically(self):
        """Verify user-configured model (e.g. gpt-4o-mini) is passed dynamically."""
        from src.energy_assistant import generate_energy_explanation
        custom_model = "gpt-4o-mini"

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "OpenAI synthesized answer using custom model."
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("src.config.get_llm_provider", return_value="openai"):
            with patch("src.config.llm_available", return_value=True):
                with patch("src.config.get_openai_api_key", return_value="sk-valid-test-key-12345678"):
                    with patch("src.config.get_openai_model", return_value=custom_model):
                        with patch("openai.OpenAI", return_value=mock_client):
                            res = generate_energy_explanation("Why was EV delayed?")
                            assert res["mode"] == "llm"
                            assert res["model"] == custom_model
                            # Verify create was called with custom_model
                            kwargs = mock_client.chat.completions.create.call_args[1]
                            assert kwargs["model"] == custom_model

    def test_openai_api_error_falls_back_safely(self):
        """Verify OpenAI API failures fall back cleanly without raising unhandled exceptions."""
        from src.energy_assistant import generate_energy_explanation
        import openai

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APIConnectionError(request=MagicMock())

        with patch("src.config.get_llm_provider", return_value="openai"):
            with patch("src.config.llm_available", return_value=True):
                with patch("src.config.get_openai_api_key", return_value="sk-valid-test-key-12345678"):
                    with patch("openai.OpenAI", return_value=mock_client):
                        res = generate_energy_explanation("How much money did I save?")
                        assert res["mode"] == "grounded_extractive"
                        assert "Note:" in res["answer"]
                        assert "Energy Cost" in res["answer"]
