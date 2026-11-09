"""
配置区 — 从 .env 文件读取 API Key
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 所有项目路径均以仓库根目录为基准，与启动目录无关。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
EVAL_DATASET_PATH = str(DATA_DIR / "datasets" / "eval_dataset.yaml")
EVAL_REPORT_PATH = str(REPORTS_DIR / "eval_report.md")
EVAL_HISTORY_PATH = str(REPORTS_DIR / "eval_history.db")
load_dotenv(PROJECT_ROOT / ".env")

# DeepSeek / DashScope 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")

# Embedding 配置（用 DashScope，免费的）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-v3"

# 向量数据库路径
CHROMA_DB_PATH = str(DATA_DIR / "chroma_db")

# 文档路径
DOCS_DIR = str(DATA_DIR / "documents")


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
