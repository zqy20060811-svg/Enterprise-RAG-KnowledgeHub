"""
会话记忆管理
内存 dict 存储，带 TTL 过期
替代原来的 JSON 文件方案，无需外部依赖
"""

import time
import threading
from typing import Dict, List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from core.config import settings


class InMemoryChatHistory(BaseChatMessageHistory):
    """内存版会话历史，带 TTL"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._messages: List[BaseMessage] = []
        self._last_access = time.time()

    def add_messages(self, messages: List[BaseMessage]) -> None:
        self._messages.extend(messages)
        self._last_access = time.time()

    @property
    def messages(self) -> List[BaseMessage]:
        self._last_access = time.time()
        return self._messages

    def clear(self) -> None:
        self._messages = []


class MemoryStore:
    """会话存储器：单例管理所有会话，带 TTL 清理"""

    def __init__(self):
        self._store: Dict[str, InMemoryChatHistory] = {}
        self._lock = threading.Lock()

    def get_history(self, session_id: str) -> InMemoryChatHistory:
        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = InMemoryChatHistory(session_id)
            return self._store[session_id]

    def cleanup_expired(self):
        """清理过期会话"""
        now = time.time()
        with self._lock:
            expired = [
                sid
                for sid, h in self._store.items()
                if now - h._last_access > settings.session_ttl_seconds
            ]
            for sid in expired:
                del self._store[sid]


memory_store = MemoryStore()
