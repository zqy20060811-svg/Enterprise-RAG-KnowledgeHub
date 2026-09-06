"""
RAG 服务：全链路编排
Query Rewrite → Hybrid Retrieval → Reranker → 置信度拒答 → LLM 流式生成
"""

from typing import List, Tuple, AsyncIterator, Dict, Any
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser

from core.config import settings
from rag.vector_store import get_vector_store, BaseVectorStore
from rag.retriever import HybridRetriever
from rag.reranker import Reranker
from rag.query_rewriter import rewrite_query
from rag.llm import get_chat_model
from rag.prompts import QA_PROMPT
from utils.memory import memory_store


class RagService:
    """RAG 问答核心服务"""

    def __init__(self):
        self.vector_store: BaseVectorStore = get_vector_store()
        self.retriever = HybridRetriever(self.vector_store)
        self.reranker = Reranker()
        self.chat_model = get_chat_model()

    # ===================== 检索阶段 =====================
    def retrieve(self, query: str, history: List[BaseMessage] = None) -> List[Tuple[Document, float]]:
        """
        完整检索链路：改写 → 混合检索 → 重排序
        返回: [(Document, rerank_score), ...]
        """
        # 1. Query Rewrite
        rewritten = rewrite_query(query, history or [])

        # 2. Hybrid Retrieval（Dense + BM25）
        candidates = self.retriever.retrieve(rewritten, top_k=settings.retrieval_top_k)

        # 3. Reranker 精排
        ranked = self.reranker.rerank(rewritten, candidates, top_n=settings.rerank_top_n)
        return ranked

    # ===================== 置信度判断 =====================
    @staticmethod
    def check_confidence(ranked: List[Tuple[Document, float]]) -> bool:
        """
        判断检索结果是否可信
        返回 True 表示可以回答，False 表示应拒答
        """
        if not ranked:
            return False
        best_score = ranked[0][1]
        return best_score >= settings.confidence_threshold

    # ===================== 来源格式化 =====================
    @staticmethod
    def format_context(ranked: List[Tuple[Document, float]]) -> str:
        """把检索结果格式化为提示词上下文"""
        if not ranked:
            return "无相关参考资料"
        parts = []
        for i, (doc, score) in enumerate(ranked, 1):
            source = doc.metadata.get("source", "未知")
            parts.append(f"[参考资料{i}] 来源：{source}\n内容：{doc.page_content}")
        return "\n\n".join(parts)

    @staticmethod
    def format_sources(ranked: List[Tuple[Document, float]]) -> List[Dict[str, Any]]:
        """构造来源引用列表（用于返回给前端溯源展示）"""
        sources = []
        for doc, score in ranked:
            sources.append({
                "source": doc.metadata.get("source", "未知"),
                "page": doc.metadata.get("page"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "score": round(float(score), 4),
            })
        return sources

    # ===================== 流式问答 =====================
    async def ask_stream(
        self, query: str, session_id: str
    ) -> AsyncIterator[str]:
        """
        流式问答（SSE）
        1. 获取会话历史
        2. 检索 + 重排
        3. 置信度判断：低于阈值直接拒答
        4. 组装提示词，LLM 流式生成
        5. 末尾输出来源引用
        """
        # 1. 获取/创建会话
        history = memory_store.get_history(session_id)

        # 2. 检索
        ranked = self.retrieve(query, history.messages)

        # 3. 置信度拒答
        if not self.check_confidence(ranked):
            yield "抱歉，知识库中未找到与您问题相关的资料。\n"
            return

        # 4. 组装提示词
        context = self.format_context(ranked)
        prompt = QA_PROMPT.format_messages(
            context=context,
            history=history.messages,
            input=query,
        )

        # 5. LLM 流式生成
        full_answer = ""
        async for chunk in self.chat_model.astream(prompt):
            content = chunk.content
            if content:
                full_answer += content
                yield content

        # 6. 记录对话历史
        from langchain_core.messages import HumanMessage, AIMessage
        history.add_messages([HumanMessage(content=query), AIMessage(content=full_answer)])

        # 7. 输出来源引用
        sources = self.format_sources(ranked)
        if sources:
            yield "\n\n--- 来源 ---\n"
            for i, s in enumerate(sources, 1):
                yield f"[{i}] {s['source']} · chunk {s.get('chunk_index', '-')} · 相关度 {s['score']}\n"
