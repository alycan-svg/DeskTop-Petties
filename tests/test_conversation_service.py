"""Unit tests for shared-world conversation persistence."""

from types import SimpleNamespace

import pytest

from app.services import conversation_service


class FakeInsertQuery:
    def __init__(self, returned_rows: list[dict]) -> None:
        self.returned_rows = returned_rows
        self.inserted_rows: list[dict] | None = None

    def insert(self, rows: list[dict]) -> "FakeInsertQuery":
        self.inserted_rows = rows
        return self

    def execute(self) -> SimpleNamespace:
        return SimpleNamespace(data=self.returned_rows)


class FakeClient:
    def __init__(self, query: FakeInsertQuery) -> None:
        self.query = query

    def table(self, table_name: str) -> FakeInsertQuery:
        assert table_name == "messages"
        return self.query


def test_save_conversation_turn_inserts_user_and_assistant(monkeypatch) -> None:
    returned_rows = [
        {"id": "user-id", "role": "user"},
        {"id": "assistant-id", "role": "assistant"},
    ]
    query = FakeInsertQuery(returned_rows)
    monkeypatch.setattr(
        conversation_service,
        "get_supabase_client",
        lambda: FakeClient(query),
    )

    result = conversation_service.save_conversation_turn("你好", "你好呀")

    assert result == returned_rows
    assert query.inserted_rows == [
        {"world_id": "shared_world", "role": "user", "content": "你好"},
        {"world_id": "shared_world", "role": "assistant", "content": "你好呀"},
    ]


def test_save_conversation_turn_rejects_incomplete_result(monkeypatch) -> None:
    query = FakeInsertQuery([{"id": "user-id", "role": "user"}])
    monkeypatch.setattr(
        conversation_service,
        "get_supabase_client",
        lambda: FakeClient(query),
    )

    with pytest.raises(RuntimeError, match="complete conversation turn"):
        conversation_service.save_conversation_turn("你好", "你好呀")
