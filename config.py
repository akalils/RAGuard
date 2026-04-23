"""
配置区 — 从 .env 文件读取 API Key
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# DeepSeek / DashScope 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "MiniMax-M2.1")

# Embedding 配置（用 DashScope，免费的）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-v3"

# 向量数据库路径
CHROMA_DB_PATH = "./chroma_db"

# 文档路径
DOCS_DIR = "./document"


# 配置验证
def validate_config():
    """检查必要配置是否存在"""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY 未设置！请检查 .env 文件")
    if not DASHSCOPE_API_KEY:
        raise ValueError("DASHSCOPE_API_KEY 未设置！请检查 .env 文件")
    print("✅ 配置验证通过")


if __name__ == "__main__":
    validate_config()
    print(f"模型: {OPENAI_MODEL}")
    print(f"API Key: {OPENAI_API_KEY[:10]}...")
