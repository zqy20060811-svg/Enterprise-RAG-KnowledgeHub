"""
知识库管理服务
"""

from typing import List
from rag.vector_store import BaseVectorStore
from rag.retriever import HybridRetriever
from services.document_service import DocumentService


class KnowledgeBaseService:
    """知识库管理：文档列表、删除、清空"""

    def __init__(self, rag_service):
        self.rag = rag_service
        self.doc_service = DocumentService(rag_service.vector_store, rag_service.retriever)

    def list_documents(self) -> List[dict]:
        return self.doc_service.list_documents()

    def delete_document(self, filename: str) -> str:
        return self.doc_service.delete_by_source(filename)

    def clear_all(self) -> str:
        self.rag.vector_store.clear()
        self.rag.retriever._rebuild_bm25_index()
        self.doc_service._md5_set.clear()
        return "知识库已清空"
