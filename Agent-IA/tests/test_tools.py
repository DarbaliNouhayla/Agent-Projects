from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError

from app.tools.accounting import CategoriserDepenseArgs, CategoriserDepenseTool
from app.tools.billing import CreerFactureArgs, CreerFactureTool
from app.tools.collections import RelancerClientArgs, RelancerClientTool

# =========================================================================
# Schema validation tests
# =========================================================================


class TestCreerFactureArgs:
    def test_valid_args(self) -> None:
        args = CreerFactureArgs(client_name="Jean", amount=1500.0, description="Conseil")
        assert args.client_name == "Jean"
        assert args.amount == 1500.0
        assert args.description == "Conseil"

    def test_string_amount_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreerFactureArgs(client_name="Jean", amount="not-a-number", description="Test")  # type: ignore[arg-type]

    def test_missing_client_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreerFactureArgs(amount=100.0, description="Test")  # type: ignore[call-arg]

    def test_negative_amount_is_accepted_by_schema(self) -> None:
        args = CreerFactureArgs(client_name="Jean", amount=-50.0, description="Avoir")
        assert args.amount == -50.0


class TestRelancerClientArgs:
    def test_valid_args(self) -> None:
        args = RelancerClientArgs(client_name="Marie", invoice_id="INV-001")
        assert args.client_name == "Marie"
        assert args.invoice_id == "INV-001"

    def test_missing_invoice_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            RelancerClientArgs(client_name="Marie")  # type: ignore[call-arg]


class TestCategoriserDepenseArgs:
    def test_valid_args(self) -> None:
        args = CategoriserDepenseArgs(expense_id="EXP-01", category="voyage")
        assert args.expense_id == "EXP-01"
        assert args.category == "voyage"


# =========================================================================
# Tool execution tests – httpx.Client is mocked
# =========================================================================


def _mock_httpx_response(status_code: int, json_data: dict) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


class TestCreerFactureTool:
    @patch("httpx.Client")
    def test_successful_execution(self, mock_client_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.post.return_value = _mock_httpx_response(
            201, {"id": "INV-123", "status": "created"}
        )

        tool = CreerFactureTool()
        result = tool.run({
            "client_name": "Jean Dupont",
            "amount": 1500.0,
            "description": "Conseil",
        })

        assert "Facture créée avec succès" in result
        mock_instance.post.assert_called_once()
        call_kwargs = mock_instance.post.call_args[1]
        assert call_kwargs["json"]["client_name"] == "Jean Dupont"
        assert call_kwargs["json"]["amount"] == 1500.0

    @patch("httpx.Client")
    def test_server_error_returns_clean_message(self, mock_client_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        resp = MagicMock(spec=httpx.Response)
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Server Error", request=MagicMock(), response=MagicMock()
        )
        mock_instance.post.return_value = resp

        tool = CreerFactureTool()
        result = tool.run({
            "client_name": "Jean Dupont",
            "amount": 1500.0,
            "description": "Conseil",
        })

        assert "Erreur" in result

    @patch("httpx.Client")
    def test_timeout_returns_clean_message(self, mock_client_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.post.side_effect = httpx.TimeoutException("Connection timed out")

        tool = CreerFactureTool()
        result = tool.run({
            "client_name": "Jean Dupont",
            "amount": 1500.0,
            "description": "Conseil",
        })

        assert "Erreur" in result


class TestRelancerClientTool:
    @patch("httpx.Client")
    def test_successful_execution(self, mock_client_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.post.return_value = _mock_httpx_response(
            200, {"status": "reminder_sent"}
        )

        tool = RelancerClientTool()
        result = tool.run({
            "client_name": "Marie Durand",
            "invoice_id": "INV-2024-042",
        })

        assert "Relance envoyée" in result
        mock_instance.post.assert_called_once()
        call_kwargs = mock_instance.post.call_args[1]
        assert call_kwargs["json"]["client_name"] == "Marie Durand"

    @patch("httpx.Client")
    def test_error_returns_clean_message(self, mock_client_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.post.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        )

        tool = RelancerClientTool()
        result = tool.run({
            "client_name": "Inconnu",
            "invoice_id": "INV-999",
        })

        assert "Erreur" in result


class TestCategoriserDepenseTool:
    @patch("httpx.Client")
    def test_successful_execution(self, mock_client_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.put.return_value = _mock_httpx_response(
            200, {"status": "categorized"}
        )

        tool = CategoriserDepenseTool()
        result = tool.run({
            "expense_id": "EXP-009",
            "category": "fournitures",
        })

        assert "catégorisée avec succès" in result
        mock_instance.put.assert_called_once()
        call_kwargs = mock_instance.put.call_args[1]
        assert call_kwargs["json"]["expense_id"] == "EXP-009"

    @patch("httpx.Client")
    def test_error_returns_clean_message(self, mock_client_cls: MagicMock) -> None:
        mock_instance = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.put.side_effect = httpx.TimeoutException("Timeout")

        tool = CategoriserDepenseTool()
        result = tool.run({
            "expense_id": "EXP-999",
            "category": "logiciel",
        })

        assert "Erreur" in result


# =========================================================================
# Tool specification generation tests
# =========================================================================


def test_get_tool_specification_structure() -> None:
    from app.tools.base import BaseTool
    from pydantic import BaseModel

    tool = CreerFactureTool()
    spec = tool.get_tool_specification()

    assert spec["type"] == "function"
    assert spec["function"]["name"] == "CreerFacture"
    assert "parameters" in spec["function"]
    params = spec["function"]["parameters"]
    assert params["type"] == "object"
    assert "client_name" in params["properties"]
    assert "amount" in params["properties"]
    assert "description" in params["properties"]
    assert "client_name" in params["required"]
    assert "amount" in params["required"]
