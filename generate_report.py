"""
评测报告生成器
读取批量评测结果，生成 Markdown 格式的评测报告
"""

import os
# 从 config.py 读取配置，避免硬编码
from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL

# 设置 DeepEval 需要的环境变量
os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY
os.environ["OPENAI_MODEL_NAME"] = DEEPSEEK_MODEL
os.environ["OPENAI_BASE_URL"] = DEEPSEEK_BASE_URL

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


def generate_report(results, meta_info, output_path="eval_report.md"):
    """生成 Markdown 评测报告"""

    report_lines = []

    # 报告头部
    report_lines.append("# RAGuard 评测报告")
    report_lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"评测数据集：{len(meta_info)} 条法律咨询问答")
    report_lines.append(f"评测维度：Answer Relevancy / Faithfulness / Contextual Precision")
    report_lines.append(f"通过阈值：0.7\n")
    report_lines.append("---\n")

    # 从 results 中提取分数
    # DeepEval 的 evaluate() 返回结果包含每个 test_case 的指标得分
    # 这里用简化方式处理，实际结构可能需要根据DeepEval版本微调
    score_data = []
    for i, test_result in enumerate(results.test_results):
        row = {
            "question": meta_info[i]["question"][:40] + "...",
            "category": meta_info[i]["category"],
            "difficulty": meta_info[i]["difficulty"],
        }
        for metric_data in test_result.metrics_data:
            # DeepEval 使用 name 属性而不是 metric_name
            metric_name = getattr(metric_data, 'name', None) or getattr(metric_data, 'metric_name', 'Unknown')
            row[metric_name] = round(metric_data.score, 3)
            row[f"{metric_name}_passed"] = metric_data.success
        score_data.append(row)

    # 总体得分
    report_lines.append("## 总体得分\n")
    all_ar = [r.get("Answer Relevancy", 0) for r in score_data if "Answer Relevancy" in r]
    all_fa = [r.get("Faithfulness", 0) for r in score_data if "Faithfulness" in r]
    all_cp = [r.get("Contextual Precision", 0) for r in score_data if "Contextual Precision" in r]

    if all_ar:
        report_lines.append(f"- **Answer Relevancy 均分**: {sum(all_ar)/len(all_ar):.3f}")
        report_lines.append(f"- **Faithfulness 均分**: {sum(all_fa)/len(all_fa):.3f}")
        report_lines.append(f"- **Contextual Precision 均分**: {sum(all_cp)/len(all_cp):.3f}")

    # 按类别分组
    report_lines.append("\n## 按法律类别分组\n")
    for category in ["劳动法", "刑法"]:
        cat_data = [r for r in score_data if r["category"] == category]
        if not cat_data:
            continue
        cat_ar = [r.get("Answer Relevancy", 0) for r in cat_data if "Answer Relevancy" in r]
        cat_fa = [r.get("Faithfulness", 0) for r in cat_data if "Faithfulness" in r]
        cat_cp = [r.get("Contextual Precision", 0) for r in cat_data if "Contextual Precision" in r]
        report_lines.append(f"### {category}\n")
        if cat_ar:
            report_lines.append(f"- Answer Relevancy: {sum(cat_ar)/len(cat_ar):.3f}")
            report_lines.append(f"- Faithfulness: {sum(cat_fa)/len(cat_fa):.3f}")
            report_lines.append(f"- Contextual Precision: {sum(cat_cp)/len(cat_cp):.3f}")
        report_lines.append("")

    # 按难度分组
    report_lines.append("## 按难度分组\n")
    for diff in ["easy", "medium", "hard"]:
        diff_data = [r for r in score_data if r["difficulty"] == diff]
        if not diff_data:
            continue
        diff_ar = [r.get("Answer Relevancy", 0) for r in diff_data if "Answer Relevancy" in r]
        diff_fa = [r.get("Faithfulness", 0) for r in diff_data if "Faithfulness" in r]
        diff_cp = [r.get("Contextual Precision", 0) for r in diff_data if "Contextual Precision" in r]
        report_lines.append(f"### {diff}\n")
        if diff_ar:
            report_lines.append(f"- Answer Relevancy: {sum(diff_ar)/len(diff_ar):.3f}")
            report_lines.append(f"- Faithfulness: {sum(diff_fa)/len(diff_fa):.3f}")
            report_lines.append(f"- Contextual Precision: {sum(diff_cp)/len(diff_cp):.3f}")
        report_lines.append("")

    # Bad Case：低于阈值的用例
    report_lines.append("## Bad Cases（未达标用例）\n")
    bad_cases = []
    for r in score_data:
        failed_metrics = []
        for key, val in r.items():
            if key.endswith("_passed") and val is False:
                metric_name = key.replace("_passed", "")
                failed_metrics.append(metric_name)
        if failed_metrics:
            bad_cases.append((r, failed_metrics))

    if bad_cases:
        for r, failed in bad_cases:
            report_lines.append(f"- **​{r['question']}​** [{r['category']}/{r['difficulty']}]")
            report_lines.append(f"  未通过: {', '.join(failed)}")
            for f in failed:
                score_key = f
                if score_key in r:
                    report_lines.append(f"  - {f}: {r[score_key]}")
            report_lines.append("")
    else:
        report_lines.append("所有用例均通过阈值！\n")

    # 写入文件
    report_content = "\n".join(report_lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n✅ 评测报告已生成: {output_path}")
    return report_content


if __name__ == "__main__":
    results, meta_info = run_full_evaluation()
    generate_report(results, meta_info)
