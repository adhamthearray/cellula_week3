from fastapi import APIRouter, HTTPException

from models.schemas import ChatRequest, ChatResponse, LearnRequest
from services.rag import AssistantService

router = APIRouter()
service = AssistantService()


@router.get("/health")
def health() -> str:
    return "OK"


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        intent, answer, retrieved_docs, execution_result = service.handle_message(request.message)
        return ChatResponse(
            intent=intent,
            answer=answer,
            retrieved_docs=retrieved_docs,
            execution_result=execution_result,
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/learn")
def learn(payload: LearnRequest) -> dict:
    try:
        return {"message": service.learn_solution(payload.question, payload.solution)}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rebuild")
def rebuild() -> dict:
    try:
        return {"message": service.rebuild_database()}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc)) from exc
