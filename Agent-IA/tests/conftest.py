from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from app.schemas.api import ChatRequest, ChatResponse, MessageParam, MessageRole, Suggestion

# ---------------------------------------------------------------------------
# Environment fixture – run first so Settings() can be imported
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_groq_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test-key-for-pytest")


# ---------------------------------------------------------------------------
# Mock Groq completion response factories
# ---------------------------------------------------------------------------

def make_mock_choice_message(text: str) -> MagicMock:
    message = MagicMock()
    message.content = text
    message.tool_calls = None
    return message


def make_mock_choice_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    tool_call_id: str = "call_abc123",
) -> MagicMock:
    import json

    tc = MagicMock()
    tc.id = tool_call_id
    tc.type = "function"
    tc.function.name = tool_name
    tc.function.arguments = json.dumps(arguments)

    message = MagicMock()
    message.content = None
    message.tool_calls = [tc]
    return message


def make_mock_response(choice_message: MagicMock) -> MagicMock:
    choice = MagicMock()
    choice.message = choice_message

    response = MagicMock()
    response.choices = [choice]
    return response


# ---------------------------------------------------------------------------
# Pre-built payload templates
# ---------------------------------------------------------------------------

SAMPLE_CHAT_REQUEST = ChatRequest(
    message="Crée une facture pour Jean Dupont de 1500€ pour conseil",
    history=[],
)

SAMPLE_CHAT_RESPONSE_TEXT = ChatResponse(
    message="Voici le résumé de votre demande...",
    suggestion=Suggestion.none,
    steps_executed=[],
)

TOOL_CALL_ARGS_CREER_FACTURE: Dict[str, Any] = {
    "client_name": "Jean Dupont",
    "amount": 1500.0,
    "description": "Conseil en stratégie",
}

TOOL_CALL_ARGS_RELANCER: Dict[str, Any] = {
    "client_name": "Marie Durand",
    "invoice_id": "INV-2024-042",
}

TOOL_CALL_ARGS_CATEGORISER: Dict[str, Any] = {
    "expense_id": "EXP-009",
    "category": "fournitures",
}


# ---------------------------------------------------------------------------
# Mock FinanceAgentOrchestrator instance (used by API tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_orchestrator() -> MagicMock:
    orch = MagicMock()
    orch.run.return_value = ChatResponse(
        message="Facture créée avec succès pour Jean Dupont.",
        suggestion=Suggestion.none,
        steps_executed=["CreerFacture executed"],
    )
    return orch


# ---------------------------------------------------------------------------
# Patch groq.Groq so no real API key / network is needed
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_groq_client() -> None:
    with patch("groq.Groq") as mock_groq:
        mock_instance = MagicMock()
        mock_groq.return_value = mock_instance
        yield


@pytest.fixture
def mock_groq_chat_completion(_patch_groq_client: None) -> MagicMock:
    import groq
    return groq.Groq.return_value.chat.completions


# ---------------------------------------------------------------------------
# Patch httpx.Client for tool-run tests
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_httpx_client() -> MagicMock:
    with patch("httpx.Client") as mock_client_cls:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        yield mock_instance
