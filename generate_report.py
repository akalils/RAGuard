"""
评测报告生成器
读取批量评测结果，生成 Markdown 格式的评测报告
"""

import os
# 从 config.py 读取配置，避免硬编码
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL

# 设置 DeepEval 需要的环境变量
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_MODEL_NAME"] = OPENAI_MODEL
os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL

from ragas_eval import run_ragas_evaluation
import yaml
import json
from datetime import datetime
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualPrecisionMetric

from rag_pipeline import ask, load_vector_store


def load_eval_dataset(path="eval_dataset.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_full_evaluation():
    """执行完整评测并返回结果"""
    vectorstore = load_vector_store()
    dataset = load_eval_dataset()

    test_cases = []
    meta_info = []  # 保存类别和难度信息，用于报告分组

    for item in dataset:
        print(f"评测中: {item['question'][:30]}...")

        result = ask(item["question"], vectorstore, verbose=False)
        retrieval_context = [doc.page_content for doc in result["retrieved_docs"]]

        test_case = LLMTestCase(
            input=item["question"],
            actual_output=result["answer"],
            expected_output=item["reference_answer"],
            retrieval_context=retrieval_context,
        )
        test_cases.append(test_case)
        meta_info.append({
            "category": item["category"],
            "difficulty": item["difficulty"],
            "question": item["question"],
        })

    metrics = [
        AnswerRelevancyMetric(threshold=0.7),
        FaithfulnessMetric(threshold=0.7),
        ContextualPrecisionMetric(threshold=0.7),
    ]

    results = evaluate(test_cases=test_cases, metrics=metrics)
    return results, meta_info

def run_ragas_batch():
    """跑 RAGAS 评测，返回 (per_question 列表, overall 字典)"""
    vectorstore = load_vector_store()
    dataset = load_eval_dataset()

    cases = []
    meta = []
    for item in dataset:
        print(f"[RAGAS] {item['question'][:30]}...")
        result = ask(item["question"], vectorstore, verbose=False)
        cases.append({
            "question":     item["question"],
            "answer":       result["answer"],
            "contexts":     [doc.page_content for doc in result["retrieved_docs"]],
            "ground_truth": item["reference_answer"],
        })
        meta.append({
            "category":   item["category"],
            "difficulty": item["difficulty"],
            "question":   item["question"],
        })

    ragas_result = run_ragas_evaluation(cases)
    return ragas_result, meta

def generate_report(
    deepeval_results, deepeval_meta,
    ragas_result, ragas_meta,
    output_path="eval_report.md",
):
    """合并 DeepEval + RAGAS 两套分数，生成一份 Markdown 报告"""
    lines = []
    lines.append("# RAGuard 评测报告")
    lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"评测数据集：{len(deepeval_meta)} 条法律咨询问答")
    lines.append(f"评测框架：DeepEval (3 指标) + RAGAS (4 指标)")
    lines.append(f"通过阈值：0.7\n")
    lines.append("---\n")

    # ============ 1. DeepEval 总体 ============
    lines.append("## 总体得分\n")
    lines.append("### DeepEval\n")
    de_score = []
    for tr in deepeval_results.test_results:
        row = {}
        for md in tr.metrics_data:
            name = getattr(md, "name", None) or getattr(md, "metric_name", "Unknown")
            row[name] = round(md.score, 3)
            row[f"{name}_passed"] = md.success
        de_score.append(row)

    for metric in ["Answer Relevancy", "Faithfulness", "Contextual Precision"]:
        vals = [r.get(metric, 0) for r in de_score if metric in r]
        if vals:
            lines.append(f"- **{metric} 均分**: {sum(vals)/len(vals):.3f}")

    # ============ 2. RAGAS 总体 ============
    lines.append("\n### RAGAS\n")
    overall = ragas_result["overall"]
    metric_cn = {
        "faithfulness":      "Faithfulness（忠实度）",
        "context_precision": "Context Precision（检索精度）",
        "context_recall":    "Context Recall（检索召回）",
        "answer_relevancy":  "Answer Relevancy（回答相关性）",
    }
    for k, v in overall.items():
        cn = metric_cn.get(k, k)
        lines.append(f"- **{cn}**: {v:.3f}")

    # ============ 3. DeepEval 按类别分组 ============
    lines.append("\n## DeepEval · 按法律类别分组\n")
    for category in ["劳动法", "刑法"]:
        cat_data = [r for r, m in zip(de_score, deepeval_meta) if m["category"] == category]
        if not cat_data:
            continue
        lines.append(f"### {category}\n")
        for metric in ["Answer Relevancy", "Faithfulness", "Contextual Precision"]:
            vals = [r.get(metric, 0) for r in cat_data if metric in r]
            if vals:
                lines.append(f"- {metric}: {sum(vals)/len(vals):.3f}")
        lines.append("")

    # ============ 4. RAGAS 按类别分组 ============
    lines.append("\n## RAGAS · 按法律类别分组\n")
    for category in ["劳动法", "刑法"]:
        rows = [r for r, m in zip(ragas_result["per_question"], ragas_meta) if m["category"] == category]
        if not rows:
            continue
        lines.append(f"### {category}\n")
        for k in ["faithfulness", "context_precision", "context_recall", "answer_relevancy"]:
            vals = [r.get(k) for r in rows if r.get(k) is not None]
            if vals:
                lines.append(f"- {metric_cn.get(k, k)}: {sum(vals)/len(vals):.3f}")
        lines.append("")

    # ============ 5. DeepEval Bad Cases ============
    lines.append("\n## DeepEval · Bad Cases（未达标用例）\n")
    de_bad = []
    for r, m in zip(de_score, deepeval_meta):
        failed = [k.replace("_passed", "") for k, v in r.items() if k.endswith("_passed") and v is False]
        if failed:
            de_bad.append((m, failed, r))
    if de_bad:
        for m, failed, r in de_bad:
            lines.append(f"- **{m['question'][:40]}...** [{m['category']}/{m['difficulty']}]")
            lines.append(f"  未通过: {', '.join(failed)}")
    else:
        lines.append("所有用例均通过阈值！")

    # ============ 6. RAGAS Bad Cases（均分 < 0.7）============
    lines.append("\n## RAGAS · Bad Cases（任一指标 < 0.7）\n")
    ragas_bad = []
    for r, m in zip(ragas_result["per_question"], ragas_meta):
        failed = [k for k in ["faithfulness", "context_precision", "context_recall", "answer_relevancy"]
                  if r.get(k) is not None and r[k] < 0.7]
        if failed:
            ragas_bad.append((m, failed, r))
    if ragas_bad:
        for m, failed, r in ragas_bad:
            lines.append(f"- **{m['question'][:40]}...** [{m['category']}/{m['difficulty']}]")
            for f in failed:
                lines.append(f"  - {metric_cn.get(f, f)}: {r[f]:.3f}")
    else:
        lines.append("所有用例 4 项指标均 ≥ 0.7！")

    # ---- 写文件 ----
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ 评测报告已生成: {output_path}")
    return content


if __name__ == "__main__":
    # DeepEval
    deepeval_results, deepeval_meta = run_full_evaluation()
    # RAGAS
    ragas_result, ragas_meta = run_ragas_batch()

    # 合并报告
    generate_report(
        deepeval_results, deepeval_meta,
        ragas_result, ragas_meta,
    )