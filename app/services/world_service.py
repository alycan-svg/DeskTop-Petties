"""World-state service for the initial shared Persona Core prototype."""

from app.schemas import WorldState


def get_default_world_state() -> WorldState:
    """Return the default shared world state used before database integration."""
    return WorldState()
