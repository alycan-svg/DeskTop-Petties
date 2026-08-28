"""Persist shared-world conversation turns in Supabase."""

from typing import Any

from app.config import get_settings
from app.database import get_supabase_client
from app.schemas import Message

MESSAGE_COLUMNS = "id,world_id,role,content,created_at"


def save_conversation_turn(
    user_message: str,
    assistant_message: str,
) -> list[dict[str, Any]]:
    """Store one user/assistant turn with a single Supabase insert request."""
    world_id = get_settings().world_id
    rows = [
        {"world_id": world_id, "role": "user", "content": user_message},
        {
            "world_id": world_id,
            "role": "assistant",
            "content": assistant_message,
        },
    ]
    response = get_supabase_client().table("messages").insert(rows).execute()
    if not response.data or len(response.data) != len(rows):
        raise RuntimeError("Supabase did not return the complete conversation turn.")
    return response.data


def get_recent_messages(limit: int = 20) -> list[Message]:
    """Return the newest shared-world messages in chronological order."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    response = (
        get_supabase_client()
        .table("messages")
        .select(MESSAGE_COLUMNS)
        .eq("world_id", get_settings().world_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    newest_first = response.data or []
    return [Message.model_validate(row) for row in reversed(newest_first)]
