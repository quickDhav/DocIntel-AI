"""Chat router — conversational RAG interface with session history."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatMessage
from app.services.rag import RAGEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])




class ChatRequest(BaseModel):
    """Incoming chat message."""

    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(..., min_length=1, max_length=64)


class CitationItem(BaseModel):
    """A single citation reference."""

    document_id: str
    document_name: str
    page_number: int


class ChatResponse(BaseModel):
    """Response to a chat message."""

    answer: str
    citations: list[CitationItem]
    session_id: str


class ClearRequest(BaseModel):
    """Request to clear a chat session."""

    session_id: str = Field(..., min_length=1, max_length=64)




@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """Send a message and receive a RAG-powered answer with citations.

    The conversation history for the given ``session_id`` is
    automatically loaded and passed to the RAG engine for multi-turn
    context.
    """
    history_records = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == request.session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )
    chat_history = [
        {"role": msg.role, "content": msg.content} for msg in history_records
    ]

    user_msg = ChatMessage(
        session_id=request.session_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    db.commit()

    rag = RAGEngine()
    try:
        result = rag.answer(request.message, chat_history)
    except Exception as exc:
        logger.exception("RAG engine error: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to generate answer")

    assistant_msg = ChatMessage(
        session_id=request.session_id,
        role="assistant",
        content=result["answer"],
        citations_json=json.dumps(result.get("citations", [])),
    )
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(
        answer=result["answer"],
        citations=[CitationItem(**c) for c in result.get("citations", [])],
        session_id=request.session_id,
    )


@router.get("/history")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Return the conversation history for a session.

    Query params:
        session_id: The session identifier.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    result = []
    for msg in messages:
        item = {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
        }
        if msg.citations_json:
            try:
                item["citations"] = json.loads(msg.citations_json)
            except json.JSONDecodeError:
                item["citations"] = []
        else:
            item["citations"] = []
        result.append(item)

    return {"session_id": session_id, "messages": result}


@router.post("/clear")
async def clear_chat(
    request: ClearRequest,
    db: Session = Depends(get_db),
):
    """Delete all messages for a given session.

    Args:
        request: Contains the ``session_id`` to clear.
    """
    deleted = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == request.session_id)
        .delete()
    )
    db.commit()
    return {"session_id": request.session_id, "messages_deleted": deleted}
