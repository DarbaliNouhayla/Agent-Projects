from __future__ import annotations

import logging
from typing import Any, Type

import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class CreerFactureArgs(BaseModel):
    client_name: str = Field(description="Full name of the client being invoiced")
    amount: float = Field(description="Total invoice amount in euros")
    description: str = Field(description="Description of the products or services being billed")


class CreerFactureTool(BaseTool):
    name: str = "CreerFacture"
    description: str = "Generate a new invoice for a client with a specified amount and description"
    args_schema: Type[BaseModel] = CreerFactureArgs

    def run(self, args: Any) -> str:
        try:
            parsed = CreerFactureArgs.model_validate(args)
            payload = {
                "client_name": parsed.client_name,
                "amount": parsed.amount,
                "description": parsed.description,
            }
            with httpx.Client(timeout=30) as client:
                response = client.post(f"{settings.mock_backend_url}/invoices", json=payload)
                response.raise_for_status()
                result = response.json()
            logger.info("Invoice created successfully for %s.", parsed.client_name)
            return f"Facture créée avec succès : {result}"
        except Exception as exc:
            logger.error("Failed to create invoice for %s: %s", args, exc)
            return f"Erreur lors de la création de la facture : {exc}"
