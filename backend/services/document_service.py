"""
文档服务：解析、清洗、分块、去重、入库
"""

import os
import hashlib
from datetime import datetime
from typing import List, Tuple

from langchain_core.documents import Document

from rag.vector_store import BaseVectorStore
from rag.retriever import HybridRetriever
from utils.file_parser import parse_document
from utils.text_splitter import clean_text, split_text, get_content_md5


class DocumentService:
    """文档处理服务"""

    def __init__(self, vector_store: BaseVectorStore, retriever: HybridRetriever):
        self.vector_store = vector_store
        self.retriever = retriever
        self._md5_set: set = set()
        self._init_md5()

    def _init_md5(self):
        """启动时从向量库重建 MD5 去重集合"""
        docs = self.vector_store.get_all_documents()
        for doc in docs:
            md5 = doc.metadata.get("content_md5")
            if md5:
                self._md5_set.add(md5)

    def upload(self, file_bytes: bytes, filename: str) -> Tuple[str, int]:
        """
        完整上传流程
        返回: (状态消息, 分块数量)
        """
        # 1. 解析文档
        content = parse_document(file_bytes, filename)
        cleaned = clean_text(content)
        if not cleaned:
            return "文档内容为空", 0

        # 2. MD5 去重
        content_md5 = get_content_md5(cleaned)
        if content_md5 in self._md5_set:
            return "[跳过] 内容已存在", 0

        # 3. 分块
        chunks = split_text(cleaned)

        # 4. 构造元数据（文件名、页码、chunk_index、md5）
        base_name = os.path.splitext(filename)[0]
        metadatas = [
            {
                "source": base_name,
                "chunk_index": i,
                "content_md5": content_md5,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            for i in range(len(chunks))
        ]

        # 5. 写入向量库
        self.vector_store.add_documents(chunks, metadatas)
        self._md5_set.add(content_md5)

        # 6. 重建 BM25 索引
        self.retriever._rebuild_bm25_index()

        return "[成功] 已存入向量库", len(chunks)

    def delete_by_source(self, filename: str) -> str:
        """按文件名删除"""
        docs = self.vector_store.get_all_documents()
        targets = [d for d in docs if d.metadata.get("source") == filename]
        if not targets:
            return f"文件：{filename} 不存在"
        # 清理对应 MD5
        for doc in targets:
            md5 = doc.metadata.get("content_md5")
            if md5 and md5 in self._md5_set:
                self._md5_set.remove(md5)
        self.vector_store.delete_by_source(filename)
        self.retriever._rebuild_bm25_index()
        return f"已删除文件：{filename}（共 {len(targets)} 个分块）"

    def list_documents(self) -> List[dict]:
        """列出所有已上传文档（按文件名聚合）"""
        docs = self.vector_store.get_all_documents()
        file_map: dict = {}
        for doc in docs:
            src = doc.metadata.get("source", "unknown")
            if src not in file_map:
                file_map[src] = {
                    "filename": src,
                    "chunk_count": 0,
                    "create_time": doc.metadata.get("create_time"),
                }
            file_map[src]["chunk_count"] += 1
        return list(file_map.values())
