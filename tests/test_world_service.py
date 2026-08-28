"""Unit tests for reading and recovering the shared cloud world state."""

from types import SimpleNamespace

from app.services import world_service


class FakeQuery:
    """Small fluent stand-in for the Supabase query builder."""

    def __init__(self, select_data: list[dict], insert_data: list[dict]) -> None:
        self.select_data = select_data
        self.insert_data = insert_data
        self.inserted_payload: dict | None = None
        self.operation = "select"

    def select(self, _columns: str) -> "FakeQuery":
        return self

    def eq(self, _column: str, _value: str) -> "FakeQuery":
        return self

    def limit(self, _count: int) -> "FakeQuery":
        return self

    def insert(self, payload: dict) -> "FakeQuery":
        self.operation = "insert"
        self.inserted_payload = payload
        return self

    def execute(self) -> SimpleNamespace:
        data = self.insert_data if self.operation == "insert" else self.select_data
        return SimpleNamespace(data=data)


class FakeClient:
    def __init__(self, query: FakeQuery) -> None:
        self.query = query

    def table(self, table_name: str) -> FakeQuery:
        assert table_name == "world_state"
        return self.query


def test_get_world_state_reads_supabase(monkeypatch) -> None:
    cloud_state = {
        "world_id": "shared_world",
        "mood": "happy",
        "color": "green",
        "animation": "bounce",
        "energy": 90,
        "friendliness": 75,
        "curiosity": 88,
        "chaos": 12,
        "stress": 8,
        "loneliness": 3,
    }
    query = FakeQuery(select_data=[cloud_state], insert_data=[])
    monkeypatch.setattr(world_service, "get_supabase_client", lambda: FakeClient(query))

    result = world_service.get_world_state()

    assert result.mood == "happy"
    assert result.animation == "bounce"
    assert query.inserted_payload is None


def test_get_world_state_inserts_defaults_when_row_is_missing(monkeypatch) -> None:
    default = world_service.get_default_world_state().model_dump()
    query = FakeQuery(select_data=[], insert_data=[default])
    monkeypatch.setattr(world_service, "get_supabase_client", lambda: FakeClient(query))

    result = world_service.get_world_state()

    assert result.world_id == "shared_world"
    assert result.mood == "curious"
    assert query.inserted_payload == default
