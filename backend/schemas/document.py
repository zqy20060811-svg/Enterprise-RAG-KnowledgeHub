"""文档相关请求/响应模型"""

from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    filename: str
    status: str
    chunk_count: int = 0


class DocumentInfo(BaseModel):
    filename: str
    chunk_count: int
    create_time: Optional[str] = None
