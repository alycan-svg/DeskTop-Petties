"""Persist shared-world conversation turns in Supabase."""

from typing import Any

from app.config import get_settings
from app.database import get_supabase_client


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
