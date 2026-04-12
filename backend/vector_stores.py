# 这个文件的作用：
# 管理【向量库】，负责：存文件、查文件、去重、删除、清空
# 相当于项目的【知识库硬盘】

import os
import re
import hashlib  # 用来生成MD5，实现文件去重
from datetime import datetime  # 获取当前时间
from langchain_chroma import Chroma  # 本地轻量向量库
from langchain_community.vectorstores import PGVector  # 数据库版向量库
from langchain_community.embeddings import DashScopeEmbeddings  # 阿里向量模型
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 文本切割工具
import config_data as config  # 配置文件


# ===================== 【新增】文本清洗工具函数（无任何打印，纯干净字符串） =====================
def clean_text(text):
    """
    文本清洗功能：
    1. 清除所有空格、换行、制表符
    2. 清除PDF/DOCX解析产生的隐藏垃圾字符（\xa0 \u200b \ufeff）
    3. 删除所有中间空格 + 首尾空格
    最终输出：无任何空白符号的纯文本字符串
    """
    # 统一处理所有空白字符、隐藏字符
    text = re.sub(r'[\s\xa0\u200b\ufeff]+', ' ', text)
    # 去除首尾空格
    text = text.strip()
    # 删除所有空格（前后+中间全部删除）
    text = text.replace(' ', '')
    return text


# ===================== MD5 去重工具 =====================
# 作用：防止同样的内容重复上传，浪费空间
# 原理：同样的文字 → 生成同样的MD5值 → 发现重复就跳过

# 检查这个MD5是否已经存在（是否传过相同内容）
def check_md5(md5_str: str):
    # 如果记录文件不存在，先创建一个空文件
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False  # 不存在，返回False

    # 逐行读文件，看看有没有重复的MD5
    with open(config.md5_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip() == md5_str:
                return True  # 找到了，重复了
    return False  # 没重复

# 把新的MD5保存到文件里，记录“这个内容已经传过了”
def save_md5(md5_str: str):
    with open(config.md5_path, 'a', encoding="utf-8") as f:
        f.write(md5_str + '\n')

# 输入一段文字，输出它的MD5值（唯一标识）
def get_string_md5(input_str: str, encoding='utf-8'):
    return hashlib.md5(input_str.encode(encoding)).hexdigest()


# ===================== 向量库核心服务 =====================
# 小白解释：
# 这是管理知识库的核心类，负责：
# 存文本、查文本、切文本、删文件、清空库
class VectorStoreService(object):

    # 初始化：创建向量库 + 文本切割器
    def __init__(self, embedding):
        self.embedding = embedding  # 保存向量模型

        # 根据配置选择用哪种向量库
        if config.vector_type == "chroma":
            # 本地文件版向量库（简单、不用装数据库）
            self.vector_store = Chroma(
                collection_name=config.collection_name,
                embedding_function=self.embedding,
                persist_directory=config.persist_directory,
            )
        elif config.vector_type == "pgvector":
            # 专业数据库版（适合正式项目）
            self.vector_store = PGVector(
                collection_name=config.pg_collection_name,
                embedding_function=self.embedding,
                connection_string=config.pg_connection_string,
            )

        # 初始化文本切割器
        # 作用：把长文章切成一小段一小段，方便AI查询
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=len,
        )

    # 获取检索器
    # 小白解释：生成一个“查找工具”，用来从库里找最相关的内容
    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": config.similarity_threshold})

    # 插入文本到向量库（底层方法）
    # texts：文字列表
    # metadatas：附加信息（文件名、时间等）
    def add_texts(self, texts, metadatas=None):
        self.vector_store.add_texts(texts=texts, metadatas=metadatas)

    # 完整上传流程：去重 + 切割 + 存入向量库
    # 小白解释：上传文件的完整逻辑，对外提供的主要方法
    def upload_document(self, data: str, filename):
        # ===================== 【唯一修改处】文本清洗：解析后立即清洗，去除所有空白符号 =====================
        cleaned_data = clean_text(data)

        # 第一步：MD5去重，重复内容直接跳过（使用清洗后的数据）
        md5_hex = get_string_md5(cleaned_data)
        if check_md5(md5_hex):
            return "[跳过]内容已存在"

        # 第二步：文本太长就切割，短就直接存
        if len(cleaned_data) > config.max_split_char_number:
            chunks = self.spliter.split_text(cleaned_data)
        else:
            chunks = [cleaned_data]

        # 第三步：给每段文字附加信息（文件名、上传时间、上传人）
        metadata = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "小曹",
        }
        metadatas = [metadata for _ in chunks]

        # 第四步：把切割好的文字存入向量库
        self.add_texts(chunks, metadatas)

        # 第五步：记录MD5，防止重复上传
        save_md5(md5_hex)

        return "[成功]已存入向量库"

    # 按文件名删除（最终版：文件名 → 取文本 → 用现成函数算MD5 → 删除MD5）
    def delete_by_filename(self, filename):
        try:
            # 1. 查询该文件的所有文档
            data = self.vector_store.get(where={"source": filename})
            if not data["documents"]:
                return f"[删除] 文件：{filename} 不存在"

            # 2. 核心修复：取第一段文本（完整文件内容），和上传时一样清洗+算MD5
            if data["documents"]:
                # 用原始内容计算MD5（和upload_document逻辑完全一致）
                original_content = data["documents"][0]
                cleaned_data = clean_text(original_content)
                target_md5 = get_string_md5(cleaned_data)

            # 3. 删除MD5记录
            if os.path.exists(config.md5_path):
                with open(config.md5_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                # 过滤掉要删除的MD5
                new_lines = [line for line in lines if line.strip() != target_md5]
                with open(config.md5_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)

            # 4. 删除向量库数据
            self.vector_store.delete(where={"source": filename})

            return f"[删除成功] 文件：{filename}（MD5已同步清理）"
        except Exception as e:
            return f"[删除失败] {str(e)}"
    # 一键清空整个向量库
    # 作用：把知识库全部清空，从头开始
    def clear_all(self):
        try:
            self.vector_store.delete_collection()  # 删除整个集合
            # 删完重新初始化一遍，保证还能继续用
            self.__init__(self.embedding)

            # =====================
            # 我只在这里加了 3 行：清空 MD5 记录文件
            # =====================
            with open(config.md5_path, 'w', encoding='utf-8') as f:
                f.write('')

            return "[清空成功] 整个向量库已清空"
        except Exception as e:
            return f"[清空失败] {str(e)}"