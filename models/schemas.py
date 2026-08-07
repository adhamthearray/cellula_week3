from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat request payload."""

    message: str = Field(..., min_length=1)


class LearnRequest(BaseModel):
    """Payload for learning a new solution."""

    question: str = Field(..., min_length=1)
    solution: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Structured chat response returned by the API."""

    intent: str
    answer: str
    retrieved_docs: List[dict]
    execution_result: str
