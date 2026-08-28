"""Unit tests for shared-world conversation persistence."""

from types import SimpleNamespace
from uuid import UUID

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


class FakeSelectQuery:
    def __init__(self, returned_rows: list[dict]) -> None:
        self.returned_rows = returned_rows
        self.filters: list[tuple[str, str]] = []
        self.requested_limit: int | None = None
        self.descending: bool | None = None

    def select(self, _columns: str) -> "FakeSelectQuery":
        return self

    def eq(self, column: str, value: str) -> "FakeSelectQuery":
        self.filters.append((column, value))
        return self

    def order(self, _column: str, desc: bool) -> "FakeSelectQuery":
        self.descending = desc
        return self

    def limit(self, count: int) -> "FakeSelectQuery":
        self.requested_limit = count
        return self

    def execute(self) -> SimpleNamespace:
        return SimpleNamespace(data=self.returned_rows)


class FakeClient:
    def __init__(self, query: FakeInsertQuery | FakeSelectQuery) -> None:
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


def test_get_recent_messages_returns_chronological_history(monkeypatch) -> None:
    newest_first = [
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "world_id": "shared_world",
            "role": "assistant",
            "content": "你好呀",
            "created_at": "2026-08-28T12:00:01Z",
        },
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "world_id": "shared_world",
            "role": "user",
            "content": "你好",
            "created_at": "2026-08-28T12:00:00Z",
        },
    ]
    query = FakeSelectQuery(newest_first)
    monkeypatch.setattr(
        conversation_service,
        "get_supabase_client",
        lambda: FakeClient(query),
    )

    result = conversation_service.get_recent_messages(limit=2)

    assert [message.role for message in result] == ["user", "assistant"]
    assert result[0].id == UUID("11111111-1111-1111-1111-111111111111")
    assert query.filters == [("world_id", "shared_world")]
    assert query.descending is True
    assert query.requested_limit == 2


@pytest.mark.parametrize("limit", [0, 101])
def test_get_recent_messages_rejects_invalid_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        conversation_service.get_recent_messages(limit)
