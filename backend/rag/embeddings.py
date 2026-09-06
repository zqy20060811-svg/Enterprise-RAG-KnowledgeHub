"""
嵌入模型工厂
提供统一的 Embeddings 接口，当前使用本地 BGE 中文模型
"""

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from core.config import settings


def get_embeddings():
    """获取嵌入模型实例（本地 BGE，CPU 运行，无需 API Key）"""
    return HuggingFaceBgeEmbeddings(
        model_name=settings.embedding_model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
