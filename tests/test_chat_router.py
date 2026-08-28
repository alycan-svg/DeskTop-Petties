"""Tests for the chat route's persistence workflow."""

import pytest
from fastapi import HTTPException

from app.routers import chat as chat_router
from app.schemas import ChatRequest, WorldState


def test_chat_saves_the_returned_reply(monkeypatch) -> None:
    saved: list[tuple[str, str]] = []
    monkeypatch.setattr(chat_router, "verify_access_password", lambda _password: None)
    monkeypatch.setattr(chat_router, "get_world_state", WorldState)
    monkeypatch.setattr(
        chat_router,
        "save_conversation_turn",
        lambda user, assistant: saved.append((user, assistant)),
    )

    response = chat_router.chat(ChatRequest(message="你记得我吗？", password="valid"))

    assert response.reply == chat_router.PLACEHOLDER_REPLY
    assert saved == [("你记得我吗？", response.reply)]


def test_chat_returns_502_when_persistence_fails(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "verify_access_password", lambda _password: None)
    monkeypatch.setattr(chat_router, "get_world_state", WorldState)

    def fail_to_save(_user: str, _assistant: str) -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(chat_router, "save_conversation_turn", fail_to_save)

    with pytest.raises(HTTPException) as error:
        chat_router.chat(ChatRequest(message="你好", password="valid"))

    assert error.value.status_code == 502
    assert error.value.detail == "Unable to save the conversation turn to Supabase."


def test_read_chat_history_returns_service_messages(monkeypatch) -> None:
    checked_passwords: list[str] = []
    requested_limits: list[int] = []
    monkeypatch.setattr(
        chat_router,
        "verify_access_password",
        checked_passwords.append,
    )
    monkeypatch.setattr(
        chat_router,
        "get_recent_messages",
        lambda limit: requested_limits.append(limit) or [],
    )

    response = chat_router.read_chat_history(limit=12, access_password="valid")

    assert response.messages == []
    assert checked_passwords == ["valid"]
    assert requested_limits == [12]


def test_read_chat_history_returns_502_when_query_fails(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "verify_access_password", lambda _password: None)

    def fail_to_read(_limit: int) -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(chat_router, "get_recent_messages", fail_to_read)

    with pytest.raises(HTTPException) as error:
        chat_router.read_chat_history(limit=20, access_password="valid")

    assert error.value.status_code == 502
    assert error.value.detail == "Unable to read conversation history from Supabase."
