"""
多格式文档解析
支持 TXT / PDF / DOCX
"""

import os
from io import BytesIO
from typing import Tuple


def parse_document(file_bytes: bytes, filename: str) -> str:
    """
    解析文档，返回纯文本
    """
    ext = os.path.splitext(filename)[-1].lower()

    if ext == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")

    elif ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif ext in (".docx", ".doc"):
        from docx import Document
        doc = Document(BytesIO(file_bytes))
        return "\n".join(para.text for para in doc.paragraphs)

    else:
        raise ValueError(f"不支持的文件格式：{ext}，仅支持 .txt/.pdf/.docx")
