"""
大模型工厂
提供统一的 ChatModel 接口，当前使用 DeepSeek
"""

import os
from langchain_deepseek import ChatDeepSeek
from core.config import settings
from core.exceptions import BizException


def get_chat_model():
    """获取对话大模型实例"""
    api_key = settings.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise BizException("DEEPSEEK_API_KEY 未配置，请在 .env 中设置", code=500)
    return ChatDeepSeek(
        model=settings.chat_model_name,
        api_key=api_key,
        temperature=0.3,
    )
