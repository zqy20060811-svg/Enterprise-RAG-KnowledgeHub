# check_db.py 独立查看向量库内容
import config_data as config
from langchain_chroma import Chroma

# 直接读取你的chroma数据库，不需要任何embedding
db = Chroma(
    collection_name=config.collection_name,
    persist_directory=config.persist_directory,
    embedding_function=None  # 关键：纯读取，不依赖模型
)

# 获取所有数据
data = db.get()

# 打印结果
print("=" * 50)
print("【向量库中存储的真实文本】")
print("=" * 50)

if not data["documents"]:
    print("\n库是空的！")
else:
    for i, (content, meta) in enumerate(zip(data["documents"], data["metadatas"])):
        print(f"\n【第 {i+1} 条】")
        print(f"文件：{meta.get('source', '未知')}")
        print(f"时间：{meta.get('create_time', '未知')}")
        print(f"内容：{repr(content)}")  # repr 会把空格、\n、隐藏字符全部显示出来！