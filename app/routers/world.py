"""Routes for reading the shared world's current state."""

from fastapi import APIRouter, HTTPException, status

from app.database import DatabaseConfigurationError
from app.schemas import WorldState
from app.services.world_service import get_world_state

router = APIRouter(prefix="/api/world", tags=["world"])


@router.get("/state", response_model=WorldState)
def read_world_state() -> WorldState:
    """Return the shared pet's current state stored in Supabase."""
    try:
        return get_world_state()
    except DatabaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to read the shared world state from Supabase.",
        ) from exc
