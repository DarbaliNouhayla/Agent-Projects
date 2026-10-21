from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.schemas.api import MessageParam, MessageRole

logger = logging.getLogger(__name__)

TOKEN_BUDGET = 4000


def _estimate_tokens(text: str) -> int:
    return len(text) // 4


class SlidingWindowMemory:
    def __init__(self, system_prompt: str, history: List[Dict[str, str]] | List[MessageParam]) -> None:
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, Any]] = []
        self._build(history)

    def _build(self, history: List[Dict[str, Any]] | List[MessageParam]) -> None:
        compiled: List[Dict[str, Any]] = []
        for entry in history:
            if isinstance(entry, MessageParam):
                compiled.append({"role": entry.role.value, "content": entry.content})
            elif isinstance(entry, dict):
                compiled.append(entry)
        self.messages = compiled
        self._trim_context()

    def _trim_context(self) -> None:
        system_tokens = _estimate_tokens(self.system_prompt)
        available = TOKEN_BUDGET - system_tokens
        if available <= 0:
            logger.warning("System prompt alone exceeds token budget; truncating prompt.")
            return

        current_total = sum(_estimate_tokens(m.get("content", "")) for m in self.messages)
        while self.messages and current_total > available:
            removed = self.messages.pop(0)
            current_total -= _estimate_tokens(removed.get("content", ""))
            logger.debug("Trimmed one historical message to stay within token budget.")

    def get_context(self) -> List[Dict[str, Any]]:
        return [{"role": "system", "content": self.system_prompt}] + self.messages

    def append(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self._trim_context()
