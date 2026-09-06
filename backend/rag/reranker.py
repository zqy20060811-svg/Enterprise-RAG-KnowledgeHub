"""
重排序器（Reranker）
使用 bge-reranker 对混合检索的候选 chunk 二次精排
"""

from typing import List, Tuple
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from core.config import settings


class Reranker:
    """基于 bge-reranker 的精排器"""

    def __init__(self):
        self.model = CrossEncoder(settings.reranker_model_name)

    def rerank(
        self, query: str, candidates: List[Tuple[Document, float]], top_n: int = None
    ) -> List[Tuple[Document, float]]:
        """
        对候选文档精排
        返回: [(Document, rerank_score), ...] 前 top_n 个
        """
        top_n = top_n or settings.rerank_top_n
        if not candidates:
            return []

        # 构造 (query, doc) 对
        pairs = [[query, doc.page_content] for doc, _ in candidates]
        scores = self.model.predict(pairs)

        # 绑定分数并排序
        scored = [
            (candidates[i][0], float(scores[i])) for i in range(len(candidates))
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]
