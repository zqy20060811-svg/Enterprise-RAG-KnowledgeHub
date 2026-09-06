"""
向量库抽象层
统一 Chroma（开发）与 PGVector（生产）的接口，通过 ENVIRONMENT 配置切换
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.vectorstores import PGVector

from core.config import settings
from rag.embeddings import get_embeddings


class BaseVectorStore(ABC):
    """向量库统一接口"""

    @abstractmethod
    def add_documents(self, chunks: List[str], metadatas: List[dict]) -> List[str]:
        """批量写入向量，返回 id 列表"""
        ...

    @abstractmethod
    def similarity_search_with_score(
        self, query: str, k: int, filter: Optional[dict] = None
    ) -> List[tuple]:
        """向量相似度检索，返回 [(Document, score), ...]"""
        ...

    @abstractmethod
    def delete_by_source(self, source: str) -> None:
        """按来源文件名删除"""
        ...

    @abstractmethod
    def get_all_documents(self) -> List[Document]:
        """获取所有文档（用于重建 BM25 索引）"""
        ...

    @abstractmethod
    def clear(self) -> None:
        """清空整个向量库"""
        ...


class ChromaVectorStore(BaseVectorStore):
    """Chroma 本地向量库（开发环境）"""

    def __init__(self):
        self.embeddings = get_embeddings()
        self.store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.chroma_persist_dir,
        )

    def add_documents(self, chunks, metadatas):
        return self.store.add_texts(texts=chunks, metadatas=metadatas)

    def similarity_search_with_score(self, query, k, filter=None):
        return self.store.similarity_search_with_score(query, k=k, filter=filter)

    def delete_by_source(self, source):
        self.store.delete(where={"source": source})

    def get_all_documents(self):
        data = self.store.get()
        docs = []
        for i, content in enumerate(data.get("documents", [])):
            meta = data["metadatas"][i] if data.get("metadatas") else {}
            docs.append(Document(page_content=content, metadata=meta))
        return docs

    def clear(self):
        self.store.delete_collection()
        # 重新初始化
        self.store = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.chroma_persist_dir,
        )


class PGVectorStore(BaseVectorStore):
    """PGVector 向量库（生产环境）"""

    def __init__(self):
        self.embeddings = get_embeddings()
        self.store = PGVector(
            collection_name=settings.pgvector_collection_name,
            embedding_function=self.embeddings,
            connection_string=settings.pgvector_connection_string,
        )

    def add_documents(self, chunks, metadatas):
        return self.store.add_texts(texts=chunks, metadatas=metadatas)

    def similarity_search_with_score(self, query, k, filter=None):
        return self.store.similarity_search_with_score(query, k=k, filter=filter)

    def delete_by_source(self, source):
        self.store.delete(where={"source": source})

    def get_all_documents(self):
        data = self.store.get()
        docs = []
        for i, content in enumerate(data.get("documents", [])):
            meta = data["metadatas"][i] if data.get("metadatas") else {}
            docs.append(Document(page_content=content, metadata=meta))
        return docs

    def clear(self):
        self.store.delete_collection()
        self.store = PGVector(
            collection_name=settings.pgvector_collection_name,
            embedding_function=self.embeddings,
            connection_string=settings.pgvector_connection_string,
        )


def get_vector_store() -> BaseVectorStore:
    """根据环境配置返回对应的向量库实例"""
    if settings.is_dev:
        return ChromaVectorStore()
    return PGVectorStore()
