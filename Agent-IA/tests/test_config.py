from __future__ import annotations

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings

from app.config import Settings


def test_default_values_are_parsed() -> None:
    s = Settings(groq_api_key="gsk_test")
    assert s.groq_primary_model == "llama-3.3-70b-versatile"
    assert s.groq_fallback_model == "llama-3.1-8b-instant"
    assert s.mock_backend_url == "http://localhost:8000"
    assert s.max_agent_iterations == 5
    assert s.groq_api_key.get_secret_value() == "gsk_test"


def test_env_var_overrides_defaults(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "gsk_override")
    monkeypatch.setenv("GROQ_PRIMARY_MODEL", "custom-model")
    monkeypatch.setenv("MAX_AGENT_ITERATIONS", "10")
    s = Settings()
    assert s.groq_api_key.get_secret_value() == "gsk_override"
    assert s.groq_primary_model == "custom-model"
    assert s.max_agent_iterations == 10


def test_missing_groq_api_key_raises_validation_error(monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    class NoEnvSettings(BaseSettings):
        groq_api_key: str
        model_config = {"env_file": None}

    with pytest.raises(ValidationError):
        NoEnvSettings()


def test_custom_backend_url() -> None:
    s = Settings(groq_api_key="gsk_test", mock_backend_url="http://10.0.0.1:9999")
    assert s.mock_backend_url == "http://10.0.0.1:9999"


def test_module_settings_is_settings_instance() -> None:
    from app.config import settings
    assert isinstance(settings, Settings)
    assert settings.groq_api_key.get_secret_value() is not None
