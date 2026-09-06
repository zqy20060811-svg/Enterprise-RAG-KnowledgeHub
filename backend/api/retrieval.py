"""
检索接口（调试用，直接返回检索结果）
"""

from fastapi import APIRouter, Depends
from core.dependencies import get_rag_service
from services.rag_service import RagService
from schemas.retrieval import RetrievalRequest, RetrievalResult

router = APIRouter(prefix="/api/retrieval", tags=["检索"])


@router.post("/search", summary="检索（返回候选 chunk + 分数）")
async def search(
    req: RetrievalRequest,
    rag_service: RagService = Depends(get_rag_service),
):
    ranked = rag_service.retrieve(req.query)
    results = [
        RetrievalResult(
            content=doc.page_content,
            source=doc.metadata.get("source", ""),
            page=doc.metadata.get("page"),
            chunk_index=doc.metadata.get("chunk_index"),
            score=round(float(score), 4),
        )
        for doc, score in ranked
    ]
    return {"code": 200, "msg": "success", "data": results}
