"""
RAGAS 0.4.3 评测封装 —— 给 RAG pipeline 的输出打分
4 指标：Faithfulness / Context Precision / Context Recall / Answer Relevancy

⚠️ RAGAS 0.4.3 的坑（自己跟自己打架）：
  - collections.* 的新类不继承 Metric → evaluate() 校验失败
  - 旧路径 ragas.metrics.* 的类继承 Metric → evaluate() 通过（带 deprecation warning）
  - 唯一可行写法：用旧路径 + 在每个 metric 构造时传 llm
  - AnswerRelevancy 还要传 embeddings（line 182 evaluation.py 会注入）
"""
import warnings
from datasets import Dataset
from ragas import evaluate

# 旧路径 import（有 DeprecationWarning，但 evaluate() 内部只接受这些类）
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import (
        Faithfulness,
        ContextPrecision,
        ContextRecall,
        AnswerRelevancy,
    )

from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


def get_ragas_llm():
    """RAGAS 用的 LLM judge（LangChain 包装，temperature 锁 0）"""
    return LangchainLLMWrapper(
        ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            temperature=0,
        )
    )


def get_ragas_embeddings():
    """
    AnswerRelevancy 强依赖 embeddings（旧路径的 AnswerRelevancy 继承
    MetricWithLLM + MetricWithEmbeddings）。
    用跟 rag_pipeline.py 一致的 HF 中文模型，本地推理不调外部 API。
    """
    return LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="shibing624/text2vec-base-chinese")
    )


def run_ragas_evaluation(test_cases: list[dict]) -> dict:
    """
    批量跑 RAGAS 评测。
    test_cases: [{question, answer, contexts, ground_truth}, ...]
    返回: {overall: {指标: 均分}, per_question: [{每条题的所有指标}, ...]}
    """
    # ---- 1. 构造 RAGAS 期望的 Dataset ----
    data = {
        "question":     [tc["question"]     for tc in test_cases],
        "answer":       [tc["answer"]       for tc in test_cases],
        "contexts":     [tc["contexts"]     for tc in test_cases],
        "ground_truth": [tc["ground_truth"] for tc in test_cases],
    }
    dataset = Dataset.from_dict(data)

    # ---- 2. 共享 LLM + embeddings ----
    llm = get_ragas_llm()
    embeddings = get_ragas_embeddings()

    # ---- 3. 构造 4 个 metric（每个都要传 llm，AnswerRelevancy 还要 embeddings）----
    metrics = [
        Faithfulness(llm=llm),
        ContextPrecision(llm=llm),
        ContextRecall(llm=llm),
        AnswerRelevancy(llm=llm, embeddings=embeddings),
    ]

    # ---- 4. 跑评测 ----
    # 不再传 llm/embeddings 给 evaluate()，因为 metric 构造时已传；
    # 旧路径 evaluate 不会再覆盖（line 174-194 只在 metric.llm is None 时才注入）
    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        raise_exceptions=False,
    )

    # ---- 5. 拆出 per-question + overall ----
    df = result.to_pandas()
    per_question = df.to_dict("records")

    overall = {}
    for col in df.columns:
        if col in ("question", "answer", "contexts", "ground_truth"):
            continue
        if df[col].dtype in ("float64", "float32"):
            overall[col] = round(float(df[col].mean()), 4)

    return {"overall": overall, "per_question": per_question}
