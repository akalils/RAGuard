"""
RAGAS 评测封装 —— 给 RAG pipeline 的输出打分
4 个核心指标：Faithfulness / Context Precision / Context Recall / Answer Relevance
"""
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    Faithfulness,
    ContextPrecision,
    ContextRecall,
    AnswerRelevancy,
)
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


def get_ragas_llm():
    """RAGAS 用的 LLM（必须 LangChain 包装，temperature 锁 0）"""
    return LangchainLLMWrapper(
        ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            temperature=0,
        )
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

    # ---- 2. 配置 4 个指标 ----
    metrics = [
        Faithfulness(),
        ContextPrecision(),
        ContextRecall(),
        AnswerRelevancy(),
    ]

    # ---- 3. 注入 LLM（让所有指标共享同一个 judge）----
    evaluator_llm = get_ragas_llm()

    # ---- 4. 跑评测 ----
    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
        raise_exceptions=False,   # 单条失败不中断整批
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