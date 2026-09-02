"""Routes for chatting with the shared world soul."""

from fastapi import APIRouter, Header, HTTPException, Query, status

from app.database import DatabaseConfigurationError
from app.schemas import ChatHistoryResponse, ChatRequest, ChatResponse
from app.security import verify_access_password
from app.services.conversation_service import get_recent_messages, save_conversation_turn
from app.services.llm import generate_chat_reply
from app.services.llm.factory import LLMConfigurationError
from app.services.world_service import get_world_state

router = APIRouter(prefix="/api", tags=["chat"])

@router.get("/chat/history", response_model=ChatHistoryResponse)
def read_chat_history(
    limit: int = Query(default=20, ge=1, le=100),
    access_password: str = Header(alias="X-Access-Password"),
) -> ChatHistoryResponse:
    """Return recent shared-world messages in chronological order."""
    verify_access_password(access_password)
    try:
        return ChatHistoryResponse(messages=get_recent_messages(limit))
    except DatabaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to read conversation history from Supabase.",
        ) from exc


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
        reply = generate_chat_reply(request.message, world_state)
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate a reply.",
        ) from exc

    try:
        save_conversation_turn(request.message, reply)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to save the conversation turn to Supabase.",
        ) from exc

    return ChatResponse(
        reply=reply,
        world_state=world_state,
        new_memories=[],
    )
