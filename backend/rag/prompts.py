"""
提示词模板集中管理
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# 问答提示词：要求基于参考资料回答，附带来源
QA_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "你是企业知识库智能问答助手。请严格基于以下参考资料回答用户问题，"
        "回答要简洁专业。如果参考资料不足以回答，请直接说明「未找到相关资料」，"
        "不要编造内容。\n\n参考资料：\n{context}",
    ),
    MessagesPlaceholder("history"),
    ("user", "{input}"),
])
