"""
混合检索器：Dense（向量） + BM25（关键词）
召回后合并去重，交由 Reranker 精排
"""

from typing import List, Tuple
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
import jieba

from core.config import settings
from rag.vector_store import BaseVectorStore


def _tokenize(text: str) -> List[str]:
    """中文分词（jieba），BM25 输入需要分词后的 token 列表"""
    return list(jieba.cut(text))


class HybridRetriever:
    """混合检索器：向量召回 + BM25 关键词召回"""

    def __init__(self, vector_store: BaseVectorStore):
        self.vector_store = vector_store
        self.bm25: BM25Okapi = None
        self.docs: List[Document] = []
        self._rebuild_bm25_index()

    def _rebuild_bm25_index(self):
        """从向量库全量重建 BM25 索引（启动时 / 写入后调用）"""
        self.docs = self.vector_store.get_all_documents()
        if not self.docs:
            self.bm25 = None
            return
        tokenized_corpus = [_tokenize(d.page_content) for d in self.docs]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def retrieve(self, query: str, top_k: int = None) -> List[Tuple[Document, float]]:
        """
        混合检索
        返回: [(Document, combined_score), ...] 按分数降序
        """
        top_k = top_k or settings.retrieval_top_k
        results: dict = {}  # doc_id -> (Document, score)

        # 1. 向量检索（Dense）
        dense_results = self.vector_store.similarity_search_with_score(query, k=top_k)
        for doc, score in dense_results:
            # Chroma 返回的是距离，越小越相似；归一化为相似度
            sim = 1.0 / (1.0 + score)
            key = self._doc_key(doc)
            if key not in results or sim > results[key][1]:
                results[key] = (doc, sim)

        # 2. BM25 检索（关键词）
        if self.bm25 is not None:
            tokenized_query = _tokenize(query)
            bm25_scores = self.bm25.get_scores(tokenized_query)
            # 取 top_k 个最高分的索引
            top_indices = sorted(
                range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
            )[:top_k]
            max_score = max(bm25_scores) if bm25_scores.max() > 0 else 1.0
            for idx in top_indices:
                if bm25_scores[idx] <= 0:
                    continue
                doc = self.docs[idx]
                # BM25 分数归一化到 [0, 1]
                norm_score = bm25_scores[idx] / max_score
                key = self._doc_key(doc)
                if key in results:
                    # 合并：加权求和（向量 0.6 + BM25 0.4）
                    existing_score = results[key][1]
                    combined = 0.6 * existing_score + 0.4 * norm_score
                    results[key] = (doc, combined)
                else:
                    results[key] = (doc, 0.4 * norm_score)

        # 按分数降序排序
        ranked = sorted(results.values(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    @staticmethod
    def _doc_key(doc: Document) -> str:
        """用 文本内容+来源 作为文档唯一标识，用于去重"""
        source = doc.metadata.get("source", "")
        chunk_idx = doc.metadata.get("chunk_index", "")
        return f"{source}::{chunk_idx}::{doc.page_content[:50]}"
