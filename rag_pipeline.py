"""
法律RAG 核心流程：
1. 加载文档（PDF/网页/CSV → 文本块）
2. 分块 + 向量化 → 存入 ChromaDB
3. 检索 + 生成回答
4. 评估回答质量（RAGAS 指标）
"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import re
import pandas as pd
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    DASHSCOPE_API_KEY, EMBEDDING_MODEL,
    CHROMA_DB_PATH, DOCS_DIR,
)


# ============================================================
# 1. 大模型初始化
# ============================================================

def get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.1,
    )


def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="shibing624/text2vec-base-chinese",
    )


# ============================================================
# 2. 文档加载（PDF/网页/Word/CSV → Document）
# ============================================================

def load_documents(docs_dir: str = DOCS_DIR) -> list[Document]:
    """
    加载多种格式文档：PDF、Word(docx)、网页URL、CSV
    """
    docs_path = Path(docs_dir)
    all_docs = []
    
    # 加载 PDF 文件
    for pdf_file in docs_path.glob("*.pdf"):
        docs = load_pdf(str(pdf_file))
        all_docs.extend(docs)
    
    # 加载 Word 文档
    for docx_file in docs_path.glob("*.docx"):
        docs = load_word(str(docx_file))
        all_docs.extend(docs)
    
    # 加载 CSV 文件
    for csv_file in docs_path.glob("*.csv"):
        docs = load_csv(str(csv_file))
        all_docs.extend(docs)
    
    # 从 urls.txt 加载网页
    urls_file = docs_path / "urls.txt"
    if urls_file.exists():
        docs = load_webpages(str(urls_file))
        all_docs.extend(docs)
    
    print(f"\n✅ 共加载 {len(all_docs)} 个文档片段")
    return all_docs


def load_pdf(file_path: str) -> list[Document]:
    """加载 PDF 文件"""
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        # 添加元数据
        for doc in docs:
            doc.metadata["type"] = "法律法规"
            doc.metadata["source"] = Path(file_path).name
            # 清理文本
            doc.page_content = clean_legal_text(doc.page_content)
        print(f"📄 加载PDF: {Path(file_path).name}，共 {len(docs)} 页")
        return docs
    except Exception as e:
        print(f"⚠️ PDF加载失败 {file_path}: {e}")
        return []


def load_word(file_path: str) -> list[Document]:
    """加载 Word 文档"""
    try:
        loader = UnstructuredWordDocumentLoader(file_path)
        docs = loader.load()
        # 添加元数据
        for doc in docs:
            doc.metadata["type"] = "法律法规"
            doc.metadata["source"] = Path(file_path).name
            # 清理文本
            doc.page_content = clean_legal_text(doc.page_content)
        print(f"📄 加载Word: {Path(file_path).name}")
        return docs
    except Exception as e:
        print(f"⚠️ Word加载失败 {file_path}: {e}")
        return []


def load_csv(file_path: str) -> list[Document]:
    """加载 CSV 文件（保留原逻辑）"""
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig", on_bad_lines='skip')
        print(f"\n📄 加载CSV: {Path(file_path).name}，共 {len(df)} 条记录")
        
        docs = []
        for idx, row in df.iterrows():
            text_parts = []
            for col, val in row.items():
                if pd.notna(val) and str(val).strip():
                    text_parts.append(f"{col}: {val}")
            
            full_text = "\n".join(text_parts)
            if not full_text.strip():
                continue
            
            doc = Document(
                page_content=full_text,
                metadata={
                    "source": Path(file_path).name,
                    "row_id": idx,
                    "type": "法律数据",
                }
            )
            docs.append(doc)
        return docs
    except Exception as e:
        print(f"⚠️ CSV加载失败 {file_path}: {e}")
        return []


def load_webpages(urls_file: str) -> list[Document]:
    """从 urls.txt 加载网页内容"""
    docs = []
    urls_path = Path(urls_file)
    
    if not urls_path.exists():
        return docs
    
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    for url in urls:
        try:
            loader = WebBaseLoader(url)
            web_docs = loader.load()
            for doc in web_docs:
                doc.metadata["type"] = "法律网页"
                doc.metadata["source"] = url
                doc.page_content = clean_legal_text(doc.page_content)
            docs.extend(web_docs)
            print(f"🌐 加载网页: {url}")
        except Exception as e:
            print(f"⚠️ 网页加载失败 {url}: {e}")
    
    return docs


def clean_legal_text(text: str) -> str:
    """
    清理法律文本，去除多余空白和特殊字符
    保留中文法律条文的格式
    """
    if not text:
        return ""
    
    # 去除多余空白行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除行首行尾空格
    text = '\n'.join(line.strip() for line in text.split('\n'))
    # 去除不可见字符但保留换行
    text = re.sub(r'[^\S\n]+', ' ', text)
    return text.strip()


def _infer_type(filename: str) -> str:
    """根据文件名推断文档类型"""
    name_lower = filename.lower()
    if "刑法" in name_lower:
        return "刑法"
    elif "民法" in name_lower:
        return "民法"
    elif "劳动法" in name_lower or "劳动合同" in name_lower:
        return "劳动法"
    elif "公司法" in name_lower:
        return "公司法"
    elif "合同法" in name_lower:
        return "合同法"
    elif "宪法" in name_lower:
        return "宪法"
    elif "诉讼法" in name_lower:
        return "诉讼法"
    elif "行政" in name_lower:
        return "行政法规"
    return "法律法规"


# ============================================================
# 3. 分块（适配中文法律文档）
# ============================================================

def split_documents(documents: list[Document]) -> list[Document]:
    """
    将文档分块，针对中文法律文档优化：
    - 优先按"条"、"章"、"节"分隔
    - 保持法律条文的完整性
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=[
            "\n\n\n",      # 大段落分隔
            "第[一二三四五六七八九十百千零]+[章节]",  # 章节标题
            "第[一二三四五六七八九十百千零0-9]+条",    # 条文
            "\n\n",        # 段落
            "\n",          # 换行
            "。",          # 句号
            "；",          # 分号
            " ",           # 空格
            "",            # 字符
        ],
        is_separator_regex=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"🔪 分块完成，共 {len(chunks)} 个文本块")
    return chunks


