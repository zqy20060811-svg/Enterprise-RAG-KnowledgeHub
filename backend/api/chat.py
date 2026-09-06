"""
对话接口：SSE 流式问答
"""

import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from core.dependencies import get_rag_service
from services.rag_service import RagService
from schemas.chat import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.post("/stream", summary="流式问答（SSE）")
async def chat_stream(
    req: ChatRequest,
    rag_service: RagService = Depends(get_rag_service),
):
    session_id = req.session_id or str(uuid.uuid4())

    async def event_generator():
        async for token in rag_service.ask_stream(req.query, session_id):
            yield token

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")
