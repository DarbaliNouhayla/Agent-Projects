from __future__ import annotations

import logging
from typing import Any, Type

import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class RelancerClientArgs(BaseModel):
    client_name: str = Field(description="Full name of the client to send the reminder to")
    invoice_id: str = Field(description="Unique identifier of the overdue invoice")


class RelancerClientTool(BaseTool):
    name: str = "RelancerClient"
    description: str = "Send a payment collection reminder to a client for a specific overdue invoice"
    args_schema: Type[BaseModel] = RelancerClientArgs

    def run(self, args: Any) -> str:
        try:
            parsed = RelancerClientArgs.model_validate(args)
            payload = {
                "client_name": parsed.client_name,
                "invoice_id": parsed.invoice_id,
            }
            with httpx.Client(timeout=30) as client:
                response = client.post(f"{settings.mock_backend_url}/reminders", json=payload)
                response.raise_for_status()
                result = response.json()
            logger.info("Reminder sent successfully to %s.", parsed.client_name)
            return f"Relance envoyée avec succès à {parsed.client_name} : {result}"
        except Exception as exc:
            logger.error("Failed to send reminder to %s: %s", args, exc)
            return f"Erreur lors de l'envoi de la relance : {exc}"
