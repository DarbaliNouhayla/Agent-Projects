from __future__ import annotations

import logging
from typing import Any, Type

import httpx
from pydantic import BaseModel, Field

from app.config import settings
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class CategoriserDepenseArgs(BaseModel):
    expense_id: str = Field(description="Unique identifier of the expense to classify")
    category: str = Field(description="Target expense category (e.g. 'fournitures', 'voyage', 'logiciel')")


class CategoriserDepenseTool(BaseTool):
    name: str = "CategoriserDepense"
    description: str = "Classify an expense into a specific accounting category"
    args_schema: Type[BaseModel] = CategoriserDepenseArgs

    def run(self, args: Any) -> str:
        try:
            parsed = CategoriserDepenseArgs.model_validate(args)
            payload = {
                "expense_id": parsed.expense_id,
                "category": parsed.category,
            }
            with httpx.Client(timeout=30) as client:
                response = client.put(f"{settings.mock_backend_url}/expenses", json=payload)
                response.raise_for_status()
                result = response.json()
            logger.info("Expense %s categorized as '%s'.", parsed.expense_id, parsed.category)
            return f"Dépense {parsed.expense_id} catégorisée avec succès en '{parsed.category}' : {result}"
        except Exception as exc:
            logger.error("Failed to categorize expense %s: %s", args, exc)
            return f"Erreur lors de la catégorisation de la dépense : {exc}"
