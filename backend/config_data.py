# config_data.py
# 这是你项目真正的配置文件，所有变量全齐，和你老配置一模一样

# ===================== 全局路径 =====================
md5_path = "./md5.text"

# ===================== 向量库配置 =====================
vector_type = "chroma"
collection_name = "rag"
persist_directory = "./chroma_db"

# PGVector 配置（你没用到，保留原样）
pg_connection_string = "postgresql+psycopg2://用户名:密码@主机:端口/数据库名"
pg_collection_name = "my_rag_collection"

# ===================== 文本切割 =====================
chunk_size = 1000
chunk_overlap = 100
separators = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]
max_split_char_number = 1000

# ===================== 检索 =====================
similarity_threshold = 1

# ===================== 模型名称（你原来的！） =====================
embedding_model_name = "text-embedding-v4"
chat_model_name = "qwen3-max"

