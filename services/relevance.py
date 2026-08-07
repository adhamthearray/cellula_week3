from __future__ import annotations

import requests

from config import settings
from utils.logger import logger


class RelevanceChecker:
    """Determines whether retrieved context is sufficient for code generation."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.OPENROUTER_API_KEY

    def is_relevant(self, question: str, context: str) -> bool:
        if not self.api_key:
            return True
        try:
            payload = {
                "model": settings.MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "Determine if the context is sufficient. Answer ONLY Relevant or Not Relevant"},
                    {"role": "user", "content": f"Question:\n{question}\n\nRetrieved Context:\n{context}"},
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
            answer = response.json()["choices"][0]["message"]["content"].strip().lower()
            return "relevant" in answer
        except Exception as exc:  # pragma: no cover
            logger.warning("Relevance check failed: %s", exc)
            return True
