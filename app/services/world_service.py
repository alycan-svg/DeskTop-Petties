"""Read the shared Persona Core state from Supabase."""

from app.config import get_settings
from app.database import get_supabase_client
from app.schemas import WorldState


def get_default_world_state() -> WorldState:
    """Return defaults used by the SQL seed and recovery insertion."""
    return WorldState(world_id=get_settings().world_id)


def get_world_state() -> WorldState:
    """Return the configured shared world's state from Supabase.

    If the world exists but its state row is absent, create the default state.
    This makes a newly created world self-healing without masking connection or
    permission failures from Supabase.
    """
    settings = get_settings()
    client = get_supabase_client()
    response = (
        client.table("world_state")
        .select(
            "world_id,mood,color,animation,energy,friendliness,curiosity,"
            "chaos,stress,loneliness"
        )
        .eq("world_id", settings.world_id)
        .limit(1)
        .execute()
    )

    if response.data:
        return WorldState.model_validate(response.data[0])

    default_state = get_default_world_state()
    inserted = (
        client.table("world_state")
        .insert(default_state.model_dump())
        .execute()
    )
    if not inserted.data:
        raise RuntimeError("Supabase did not return the inserted world state.")
    return WorldState.model_validate(inserted.data[0])
