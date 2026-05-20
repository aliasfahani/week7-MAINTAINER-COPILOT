from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infra.db import get_db
from app.routes.dependencies import get_current_user
from app.schemas import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return handle_chat(
        user=user,
        db=db,
        message=payload.message,
        conversation_id=payload.conversation_id,
        issue=payload.issue.model_dump() if payload.issue else None,
    )
