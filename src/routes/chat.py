"""
Router: Chat
POST /v1/chat/stream — SSE streaming real-time.
"""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.core.cache import get_vectorstore
from src.core.security import is_safe_query
from src.schemas.chat import ERROR_RESPONSES, ChatRequest
from src.services import session_store
from src.services.llm import ask_llm
from src.services.rag import get_context
from src.services.vectorstore_cache import history_to_string

router = APIRouter(prefix="/v1", tags=["Chat"])


@router.post("/chat/stream", responses=ERROR_RESPONSES)
async def chat_stream(body: ChatRequest, request: Request):
    """SSE streaming — trả từng chunk text real-time, phù hợp UI typing effect."""
    is_safe, err = is_safe_query(body.message)
    if not is_safe:
        raise HTTPException(status_code=400, detail=err)

    payload = await session_store.load_vectorstore_payload(
        request.app.state.redis, body.session_id
    )
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail="Session không tồn tại hoặc đã hết hạn. Gọi lại /v1/ingest.",
        )

    chat_history = history_to_string(body.history)

    # Chuẩn bị context trong thread pool (CPU-bound, không block event loop)
    vectorstore = await asyncio.to_thread(get_vectorstore, body.session_id, payload)
    context = await asyncio.to_thread(get_context, vectorstore, body.message)

    def _sse_generator():
        for chunk in ask_llm(context, body.message, chat_history):
            if chunk:
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
