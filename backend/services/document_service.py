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

                

    @staticmethod
    def _make_doc_id(source_key: str, chunk_index: int) -> str:
        """确定性 ID：同来源同序号的分块覆盖写入（upsert 语义）"""
        return hashlib.sha256(f"{source_key}::{chunk_index}".encode("utf-8")).hexdigest()

    def batch_ingest(self, items: List[dict]) -> dict:
        """
        批量入库：循环内不重建 BM25，结束后统一重建一次
        items: [{content, source, source_type, source_url, license, crawl_time}, ...]
        返回: {"added": 新增文档数, "skipped": 跳过数, "chunk_count": 入库分块总数}
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_chunks: List[str] = []
        all_metas: List[dict] = []
        all_ids: List[str] = []
        stats = {"added": 0, "skipped": 0, "chunk_count": 0}

        for item in items:
            cleaned = clean_text(item.get("content", ""))
            if not cleaned:
                stats["skipped"] += 1
                continue

            content_md5 = get_content_md5(cleaned)
            if content_md5 in self._md5_set:
                stats["skipped"] += 1
                continue

            chunks = split_text(cleaned)
            source = item.get("source", "unknown")
            source_key = item.get("source_url") or source
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metas.append(
                    {
                        "source": source,
                        "source_type": item.get("source_type", "upload"),
                        "source_url": item.get("source_url", ""),
                        "license": item.get("license", ""),
                        "crawl_time": item.get("crawl_time", ""),
                        "chunk_index": i,
                        "content_md5": content_md5,
                        "create_time": now,
                    }
                )
                all_ids.append(self._make_doc_id(source_key, i))
            self._md5_set.add(content_md5)
            stats["added"] += 1
            stats["chunk_count"] += len(chunks)

        if all_chunks:
            self.vector_store.add_documents(all_chunks, all_metas, all_ids)
            self.retriever._rebuild_bm25_index()

        return stats

    def upload(self, file_bytes: bytes, filename: str) -> Tuple[str, int]:
        """
        完整上传流程（单文件入口，复用 batch_ingest）
        返回: (状态消息, 分块数量)
        """
        content = parse_document(file_bytes, filename)
        cleaned = clean_text(content)
        if not cleaned:
            return "文档内容为空", 0

        stats = self.batch_ingest(
            [
                {
                    "content": content,
                    "source": os.path.splitext(filename)[0],
                    "source_type": "upload",
                }
            ]
        )
        if stats["added"] == 0:
            return "[跳过] 内容已存在", 0
        return "[成功] 已存入向量库", stats["chunk_count"]

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
