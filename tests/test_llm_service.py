"""Tests for provider-independent context construction and reply generation."""

from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.schemas import Message, WorldState
from app.services.llm import service
from app.services.llm.base import LLMMessage
from app.services.llm.mock import MockLLMProvider


def make_message(role: str, content: str, sequence: int) -> Message:
    return Message.model_validate(
        {
            "id": UUID(int=sequence),
            "world_id": "shared_world",
            "role": role,
            "content": content,
            "created_at": datetime(2026, 9, 2, tzinfo=UTC),
        }
    )


def test_build_chat_context_combines_state_history_and_current_message() -> None:
    history = [
        make_message("user", "我喜欢蓝色", 1),
        make_message("assistant", "我记下了", 2),
    ]

    context = service.build_chat_context(
        history,
        "今天心情怎么样？",
        WorldState(mood="happy", energy=90),
    )

    assert [message.role for message in context] == [
        "system",
        "user",
        "assistant",
        "user",
    ]
    assert "心情=happy" in context[0].content
    assert "活力=90" in context[0].content
    assert context[-1].content == "今天心情怎么样？"


def test_generate_chat_reply_uses_bounded_history_and_provider(monkeypatch) -> None:
    captured: list[LLMMessage] = []

    class FakeProvider:
        def generate(self, messages: list[LLMMessage]) -> str:
            captured.extend(messages)
            return "  有上下文的回答  "

    monkeypatch.setattr(service, "get_recent_messages", lambda limit: [])
    monkeypatch.setattr(service, "get_llm_provider", FakeProvider)

    reply = service.generate_chat_reply("你好", WorldState())

    assert reply == "有上下文的回答"
    assert captured[-1] == LLMMessage(role="user", content="你好")


def test_generate_chat_reply_rejects_empty_provider_response(monkeypatch) -> None:
    class EmptyProvider:
        def generate(self, _messages: list[LLMMessage]) -> str:
            return "   "

    monkeypatch.setattr(service, "get_recent_messages", lambda limit: [])
    monkeypatch.setattr(service, "get_llm_provider", EmptyProvider)

    with pytest.raises(RuntimeError, match="empty reply"):
        service.generate_chat_reply("你好", WorldState())


def test_mock_provider_reports_previous_context_size() -> None:
    messages = [
        LLMMessage(role="system", content="system"),
        LLMMessage(role="user", content="旧问题"),
        LLMMessage(role="assistant", content="旧回答"),
        LLMMessage(role="user", content="新问题"),
    ]

    reply = MockLLMProvider().generate(messages)

    assert "新问题" in reply
    assert "此前 2 条消息" in reply