# ============================================================
# 4. 向量存储
# ============================================================

def build_vector_store(chunks: list[Document], persist_dir: str = CHROMA_DB_PATH):
    """构建向量数据库"""
    embeddings = get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
    )
    print(f"✅ 向量库已保存到: {persist_dir}")
    return vectorstore


def load_vector_store(persist_dir: str = CHROMA_DB_PATH) -> Chroma:
    """加载已有向量数据库"""
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
    )


# ============================================================
# 5. RAG 问答链
# ============================================================

def create_qa_chain(vectorstore: Chroma, k: int = 3):
    """
    创建检索+生成问答链
    """
    from langchain_openai import ChatOpenAI

    llm = get_llm()

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )

    system_prompt = """你是一个专业的中国法律顾问，基于以下检索到的法律法规文档回答用户问题。

回答要求：
1. 回答必须严格基于检索到的法律法规条文，不得编造
2. 引用法律条文时请明确标注出处（如：《刑法》第XX条）
3. 如果上下文中没有相关法律内容，请明确说明"根据现有资料无法确定"
4. 对于法律问题，建议用户必要时咨询专业律师
5. 回答应当专业、准确、通俗易懂

检索到的法律法规上下文：
{context}

用户问题：{question}

请根据上述法律法规条文，给出专业的法律解答："""

    prompt = PromptTemplate.from_template(system_prompt)

    # 使用 LCEL 组合链
    chain = (
        {"context": retriever, "question": lambda x: x}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever

# ============================================================
# 7. 检索演示（不用LLM，直接看检索到啥）
# ============================================================

def retrieve_demo(question: str, vectorstore: Chroma, k: int = 3):
    """只检索，不生成——用来调试检索质量"""
    results = vectorstore.similarity_search_with_score(question, k=k)

    print(f"\n🔍 检索到 {len(results)} 条相关内容：\n")
    for i, (doc, score) in enumerate(results, 1):
        print(f"--- 结果 {i} (相似度分数: {score:.4f}) ---")
        print(f"来源: {doc.metadata['source']} | 类型: {doc.metadata.get('type', '未知')}")
        print(f"内容: {doc.page_content[:300]}")
        print()


# ============================================================
# 8. 完整问答流程
# ============================================================

def ask(question: str, vectorstore: Optional[Chroma] = None, verbose: bool = True):
    """
    完整问答：检索 → 生成
    """
    if vectorstore is None:
        vectorstore = load_vector_store()

    qa_chain, retriever = create_qa_chain(vectorstore)

    # 检索阶段
    retrieved_docs = retriever.invoke(question)
    context_text = "\n\n".join([doc.page_content for doc in retrieved_docs])

    if verbose:
        print(f"\n🔍 检索到 {len(retrieved_docs)} 条相关内容")
        for i, doc in enumerate(retrieved_docs, 1):
            print(f"  [{i}] {doc.metadata['source']}: {doc.page_content[:100]}...")

    # 生成阶段
    answer = qa_chain.invoke(question)

    if verbose:
        print(f"\n📝 回答:\n{answer}")

    return {
        "question": question,
        "answer": answer,
        "retrieved_docs": retrieved_docs,
    }


# ============================================================
# 主程序：初始化向量库 + 进入问答循环
# ============================================================

def main():
    print("=" * 60)
    print(" ⚖️ 中国法律法规智能问答系统")
    print("=" * 60)
    print("\n支持文档格式：PDF | Word(.docx) | CSV | 网页(urls.txt)")
    print("支持的法律法规：刑法、民法、劳动法、公司法等")

    # 1. 加载或重建向量库
    if Path(CHROMA_DB_PATH).exists():
        print("\n📦 发现已有向量库，直接加载...")
        vectorstore = load_vector_store()
    else:
        print("\n📥 构建向量库...")
        raw_docs = load_documents(DOCS_DIR)
        if not raw_docs:
            print("⚠️ 目录下没有文档，请先放入法律文档")
            print("\n提示：")
            print("  1. 将 PDF/Word 法律文件放入 ./document/ 目录")
            print("  2. 或将网页 URL 写入 ./document/urls.txt（每行一个）")
            return
        chunks = split_documents(raw_docs)
        vectorstore = build_vector_store(chunks)

    # 2. 进入问答循环
    print("\n✅ 系统就绪！开始法律问答（输入 quit 退出）\n")
    print("-" * 60)

    while True:
        question = input("❓ 请输入法律问题: ").strip()
        if question.lower() == "quit":
            break
        if not question:
            continue

        print()
        ask(question, vectorstore)

if __name__ == "__main__":
    main()
