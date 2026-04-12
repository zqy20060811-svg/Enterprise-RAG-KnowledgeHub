# 知识科普：这个文件的作用
# 专门负责【保存聊天记录】和【读取聊天记录】
# 让AI能记住你之前说过什么

import json
import os
from typing import Sequence

# 导入LangChain专门用来管理聊天历史的工具
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict


# 根据会话id获取聊天历史
# 小白解释：给一个对话ID，返回这个对话的所有历史记录
def get_history(session_id):
    # 创建一个文件聊天记录管理器，存在 ./chat_history 文件夹里
    return FileChatMessageHistory(session_id, "./chat_history")


# 文件版聊天历史管理
# 小白解释：这是一个工具类，专门把聊天记录存到本地文件里
class FileChatMessageHistory(BaseChatMessageHistory):

    # 初始化方法：创建对象时自动执行
    # session_id：对话的唯一编号（区分不同用户/不同对话）
    # storage_path：聊天记录存在哪个文件夹
    def __init__(self, session_id, storage_path):
        self.session_id = session_id  # 保存对话ID
        self.storage_path = storage_path  # 保存文件夹路径
        # 拼接出完整文件路径：文件夹/对话ID
        self.file_path = os.path.join(storage_path, session_id)
        # 创建存储文件夹，如果已经存在就不创建（防止报错）
        os.makedirs(storage_path, exist_ok=True)

    # 添加消息到聊天历史
    # 小白解释：把新的对话内容保存到文件里
    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        # 先把已经存在的历史消息取出来，转成列表
        all_messages = list(self.messages)
        # 把新消息追加到列表后面
        all_messages.extend(messages)
        # 把消息对象转成JSON格式（方便存文件）
        saved = [message_to_dict(m) for m in all_messages]

        # 打开文件，把所有聊天记录写进去（覆盖原来的内容）
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(saved, f, ensure_ascii=False)

    # 获取所有聊天历史（只读属性）
    # 小白解释：从文件里把聊天记录读出来
    @property
    def messages(self) -> list[BaseMessage]:
        try:
            # 打开文件读取内容
            with open(self.file_path, "r", encoding="utf-8") as f:
                # 把JSON格式转回LangChain能识别的消息对象
                return messages_from_dict(json.load(f))
        except FileNotFoundError:
            # 如果文件不存在，说明还没有聊天记录，返回空列表
            return []

    # 清空当前对话的所有聊天记录
    # 小白解释：把文件内容清空，变成空列表
    def clear(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)