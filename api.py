"""
法律RAG API服务 - FastAPI
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from rag_pipeline import ask, load_vector_store, build_vector_store, load_documents, split_documents
from config import CHROMA_DB_PATH
from pathlib import Path

app = FastAPI(title="法律法规智能问答API", version="1.0")

# 全局向量库（启动时加载）
vectorstore = None


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[dict]


@app.on_event("startup")
def startup_event():
    """启动时初始化向量库"""
    global vectorstore
    
    if Path(CHROMA_DB_PATH).exists():
        print("📦 加载已有向量库...")
        vectorstore = load_vector_store()
    else:
        print("📥 构建向量库...")
        raw_docs = load_documents()
        if raw_docs:
            chunks = split_documents(raw_docs)
            vectorstore = build_vector_store(chunks)
        else:
            print("⚠️ 未找到文档，请先放入法律文件")
    
    print("✅ API服务已启动")


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest):
    """
    法律咨询接口
    
    示例请求:
    {
        "question": "盗窃罪的量刑标准是什么？"
    }
    """
    global vectorstore
    
    if vectorstore is None:
        return AskResponse(
            question=req.question,
            answer="向量库未初始化，请先上传法律文档",
            sources=[]
        )
    
    result = ask(req.question, vectorstore, verbose=False)
    
    # 格式化来源
    sources = [
        {
            "source": doc.metadata.get("source", "未知"),
            "type": doc.metadata.get("type", "未知"),
            "content": doc.page_content[:200] + "..."
        }
        for doc in result["retrieved_docs"]
    ]
    
    return AskResponse(
        question=result["question"],
        answer=result["answer"],
        sources=sources
    )


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok", "vectorstore_ready": vectorstore is not None}


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "法律法规智能问答API",
        "docs": "/docs",
        "endpoints": {
            "POST /ask": "提交法律问题",
            "GET /health": "健康检查"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
