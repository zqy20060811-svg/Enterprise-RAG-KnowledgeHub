# 这个文件是整个项目的【核心大脑】
# 作用：把 知识库 + 大模型 + 聊天记忆 组装到一起，实现带记忆的 RAG 智能问答

# 导入需要的工具包
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from knowledge_base import get_history  # 导入聊天历史管理工具
from vector_stores import VectorStoreService  # 导入向量库服务
from langchain_community.embeddings import DashScopeEmbeddings  # 阿里向量模型
import config_data as config  # 配置文件
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # 提示词模板
from langchain_community.chat_models.tongyi import ChatTongyi  # 阿里通义大模型
import os
from dotenv import load_dotenv
# 设置阿里大模型的API密钥（必须要有，不然调用不了AI）
#os.environ["DASHSCOPE_API_KEY"] = "key"
load_dotenv()  # 读取 .env 文件
api_key = os.getenv("DASHSCOPE_API_KEY")
# 调试工具：打印最终发送给AI的完整提示词
# 作用：方便我们看AI到底收到了什么内容
def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())  # 打印完整提示词
    print("=" * 20)
    return prompt

# RAG 核心服务类
# 小白解释：这是整个项目最核心的类，负责所有问答逻辑
class RagService(object):
    # 初始化方法：创建对象时自动执行
    # 作用：把向量库、提示词、AI模型全部准备好
    def __init__(self):
        # 1. 创建向量库服务（用来查询知识库）
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name)
        )

        # 2. 设置提示词模板（告诉AI怎么回答）
        # 规则：只看参考资料 + 看聊天历史 + 回答用户问题
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "以我提供的已知参考资料为主，简洁专业地回答用户问题。参考资料:{context}。"),
            ("system", "并且我提供用户的对话历史记录，如下："),
            MessagesPlaceholder("history"),  # 占位符：自动填入聊天历史
            ("user", "请回答用户提问：{input}")  # 用户问题
        ])

        # 3. 创建AI大模型对象
        self.chat_model = ChatTongyi(
            model=config.chat_model_name,
            api_key=os.environ["DASHSCOPE_API_KEY"]
        )

        # 4. 组装完整的问答链（最关键！把所有零件拼起来）
        self.chain = self.__get_chain()

    # 【内部方法】组装完整的RAG问答链
    # 小白解释：把“查库+提示词+AI”拼成一条流水线
    def __get_chain(self):
        # 获取向量库的检索器（负责从知识库找答案）
        retriever = self.vector_service.get_retriever()

        # 格式化文档：把查到的知识库内容变成字符串
        def format_document(docs: list[Document]):
            if not docs:
                return "无相关参考资料"
            res = ""
            for doc in docs:
                res += f"文档片段：{doc.page_content}\n元数据：{doc.metadata}\n\n"
            return res

        # 格式化：给检索器只传用户问题
        def format_for_retriever(value: dict):
            return value["input"]

        # 格式化：把数据整理成提示词需要的格式
        def format_for_prompt_template(value):
            return {
                "input": value["input"]["input"],
                "context": value["context"],
                "history": value["input"]["history"]
            }

        # ===================== 核心流水线 =====================
        # 1. 接收用户问题
        # 2. 去知识库查资料
        # 3. 组装提示词
        # 4. 发给AI
        # 5. 解析AI返回的文字
        #RunnableLambda是适配器给不是chain的函数能进chain
        chain = (
            {
                "input": RunnablePassthrough(),  # 原样传递用户输入
                "context": RunnableLambda(format_for_retriever) | retriever | format_document  # 查询知识库
            }
            | RunnableLambda(format_for_prompt_template)  # 整理数据格式
            | self.prompt_template  # 填入提示词模板
            | print_prompt  # 打印调试
            | self.chat_model  # 调用AI
            | StrOutputParser()  # 把结果转成普通字符串
        )

        # 给流水线加上【记忆功能】
        return RunnableWithMessageHistory(
            chain,
            get_history,  # 读取聊天历史
            input_messages_key="input",
            history_messages_key="history"
        )
    # ===================== 文件上传处理 =====================
    # 作用：接收二进制文件，提取文字，存入向量库
    # 输入：文件bytes + 文件名
    # 输出：上传结果
    def upload_file_process(self, file_bytes: bytes, filename: str):
        try:
            import os
            # 获取后缀
            ext = os.path.splitext(filename)[-1].lower()
            content = ""

            # TXT 解析
            if ext == ".txt":
                content = file_bytes.decode("utf-8", errors="ignore")

            # PDF 解析
            elif ext == ".pdf":
                from pypdf import PdfReader
                from io import BytesIO
                reader = PdfReader(BytesIO(file_bytes))
                content = "\n".join(page.extract_text() or "" for page in reader.pages)

            # DOCX 解析
            elif ext in [".docx", ".doc"]:
                from docx import Document
                from io import BytesIO
                doc = Document(BytesIO(file_bytes))
                content = "\n".join(para.text for para in doc.paragraphs)

            # 去掉后缀，得到干净文件名（你要的效果）
            clean_filename = os.path.splitext(filename)[0]

            # 存库
            return self.vector_service.upload_document(content, clean_filename)

        except Exception as e:
            return f"上传失败：{str(e)}"

    # 流式问答接口（打字机效果）
    # 作用：接收用户问题，返回一个迭代器，一点点吐出文字
    def ask_question_stream(self, prompt: str, session_id: str):
        # 动态传入 session_id
        config = {"configurable": {"session_id": session_id}}
        return self.chain.stream(
            {"input": prompt},
            config=config
        )


# 创建一个全局唯一的RAG服务实例
# 作用：让 main.py 直接调用，不用反复初始化
rag_service = RagService()