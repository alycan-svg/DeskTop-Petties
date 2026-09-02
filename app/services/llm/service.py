"""Build Persona Core context and request a provider-independent reply."""

from app.config import get_settings
from app.schemas import Message, WorldState
from app.services.conversation_service import get_recent_messages
from app.services.llm.base import LLMMessage
from app.services.llm.factory import get_llm_provider


def build_chat_context(
    history: list[Message],
    user_message: str,
    world_state: WorldState,
) -> list[LLMMessage]:
    """Build chronological model context from persona state and recent chat."""
    system_prompt = (
        "你是共享桌面宠物‘世界之魂’。回答要自然、友善、有一点生命感；"
        "不要声称记得上下文中没有出现的事情。"
        f"当前状态：心情={world_state.mood}，活力={world_state.energy}，"
        f"好奇心={world_state.curiosity}，压力={world_state.stress}。"
    )
    context = [LLMMessage(role="system", content=system_prompt)]
    context.extend(
        LLMMessage(role=message.role, content=message.content)
        for message in history
        if message.role in {"user", "assistant", "system"}
    )
    context.append(LLMMessage(role="user", content=user_message))
    return context


def generate_chat_reply(user_message: str, world_state: WorldState) -> str:
    """Generate a reply using bounded recent history and the selected provider."""
    settings = get_settings()
    history = get_recent_messages(settings.llm_history_limit)
    context = build_chat_context(history, user_message, world_state)
    reply = get_llm_provider().generate(context).strip()
    if not reply:
        raise RuntimeError("The LLM provider returned an empty reply.")
    return reply
