"""Deterministic local provider used before choosing a real LLM vendor."""

from app.services.llm.base import LLMMessage


class MockLLMProvider:
    """Produce a visible, testable response without an external API call."""

    def generate(self, messages: list[LLMMessage]) -> str:
        user_messages = [message.content for message in messages if message.role == "user"]
        current_message = user_messages[-1]
        previous_count = max(len(messages) - 2, 0)
        return (
            f"（Mock 模式）我收到了：“{current_message}”。"
            f"这次回答参考了此前 {previous_count} 条消息。"
        )
