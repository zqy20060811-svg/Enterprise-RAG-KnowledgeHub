"""检索相关请求/响应模型"""

from pydantic import BaseModel
from typing import Optional


class RetrievalRequest(BaseModel):
    query: str


class RetrievalResult(BaseModel):
    content: str
    source: str
    page: Optional[str] = None
    chunk_index: Optional[int] = None
    score: float
