from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool = "tool"


class SelectedContext(str, Enum):
    personnel = "personnel"
    professionnel = "professionnel"
    sante = "santé"


class Suggestion(str, Enum):
    booking_intent = "BOOKING_INTENT"
    none = "NONE"


class MessageParam(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[MessageParam] = Field(default_factory=list)
    selected_context: Optional[SelectedContext] = None


class ChatResponse(BaseModel):
    message: str
    suggestion: Suggestion = Suggestion.none
    steps_executed: List[str] = Field(default_factory=list)
