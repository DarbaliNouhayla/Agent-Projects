from __future__ import annotations

from app.core.memory import SlidingWindowMemory, _estimate_tokens

_LONG_MSG = "Bonjour " * 2000


def test_system_prompt_at_index_zero() -> None:
    mem = SlidingWindowMemory("System prompt content", [])
    ctx = mem.get_context()
    assert ctx[0]["role"] == "system"
    assert ctx[0]["content"] == "System prompt content"


def test_system_prompt_never_removed_after_truncation() -> None:
    large_history = [
        {"role": "user", "content": _LONG_MSG},
        {"role": "assistant", "content": _LONG_MSG},
        {"role": "user", "content": _LONG_MSG},
        {"role": "assistant", "content": _LONG_MSG},
    ]
    mem = SlidingWindowMemory("Short system prompt", large_history)
    ctx = mem.get_context()
    assert ctx[0]["role"] == "system"
    assert ctx[0]["content"] == "Short system prompt"


def test_old_messages_are_truncated_when_over_budget() -> None:
    sp = "S" * 10
    history = [{"role": "user", "content": _LONG_MSG}] * 10
    mem = SlidingWindowMemory(sp, history)
    total_tokens = sum(_estimate_tokens(m.get("content", "")) for m in mem.messages)
    available = 4000 - _estimate_tokens(sp)
    assert total_tokens <= available


def test_empty_history_keeps_system_prompt_only() -> None:
    mem = SlidingWindowMemory("Sys", [])
    ctx = mem.get_context()
    assert len(ctx) == 1
    assert ctx[0]["role"] == "system"


def test_append_respects_token_budget() -> None:
    mem = SlidingWindowMemory("Sys", [])
    mem.append("user", _LONG_MSG)
    mem.append("assistant", _LONG_MSG)
    mem.append("user", _LONG_MSG)
    ctx = mem.get_context()
    assert ctx[0]["role"] == "system"
    total_no_system = sum(_estimate_tokens(m.get("content", "")) for m in mem.messages)
    assert total_no_system <= 4000 - _estimate_tokens("Sys")


def test_build_from_message_param_objects() -> None:
    from app.schemas.api import MessageParam, MessageRole
    history = [
        MessageParam(role=MessageRole.user, content="Hello"),
        MessageParam(role=MessageRole.assistant, content="Bonjour"),
    ]
    mem = SlidingWindowMemory("Sys", history)
    assert len(mem.messages) == 2
    assert mem.messages[0]["role"] == "user"
    assert mem.messages[1]["role"] == "assistant"


def test_estimate_tokens() -> None:
    assert _estimate_tokens("abcd") == 1
    assert _estimate_tokens("") == 0
    assert _estimate_tokens("a" * 100) == 25
