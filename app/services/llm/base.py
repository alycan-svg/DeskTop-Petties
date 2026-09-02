"""Provider-independent LLM message and interface definitions."""

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class LLMMessage:
    """A minimal chat message understood by every provider adapter."""

    role: Literal["system", "user", "assistant"]
    content: str


class LLMProvider(Protocol):
    """Contract implemented by mock and future cloud model providers."""

    def generate(self, messages: list[LLMMessage]) -> str:
        """Generate one assistant response from chronological context."""
        ...
