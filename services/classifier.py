from __future__ import annotations

import re
from typing import Optional

import requests

from config import settings
from utils.logger import logger


class IntentClassifier:
    """Classifies a request as either explain or generate."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.OPENROUTER_API_KEY

    def classify(self, message: str) -> str:
        """Use an LLM when available, otherwise fallback to keyword heuristics."""
        if not message.strip():
            return "Generate"

        if self.api_key:
            try:
                payload = {
                    "model": settings.MODEL_NAME,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an intent classifier. Classify the following request. Only output one word. Explain or Generate.",
                        },
                        {"role": "user", "content": message},
                    ],
                }
                response = requests.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=settings.REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"].strip().lower()
                if "explain" in content:
                    return "Explain"
                return "Generate"
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.warning("Intent classification via LLM failed: %s", exc)

        lowered = message.lower()
        if re.search(r"\b(explain|what does|why does|line by line|describe)\b", lowered):
            return "Explain"
        return "Generate"
