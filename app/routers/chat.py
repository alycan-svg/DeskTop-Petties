"""Routes for chatting with the shared world soul."""

from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse
from app.security import verify_access_password
from app.services.world_service import get_default_world_state

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Return a placeholder reply until database and LLM services are added."""
    verify_access_password(request.password)
    return ChatResponse(
        reply="我听到了。云端的我还在苏醒，接下来会把这些话沉淀成长期记忆。",
        world_state=get_default_world_state(),
        new_memories=[],
    )
