"""
文本分块工具
结构化分块：优先按段落/标题边界切，保留语义完整性
"""

import re
import hashlib
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import settings


def clean_text(text: str) -> str:
    """文本清洗：去除多余空白和隐藏字符"""
    text = re.sub(r"[\s\xa0\u200b\ufeff]+", " ", text)
    return text.strip()


def get_content_md5(text: str) -> str:
    """计算文本 MD5，用于去重"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def split_text(text: str) -> list[str]:
    """
    结构化分块
    优先按段落/句号等语义边界切，chunk_size 和 overlap 可配置
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        length_function=len,
    )
    return splitter.split_text(text)
