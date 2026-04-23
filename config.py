"""
配置区 — 填你的API Key
"""
import os
from dotenv import load_dotenv

load_dotenv()

# DEEPSEEK_API_KEY = "sk-1d6b5f973ad94eb5936262f903daddf4"
# DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
# DEEPSEEK_MODEL = os.getenv("OPENAI_MODEL_NAME", "deepseek-chat")

DEEPSEEK_API_KEY = "sk-4408eca08dd7492890a48bacebe294c8"
DEEPSEEK_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
DEEPSEEK_MODEL = os.getenv("OPENAI_MODEL_NAME", "MiniMax-M2.1")

# Embedding 配置（用 DashScope，免费的）
DASHSCOPE_API_KEY = "sk-c40afaedce9a441aa059d5348b58a3a7"
EMBEDDING_MODEL = "text-embedding-v3"

# 向量数据库路径
CHROMA_DB_PATH = "./chroma_db"

# 文档路径
DOCS_DIR = "./document"
