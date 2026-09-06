"""
知识库管理接口
"""

from fastapi import APIRouter, Depends
from core.dependencies import get_kb_service
from services.kb_service import KnowledgeBaseService

router = APIRouter(prefix="/api/kb", tags=["知识库管理"])


@router.post("/clear", summary="清空知识库")
async def clear_kb(kb_service: KnowledgeBaseService = Depends(get_kb_service)):
    msg = kb_service.clear_all()
    return {"code": 200, "msg": msg}
