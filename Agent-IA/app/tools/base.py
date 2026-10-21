from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Type

from pydantic import BaseModel


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def args_schema(self) -> Type[BaseModel]:
        pass

    @abstractmethod
    def run(self, args: Any) -> str:
        pass

    def get_tool_specification(self) -> Dict[str, Any]:
        schema = self.args_schema.model_json_schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
