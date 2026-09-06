"""对话相关请求/响应模型"""

from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class SourceRef(BaseModel):
    """来源引用"""
    source: str
    page: Optional[str] = None
    chunk_index: Optional[int] = None
    score: float
