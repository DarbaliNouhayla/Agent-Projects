from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from groq import Groq

from app.config import settings
from app.core.exceptions import LLMConnectionError, RateLimitExceeded

logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self) -> None:
        self._client = Groq(api_key=settings.groq_api_key.get_secret_value())
        self._primary_model: str = settings.groq_primary_model
        self._fallback_model: str = settings.groq_fallback_model
        self._active_model: str = self._primary_model

    def _execute_with_retry(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        attempt: int = 1,
        max_retries: int = 3,
    ) -> Any:
        try:
            kwargs: Dict[str, Any] = {
                "model": self._active_model,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self._client.chat.completions.create(**kwargs)
            return response

        except Exception as exc:
            error_str = str(exc).lower()
            is_rate_limit = "429" in error_str or "rate limit" in error_str or "too many requests" in error_str

            if is_rate_limit and attempt <= max_retries:
                wait = 2 ** attempt
                logger.warning(
                    "Rate limited (attempt %d/%d). Waiting %ds before retry.",
                    attempt, max_retries, wait,
                )
                if attempt < max_retries:
                    time.sleep(wait)
                    return self._execute_with_retry(messages, tools, attempt + 1, max_retries)
                raise RateLimitExceeded(
                    f"Rate limit exceeded after {max_retries} retries."
                ) from exc

            if attempt <= max_retries:
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s. Retrying...",
                    attempt, max_retries, exc,
                )
                time.sleep(2 ** attempt)
                return self._execute_with_retry(messages, tools, attempt + 1, max_retries)

            if self._active_model == self._primary_model:
                logger.info("Primary model failed; falling back to %s.", self._fallback_model)
                self._active_model = self._fallback_model
                return self._execute_with_retry(messages, tools, 1, max_retries)

            raise LLMConnectionError(f"LLM connection failed after retries and fallback: {exc}") from exc

    def generate_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        return self._execute_with_retry(messages, tools)
