"""
批量评测 —— 读取 eval_dataset.yaml，对每条数据跑评测
这是你项目的核心脚本
"""

import os

# 从 config.py 读取配置，避免硬编码
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL

# 设置 DeepEval 需要的环境变量
os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY
os.environ["OPENAI_MODEL_NAME"] = DEEPSEEK_MODEL
os.environ["OPENAI_BASE_URL"] = DEEPSEEK_BASE_URL

import yaml
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualPrecisionMetric

from rag_pipeline import ask, load_vector_store


# ============ 加载数据集 ============
def load_eval_dataset(path="eval_dataset.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============ 初始化向量库 ============
_vectorstore = load_vector_store()
_dataset = load_eval_dataset()


# ============ 参数化测试：每条数据生成一个测试用例 ============
# pytest 的参数化机制：自动为每条数据生成独立的测试函数
@pytest.mark.parametrize(
    "item",  # 参数名
    _dataset,  # 数据源（列表，每个元素是一条测试数据）
    ids=[f"{d['category']}_{''.join(d['question'][:15])}" for d in _dataset]  # 测试用例ID
)
def test_rag_eval(item):
    """对每条法律咨询问答进行评测"""

    # 1. 调用RAG应用
    result = ask(item["question"], _vectorstore, verbose=False)

    # 2. 提取检索上下文
    retrieval_context = [doc.page_content for doc in result["retrieved_docs"]]

    # 3. 构建测试用例
    test_case = LLMTestCase(
        input=item["question"],
        actual_output=result["answer"],
        expected_output=item["reference_answer"],
        retrieval_context=retrieval_context,
    )

    # 4. 定义评测指标
    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
        ContextualPrecisionMetric(threshold=0.7),
    ]

    # 5. 执行评测
    assert_test(test_case, metrics)
