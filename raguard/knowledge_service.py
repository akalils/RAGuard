from functools import lru_cache
import logging
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


logger = logging.getLogger(__name__)
QueryText = Annotated[
    str,
    StringConstraints(
        strict=True, strip_whitespace=True, min_length=1, max_length=1000
    ),
]
ResultLimit = Annotated[int, Field(strict=True, ge=1, le=5)]

class SearchInput(BaseModel):
    query: QueryText
    top_k: ResultLimit = 3

@lru_cache(maxsize=1)
def get_vectorstore():
    from raguard.config import CHROMA_DB_PATH, PROJECT_ROOT
    db_path = Path(CHROMA_DB_PATH).expanduser()
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    if not (db_path / "chroma.sqlite3").is_file():
        raise FileNotFoundError("尚未准备 Chroma 向量库")
    
    from raguard.rag_pipeline import load_vector_store

    return load_vector_store(persist_dir=str(db_path))

def search(query: str, top_k: int = 3) -> dict:
    params = SearchInput(query=query, top_k=top_k)
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(params.query, k=params.top_k)
        results = []
        for doc in docs:
            source = str(doc.metadata.get("source", "未知来源"))
            if "://" not in source:
                source = Path(source).name
            results.append({"content": doc.page_content, "source": source})
    except FileNotFoundError:
        raise RuntimeError(
            "KNOWLEDGE_BASE_NOT_READY：请先准备已有向量库和本地模型文件"
        ) from None
    except Exception as exc:
        logger.error("检索失败，异常类型：%s", type(exc).__name__)
        raise RuntimeError(
            "SEARCH_FAILED：请检查检索依赖、模型和向量库配置。"
        ) from None
    
    return {"query": params.query, "results": results}