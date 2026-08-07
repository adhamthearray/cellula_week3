from __future__ import annotations

from typing import List, Tuple

try:
    from langchain.memory import ConversationBufferMemory
except ImportError:  # pragma: no cover - fallback
    ConversationBufferMemory = None


class ConversationMemory:
    """Stores prior chat turns and injects them into prompts."""

    def __init__(self) -> None:
        if ConversationBufferMemory is not None:
            self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        else:
            self.memory = None
        self._history: List[Tuple[str, str]] = []

    def add_user_message(self, message: str) -> None:
        self._history.append(("user", message))
        if self.memory is not None:
            self.memory.chat_memory.add_user_message(message)

    def add_ai_message(self, message: str) -> None:
        self._history.append(("assistant", message))
        if self.memory is not None:
            self.memory.chat_memory.add_ai_message(message)

    def build_context(self) -> str:
        if self.memory is not None:
            try:
                return self.memory.load_memory_variables({})["chat_history"]
            except Exception:  # pragma: no cover
                pass

        if not self._history:
            return ""
        formatted: List[str] = []
        for role, text in self._history[-6:]:
            formatted.append(f"{role}: {text}")
        return "\n".join(formatted)
