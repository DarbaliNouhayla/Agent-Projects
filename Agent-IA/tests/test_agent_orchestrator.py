from __future__ import annotations

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from app.core.agent import FinanceAgentOrchestrator
from app.schemas.api import ChatRequest, ChatResponse, Suggestion

# ---------------------------------------------------------------------------
# Helper – build a mock Groq response from a text message
# ---------------------------------------------------------------------------

def _text_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = text
    msg.tool_calls = None
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# Helper – build a mock Groq response that requests a tool call
# ---------------------------------------------------------------------------

def _tool_call_response(
    tool_name: str,
    arguments: Dict[str, Any],
    tool_call_id: str = "call_test_001",
) -> MagicMock:
    tc = MagicMock()
    tc.id = tool_call_id
    tc.type = "function"
    tc.function.name = tool_name
    tc.function.arguments = json.dumps(arguments)

    msg = MagicMock()
    msg.content = None
    msg.tool_calls = [tc]

    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# =========================================================================
# Scenario 1 – Conversational only (no tool call)
# =========================================================================


class TestScenarioConversational:
    @patch("app.core.agent.GroqClient")
    def test_returns_assistant_message_and_no_steps(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance
        mock_instance.generate_chat_completion.return_value = _text_response(
            "Bonjour, je suis votre assistant financier. Comment puis-je vous aider ?"
        )

        orchestrator = FinanceAgentOrchestrator()
        request = ChatRequest(message="Bonjour", history=[])
        response = orchestrator.run(request)

        assert response.message == "Bonjour, je suis votre assistant financier. Comment puis-je vous aider ?"
        assert response.steps_executed == []
        assert response.suggestion == Suggestion.none

    @patch("app.core.agent.GroqClient")
    def test_no_tool_call_suggestion_stays_none(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance
        mock_instance.generate_chat_completion.return_value = _text_response(
            "Je peux vous aider avec vos factures."
        )

        orchestrator = FinanceAgentOrchestrator()
        request = ChatRequest(message="Quels sont mes outils ?", history=[])
        response = orchestrator.run(request)

        assert response.suggestion == Suggestion.none


# =========================================================================
# Scenario 2 – Tool execution routing
# =========================================================================


class TestScenarioToolExecution:
    @patch("app.core.agent.GroqClient")
    def test_executes_tool_and_returns_summary(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance

        # First LLM call → tool call request
        # Second LLM call (after tool result) → French summary
        mock_instance.generate_chat_completion.side_effect = [
            _tool_call_response("CreerFacture", {
                "client_name": "Jean Dupont",
                "amount": 1500.0,
                "description": "Conseil en stratégie",
            }),
            _text_response(
                "La facture pour Jean Dupont d'un montant de 1500€ a été créée avec succès."
            ),
        ]

        orchestrator = FinanceAgentOrchestrator()

        with patch.object(
            orchestrator._tool_map["CreerFacture"], "run", return_value="Facture créée : OK"
        ) as mock_tool_run:
            request = ChatRequest(
                message="Crée une facture pour Jean Dupont de 1500€",
                history=[],
            )
            response = orchestrator.run(request)

        assert "La facture pour Jean Dupont" in response.message
        assert "CreerFacture executed" in response.steps_executed
        assert response.suggestion == Suggestion.none
        mock_tool_run.assert_called_once()

    @patch("app.core.agent.GroqClient")
    def test_reports_unknown_tool_gracefully(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance

        mock_instance.generate_chat_completion.side_effect = [
            _tool_call_response("OutilInexistant", {"param": "value"}),
            _text_response("Je n'ai pas trouvé l'outil demandé."),
        ]

        orchestrator = FinanceAgentOrchestrator()
        request = ChatRequest(message="Appelle un outil inconnu", history=[])
        response = orchestrator.run(request)

        assert "Outil inconnu" in response.message or "n'ai pas trouvé" in response.message

    @patch("app.core.agent.GroqClient")
    def test_tool_error_does_not_crash_orchestrator(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance

        mock_instance.generate_chat_completion.side_effect = [
            _tool_call_response("CreerFacture", {
                "client_name": "Jean Dupont",
                "amount": 1500.0,
                "description": "Conseil",
            }),
            _text_response("Une erreur est survenue lors de la création de la facture."),
        ]

        orchestrator = FinanceAgentOrchestrator()

        with patch.object(
            orchestrator._tool_map["CreerFacture"],
            "run",
            return_value="Erreur lors de la création de la facture : HTTP 500",
        ):
            request = ChatRequest(message="Crée une facture", history=[])
            response = orchestrator.run(request)

        assert response.steps_executed == ["CreerFacture executed"]


# =========================================================================
# Scenario 3 – Booking intent heuristic
# =========================================================================


class TestScenarioBookingIntent:
    @patch("app.core.agent.GroqClient")
    def test_dispute_keyword_triggers_booking_intent(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance
        mock_instance.generate_chat_completion.return_value = _text_response(
            "Le client refuse de payer la facture INV-2024-042. "
            "Il conteste les montants facturés."
        )

        orchestrator = FinanceAgentOrchestrator()
        request = ChatRequest(
            message="Mon client conteste sa facture",
            history=[],
        )
        response = orchestrator.run(request)

        assert response.suggestion == Suggestion.booking_intent

    @patch("app.core.agent.GroqClient")
    def test_french_pushback_triggers_booking_intent(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance
        mock_instance.generate_chat_completion.return_value = _text_response(
            "Le client a exprimé des difficultés financières et ne peut pas payer "
            "la facture pour le moment."
        )

        orchestrator = FinanceAgentOrchestrator()
        request = ChatRequest(
            message="Le client ne peut pas payer sa facture",
            history=[],
        )
        response = orchestrator.run(request)

        assert response.suggestion == Suggestion.booking_intent

    @patch("app.core.agent.GroqClient")
    def test_no_keyword_remains_none(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance
        mock_instance.generate_chat_completion.return_value = _text_response(
            "La facture a été envoyée avec succès au client."
        )

        orchestrator = FinanceAgentOrchestrator()
        request = ChatRequest(
            message="Envoie la facture au client",
            history=[],
        )
        response = orchestrator.run(request)

        assert response.suggestion == Suggestion.none


# =========================================================================
# Max iterations guard
# =========================================================================


class TestMaxIterations:
    @patch("app.core.agent.GroqClient")
    def test_loop_exits_when_max_iterations_reached(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance

        # Every LLM call returns a tool call → infinite loop prevented by max iterations
        mock_instance.generate_chat_completion.return_value = _tool_call_response(
            "CreerFacture", {
                "client_name": "X",
                "amount": 100.0,
                "description": "Test",
            }
        )

        with patch.object(
            FinanceAgentOrchestrator, "_get_tool_specs", return_value=[]
        ):
            orchestrator = FinanceAgentOrchestrator()

            with patch.object(
                orchestrator._tool_map["CreerFacture"],
                "run",
                return_value="Facture créée : OK",
            ):
                request = ChatRequest(message="test", history=[])
                response = orchestrator.run(request)

        assert "limite" in response.message or "itération" in response.message


# =========================================================================
# ChatResponse structure
# =========================================================================


class TestResponseStructure:
    @patch("app.core.agent.GroqClient")
    def test_response_is_chat_response_instance(
        self, mock_groq_cls: MagicMock
    ) -> None:
        mock_instance = MagicMock()
        mock_groq_cls.return_value = mock_instance
        mock_instance.generate_chat_completion.return_value = _text_response("Bonjour")

        orchestrator = FinanceAgentOrchestrator()
        request = ChatRequest(message="Bonjour", history=[])
        response = orchestrator.run(request)

        assert isinstance(response, ChatResponse)
        assert isinstance(response.message, str)
        assert isinstance(response.suggestion, Suggestion)
        assert isinstance(response.steps_executed, list)
