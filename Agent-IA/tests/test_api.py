from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.api import ChatRequest, ChatResponse, Suggestion


def _make_client() -> TestClient:
    from app.main import app
    return TestClient(app)


class TestChatEndpoint:
    def test_health_endpoint_returns_ok(self) -> None:
        client = _make_client()
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_post_chat_returns_200_with_valid_response(self) -> None:
        from app.main import orchestrator

        client = _make_client()

        with patch.object(
            orchestrator,
            "run",
            return_value=ChatResponse(
                message="Facture créée avec succès pour Jean Dupont.",
                suggestion=Suggestion.none,
                steps_executed=["CreerFacture executed"],
            ),
        ):
            payload = {
                "message": "Crée une facture pour Jean Dupont de 1500€",
                "history": [],
            }
            response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Facture créée avec succès pour Jean Dupont."
        assert data["suggestion"] == "NONE"
        assert data["steps_executed"] == ["CreerFacture executed"]

    def test_post_chat_with_history(self) -> None:
        from app.main import orchestrator

        client = _make_client()

        with patch.object(
            orchestrator,
            "run",
            return_value=ChatResponse(
                message="Suite de la conversation.",
                suggestion=Suggestion.none,
                steps_executed=[],
            ),
        ):
            payload = {
                "message": "Suite",
                "history": [
                    {"role": "user", "content": "Bonjour"},
                    {"role": "assistant", "content": "Bonjour, comment puis-je vous aider ?"},
                ],
            }
            response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Suite de la conversation."

    def test_post_chat_with_selected_context(self) -> None:
        from app.main import orchestrator

        client = _make_client()

        with patch.object(
            orchestrator,
            "run",
            return_value=ChatResponse(
                message="Contexte professionnel sélectionné.",
                suggestion=Suggestion.none,
                steps_executed=[],
            ),
        ):
            payload = {
                "message": "Analyse mes dépenses",
                "history": [],
                "selected_context": "professionnel",
            }
            response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Contexte professionnel sélectionné."

    def test_post_chat_booking_intent_suggestion(self) -> None:
        from app.main import orchestrator

        client = _make_client()

        with patch.object(
            orchestrator,
            "run",
            return_value=ChatResponse(
                message="Le client refuse de payer la facture.",
                suggestion=Suggestion.booking_intent,
                steps_executed=["RelancerClient executed"],
            ),
        ):
            payload = {
                "message": "Mon client refuse de payer",
                "history": [],
            }
            response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["suggestion"] == "BOOKING_INTENT"
        assert "RelancerClient executed" in data["steps_executed"]

    def test_post_chat_empty_message(self) -> None:
        from app.main import orchestrator

        client = _make_client()

        with patch.object(
            orchestrator,
            "run",
            return_value=ChatResponse(
                message="Je n'ai pas compris votre demande.",
                suggestion=Suggestion.none,
                steps_executed=[],
            ),
        ):
            payload = {
                "message": "",
                "history": [],
            }
            response = client.post("/api/chat", json=payload)

        assert response.status_code == 200

    def test_post_chat_invalid_payload_returns_422(self) -> None:
        client = _make_client()
        response = client.post("/api/chat", json={"invalid": "data"})
        assert response.status_code == 422


class TestChatResponseStructure:
    def test_response_fields_match_chat_response_schema(self) -> None:
        from app.main import orchestrator

        client = _make_client()

        with patch.object(
            orchestrator,
            "run",
            return_value=ChatResponse(
                message="Test",
                suggestion=Suggestion.none,
                steps_executed=["step1"],
            ),
        ):
            payload = ChatRequest(message="Test", history=[]).model_dump()
            response = client.post("/api/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "suggestion" in data
        assert "steps_executed" in data
        assert isinstance(data["message"], str)
        assert isinstance(data["suggestion"], str)
        assert isinstance(data["steps_executed"], list)
