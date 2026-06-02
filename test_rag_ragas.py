"""
RAGAS 批量评测入口
跟 test_rag_batch.py（DeepEval）并列存在 —— 两个框架独立跑、独立报告
"""
import os
import yaml
import pytest

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
from rag_pipeline import ask, load_vector_store
from ragas_eval import run_ragas_evaluation


# DeepEval 也是靠这套 env var，跟 RAGAS 共享一份
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_MODEL_NAME"] = OPENAI_MODEL
os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL


def _load_dataset(path="eval_dataset.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---- 模块加载时执行：建向量库 → 跑 RAG → 跑 RAGAS（只跑一次）----
_vectorstore = load_vector_store()
_dataset = _load_dataset()


def _build_test_cases():
    cases = []
    for item in _dataset:
        result = ask(item["question"], _vectorstore, verbose=False)
        cases.append({
            "question":     item["question"],
            "answer":       result["answer"],
            "contexts":     [doc.page_content for doc in result["retrieved_docs"]],
            "ground_truth": item["reference_answer"],
        })
        print(f"  [RAG]  {item['question'][:30]}...")
    return cases


_test_cases = _build_test_cases()
print(f"\n[RAGAS] 评测 {len(_test_cases)} 条题...")
_ragas_result = run_ragas_evaluation(_test_cases)
print(f"[RAGAS] Overall: {_ragas_result['overall']}")


# ---- pytest 参数化：每条题一个用例，只校验分数存在 ----
@pytest.mark.parametrize(
    "idx",
    range(len(_dataset)),
    ids=[d["question"][:20] for d in _dataset],
)
def test_ragas_per_question(idx):
    """每条题至少能拿到 4 个指标的分数（不全为 None）"""
    row = _ragas_result["per_question"][idx]
    for metric in ("faithfulness", "context_precision", "context_recall", "answer_relevancy"):
        assert row[metric] is not None, f"#{idx} {metric} is None"


def test_ragas_overall_quality():
    """整体均分：4 指标都不应低于 0.5（最低质量门）"""
    overall = _ragas_result["overall"]
    print(f"\n[RAGAS Overall] {overall}")
    for metric, score in overall.items():
        assert score >= 0.5, f"{metric} = {score} < 0.5"