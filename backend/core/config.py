"""
配置中心
使用 pydantic-settings 从 .env 读取所有配置，集中管理
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===================== 运行环境 =====================
    environment: str = Field(default="dev", description="dev: Chroma / prod: PGVector")

    # ===================== 服务配置 =====================
    host: str = "127.0.0.1"
    port: int = 8000

    # ===================== 大模型配置 =====================
    deepseek_api_key: str = Field(default="", description="DeepSeek API Key")
    chat_model_name: str = Field(default="deepseek-chat")

    # ===================== 嵌入模型配置 =====================
    embedding_model_name: str = Field(default="BAAI/bge-small-zh-v1.5")

    # ===================== 重排序模型 =====================
    reranker_model_name: str = Field(default="BAAI/bge-reranker-v2-m3")

    # ===================== 向量库配置 =====================
    chroma_persist_dir: str = Field(default="./data/chroma_db")
    chroma_collection_name: str = Field(default="rag_knowledge_base")
    pgvector_connection_string: str = Field(
        default="postgresql+psycopg2://postgres:password@localhost:5432/rag_db"
    )
    pgvector_collection_name: str = Field(default="rag_knowledge_base")

    # ===================== 检索配置 =====================
    retrieval_top_k: int = Field(default=20, description="混合检索候选数量")
    rerank_top_n: int = Field(default=3, description="Reranker 精排后返回数量")
    confidence_threshold: float = Field(
        default=0.3, description="拒答阈值：最高分低于此值则拒答"
    )

    # ===================== 分块配置 =====================
    chunk_size: int = 1000
    chunk_overlap: int = 100

    # ===================== 会话配置 =====================
    session_ttl_seconds: int = Field(default=3600, description="会话上下文过期时间(秒)")

    @property
    def is_dev(self) -> bool:
        return self.environment.lower() == "dev"


settings = Settings()
