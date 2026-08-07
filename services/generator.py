from __future__ import annotations

from typing import List, Optional

import requests

from config import settings
from utils.logger import logger


class CodeGenerator:
    """Generates code from a prompt and optional retrieved context."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.OPENROUTER_API_KEY

    def generate(self, prompt: str, context: Optional[List[str]] = None) -> str:
        if not self.api_key:
            return "OpenRouter API key is not configured. Please set OPENROUTER_API_KEY in the environment."

        context_text = ""
        if context:
            context_text = "\n\n".join(context)

        payload = {
            "model": settings.MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert software engineer. Generate the requested code. Use the retrieved context. If information is missing say so. Do not hallucinate.",
                },
                {"role": "user", "content": f"Prompt:\n{prompt}\n\nRetrieved Context:\n{context_text}"},
            ],
        }
        try:
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
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.error("Code generation failed: %s", exc)
            return f"Code generation failed: {exc}"
