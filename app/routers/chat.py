"""Routes for chatting with the shared world soul."""

from fastapi import APIRouter, HTTPException, status

from app.database import DatabaseConfigurationError
from app.schemas import ChatRequest, ChatResponse
from app.security import verify_access_password
from app.services.conversation_service import save_conversation_turn
from app.services.world_service import get_world_state

router = APIRouter(prefix="/api", tags=["chat"])

PLACEHOLDER_REPLY = "我听到了。云端的我还在苏醒，接下来会把这些话沉淀成长期记忆。"


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Persist a chat turn and return it with the live cloud world state."""
    verify_access_password(request.password)
    try:
        world_state = get_world_state()
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

    try:
        save_conversation_turn(request.message, PLACEHOLDER_REPLY)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to save the conversation turn to Supabase.",
        ) from exc

    return ChatResponse(
        reply=PLACEHOLDER_REPLY,
        world_state=world_state,
        new_memories=[],
    )
