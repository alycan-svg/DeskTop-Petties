"""Routes for reading the shared world's current state."""

from fastapi import APIRouter

from app.schemas import WorldState
from app.services.world_service import get_default_world_state

router = APIRouter(prefix="/api/world", tags=["world"])


@router.get("/state", response_model=WorldState)
def read_world_state() -> WorldState:
    """Return the shared pet's current state.

    In Step 1 this returns a default in-memory state. Later steps will read the
    same shape from Supabase so the PyQt6 desktop pet does not need to change.
    """
    return get_default_world_state()
