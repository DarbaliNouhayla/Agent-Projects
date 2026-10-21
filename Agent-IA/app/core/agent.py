from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from app.config import settings
from app.core.llm import GroqClient
from app.core.memory import SlidingWindowMemory
from app.core.prompts import build_system_prompt
from app.schemas.api import ChatRequest, ChatResponse, Suggestion
from app.tools.accounting import CategoriserDepenseTool
from app.tools.base import BaseTool
from app.tools.billing import CreerFactureTool
from app.tools.collections import RelancerClientTool

logger = logging.getLogger(__name__)

BOOKING_INTENT_KEYWORDS = [
    "contest", "dispute", "refuse", "ne peut pas payer",
    "difficulté financière", "pushback", "je ne paierai pas",
]


class FinanceAgentOrchestrator:
    def __init__(self) -> None:
        self._llm = GroqClient()
        self._tools: List[BaseTool] = [
            CreerFactureTool(),
            RelancerClientTool(),
            CategoriserDepenseTool(),
        ]
        self._tool_map: Dict[str, BaseTool] = {t.name: t for t in self._tools}

    def _get_tool_specs(self) -> List[Dict[str, Any]]:
        return [t.get_tool_specification() for t in self._tools]

    def _detect_booking_intent(self, text: str) -> bool:
        lowered = text.lower()
        return any(kw.lower() in lowered for kw in BOOKING_INTENT_KEYWORDS)

    def run(self, request: ChatRequest) -> ChatResponse:
        system_prompt = build_system_prompt()
        history_dicts: List[Dict[str, str]] = []
        for h in request.history:
            history_dicts.append({"role": h.role.value, "content": h.content})

        memory = SlidingWindowMemory(system_prompt, history_dicts)
        memory.append("user", request.message)

        context = memory.get_context()
        tool_specs = self._get_tool_specs()
        steps: List[str] = []

        suggestion = Suggestion.none

        for iteration in range(settings.max_agent_iterations):
            logger.info("Agent iteration %d/%d.", iteration + 1, settings.max_agent_iterations)

            response = self._llm.generate_chat_completion(context, tools=tool_specs)
            choice = response.choices[0]
            message = choice.message

            if message.tool_calls:
                tool_calls_data = []
                for tc in message.tool_calls:
                    tool_calls_data.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    })

                assistant_msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": message.content or "",
                }
                if tool_calls_data:
                    assistant_msg["tool_calls"] = tool_calls_data
                context.append(assistant_msg)

                for tc in message.tool_calls:
                    tool_name = tc.function.name
                    raw_args = tc.function.arguments
                    logger.info("Tool call: %s with args %s", tool_name, raw_args)

                    tool = self._tool_map.get(tool_name)
                    if tool is None:
                        error_msg = f"Outil inconnu : {tool_name}"
                        context.append({"role": "tool", "tool_call_id": tc.id, "content": error_msg})
                        steps.append(error_msg)
                        continue

                    try:
                        parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except json.JSONDecodeError:
                        parsed_args = {}

                    result = tool.run(parsed_args)
                    steps.append(f"{tool_name} executed")
                    context.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                    memory.append("tool", result)

                continue

            content = message.content or ""
            context.append({"role": "assistant", "content": content})
            memory.append("assistant", content)

            if self._detect_booking_intent(content):
                suggestion = Suggestion.booking_intent

            return ChatResponse(
                message=content,
                suggestion=suggestion,
                steps_executed=steps,
            )

        logger.warning("Agent reached max iterations (%d). Forcing exit.", settings.max_agent_iterations)
        return ChatResponse(
            message="Désolé, je n'ai pas pu traiter votre demande dans le nombre limite d'itérations. Veuillez reformuler ou contacter un conseiller.",
            suggestion=suggestion,
            steps_executed=steps,
        )
