"""
查询改写器（Query Rewrite）
将多轮对话中的指代/省略追问，结合历史改写成独立完整的检索 Query
"""

from typing import List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from rag.llm import get_chat_model


REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是一个查询改写助手。根据用户的对话历史，把当前的追问改写成一句"
        "不需要上下文也能独立理解的完整问题，用于知识库检索。"
        "只输出改写后的问题，不要解释。",
    ),
    ("user", "对话历史：\n{history}\n\n当前追问：{question}\n\n改写后的问题："),
])


def _format_history(history: List[BaseMessage]) -> str:
    lines = []
    for msg in history:
        role = "用户" if isinstance(msg, HumanMessage) else "助手"
        lines.append(f"{role}：{msg.content}")
    return "\n".join(lines)


def rewrite_query(question: str, history: List[BaseMessage]) -> str:
    """
    改写查询
    - 无历史时直接返回原问题
    - 有历史时调用 LLM 改写
    """
    if not history:
        return question

    llm = get_chat_model()
    chain = REWRITE_PROMPT | llm
    history_text = _format_history(history[-6:])  # 最多取最近 6 轮，控制 token
    result = chain.invoke({"history": history_text, "question": question})
    rewritten = result.content.strip()
    return rewritten if rewritten else question
