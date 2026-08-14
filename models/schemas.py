from typing import Any, List, Optional

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


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    table_name: str
    rows: int
    columns: List[str]


class TextAnalysisRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)


class DataAnalysisResponse(BaseModel):
    dataset_id: str
    query: str
    transcription: Optional[str] = None
    generated_sql: str
    columns: List[str]
    rows: List[dict[str, Any]]
    row_count: int
    analysis: str
