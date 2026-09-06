"""
依赖注入
通过 FastAPI Depends 提供 RAG 相关服务单例，避免模块级初始化
"""

from functools import lru_cache

from services.rag_service import RagService
from services.document_service import DocumentService
from services.kb_service import KnowledgeBaseService


@lru_cache
def get_rag_service() -> RagService:
    return RagService()


@lru_cache
def get_document_service() -> DocumentService:
    rag = get_rag_service()
    return DocumentService(rag.vector_store, rag.retriever)


@lru_cache
def get_kb_service() -> KnowledgeBaseService:
    return KnowledgeBaseService(get_rag_service())
