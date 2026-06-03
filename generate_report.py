"""
评测报告生成器
DeepEval (3 指标) + RAGAS (4 指标) + 检索指标 (MRR/NDCG)
SQLite 持久化 + 回归对比
"""

import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_MODEL_NAME"] = OPENAI_MODEL
os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL

import math
import re
import sqlite3
import yaml
from datetime import datetime
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualPrecisionMetric
from deepeval.models import DeepEvalBaseLLM
from openai import AsyncOpenAI
from ragas_eval import run_ragas_evaluation
from rag_pipeline import ask, load_vector_store

DB_PATH = "eval_history.db"


# ============================================================
# 1. 检索指标：MRR / NDCG
# ============================================================

def _extract_key_phrases(text: str) -> set[str]:
    """从参考答案中提取关键法律条文引用（如《劳动合同法》第XX条）"""
    patterns = [
        r"《[^》]+》第[一二三四五六七八九十百千零0-9]+条",
        r"第[一二三四五六七八九十百千零0-9]+条",
        r"百分之[一二三四五六七八九十百千]+",
        r"[一二三四五六七八九十]+年",
    ]
    phrases = set()
    for p in patterns:
        phrases.update(re.findall(p, text))
    return phrases


def compute_retrieval_metrics(
    retrieved_docs: list, reference_answer: str, k: int = 5
) -> dict:
    """
    计算单个问题的检索质量指标：
    - MRR: 第一个相关文档排名的倒数
    - NDCG@k: 标准化折损累积增益（二值相关性）
    """
    if not retrieved_docs or not reference_answer:
        return {"mrr": 0.0, "ndcg": 0.0}

    key_phrases = _extract_key_phrases(reference_answer)
    if not key_phrases:
        # fallback: 用参考答案的前 20 个字作为匹配
        key_phrases = {reference_answer[:20]}

    # 标记每个检索结果是否相关
    relevance = []
    for doc in retrieved_docs[:k]:
        content = doc.page_content
        matched = sum(1 for p in key_phrases if p in content)
        relevance.append(1 if matched > 0 else 0)

    # MRR: 第一个相关文档排名的倒数
    mrr = 0.0
    for i, rel in enumerate(relevance):
        if rel == 1:
            mrr = 1.0 / (i + 1)
            break

    # NDCG@k
    dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(relevance))
    ideal = sorted(relevance, reverse=True)
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal))
    ndcg = dcg / idcg if idcg > 0 else 0.0

    return {"mrr": round(mrr, 4), "ndcg": round(ndcg, 4), "retrieved_count": len(retrieved_docs)}


# ============================================================
# 2. SQLite 持久化
# ============================================================

def init_db():
    """初始化 SQLite 数据库"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eval_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time TEXT NOT NULL,
            dataset_size INTEGER,
            -- DeepEval
            de_answer_relevancy REAL,
            de_faithfulness REAL,
            de_context_precision REAL,
            -- RAGAS
            ragas_faithfulness REAL,
            ragas_context_precision REAL,
            ragas_context_recall REAL,
            ragas_answer_relevancy REAL,
            -- 检索
            mrr REAL,
            ndcg REAL,
            -- 元数据
            llm_model TEXT,
            embedding_model TEXT,
            chunk_size INTEGER,
            chunk_overlap INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eval_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            question TEXT,
            category TEXT,
            difficulty TEXT,
            -- DeepEval per-question
            de_answer_relevancy REAL,
            de_faithfulness REAL,
            de_context_precision REAL,
            -- RAGAS per-question
            ragas_faithfulness REAL,
            ragas_context_precision REAL,
            ragas_context_recall REAL,
            ragas_answer_relevancy REAL,
            -- 检索
            mrr REAL,
            ndcg REAL,
            retrieved_count INTEGER,
            FOREIGN KEY (run_id) REFERENCES eval_runs(id)
        )
    """)
    conn.commit()
    return conn


def save_run(conn, run_meta: dict, q_scores: list[dict]):
    """保存一次评测结果"""
    cur = conn.execute(
        """INSERT INTO eval_runs
        (run_time, dataset_size, de_answer_relevancy, de_faithfulness,
         de_context_precision, ragas_faithfulness, ragas_context_precision,
         ragas_context_recall, ragas_answer_relevancy, mrr, ndcg,
         llm_model, embedding_model, chunk_size, chunk_overlap)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            run_meta["run_time"], run_meta["dataset_size"],
            run_meta["de_answer_relevancy"], run_meta["de_faithfulness"],
            run_meta["de_context_precision"],
            run_meta["ragas_faithfulness"], run_meta["ragas_context_precision"],
            run_meta["ragas_context_recall"], run_meta["ragas_answer_relevancy"],
            run_meta["mrr"], run_meta["ndcg"],
            run_meta["llm_model"], run_meta["embedding_model"],
            run_meta["chunk_size"], run_meta["chunk_overlap"],
        ),
    )
    run_id = cur.lastrowid
    for q in q_scores:
        conn.execute(
            """INSERT INTO eval_questions
            (run_id, question, category, difficulty,
             de_answer_relevancy, de_faithfulness, de_context_precision,
             ragas_faithfulness, ragas_context_precision, ragas_context_recall,
             ragas_answer_relevancy, mrr, ndcg, retrieved_count)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                run_id, q["question"], q["category"], q["difficulty"],
                q["de_answer_relevancy"], q["de_faithfulness"],
                q["de_context_precision"],
                q["ragas_faithfulness"], q["ragas_context_precision"],
                q["ragas_context_recall"], q["ragas_answer_relevancy"],
                q["mrr"], q["ndcg"], q["retrieved_count"],
            ),
        )
    conn.commit()
    return run_id


def get_last_run(conn) -> dict | None:
    """获取上一次评测结果"""
    row = conn.execute(
        "SELECT * FROM eval_runs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    cols = [d[0] for d in conn.execute("SELECT * FROM eval_runs LIMIT 0").description]
    return dict(zip(cols, row))


def get_last_run_questions(conn, run_id: int) -> list[dict]:
    """获取某次评测的各题分数"""
    rows = conn.execute(
        "SELECT * FROM eval_questions WHERE run_id = ?", (run_id,)
    ).fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM eval_questions LIMIT 0").description]
    return [dict(zip(cols, r)) for r in rows]


def compare_runs(current: dict, previous: dict, threshold: float = 0.05) -> list[dict]:
    """
    对比两次评测，找出回退指标（下降超过 threshold 的）
    """
    metrics = [
        "de_answer_relevancy", "de_faithfulness", "de_context_precision",
        "ragas_faithfulness", "ragas_context_precision",
        "ragas_context_recall", "ragas_answer_relevancy",
        "mrr", "ndcg",
    ]
    regressions = []
    for m in metrics:
        cur_val = current.get(m, 0)
        prev_val = previous.get(m, 0)
        if prev_val and cur_val < prev_val - threshold:
            regressions.append({
                "metric": m,
                "current": cur_val,
                "previous": prev_val,
                "delta": cur_val - prev_val,
            })
    return regressions


# ============================================================
# 3. 评测执行
# ============================================================

def run_full_evaluation():
    """执行 DeepEval 评测 + 检索指标"""
    vectorstore = load_vector_store()
    dataset = load_eval_dataset()

    test_cases = []
    meta_info = []
    retrieval_results = []  # 保存检索结果用于计算 MRR/NDCG

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
            "reference_answer": item["reference_answer"],
        })
        retrieval_results.append({
            "docs": result["retrieved_docs"],
            "count": len(result["retrieved_docs"]),
        })

    # DeepEval 评测
    eval_model = AzureJudgeLLM()
    metrics = [
        AnswerRelevancyMetric(model=eval_model, threshold=0.7),
        FaithfulnessMetric(model=eval_model, threshold=0.7),
        ContextualPrecisionMetric(model=eval_model, threshold=0.7),
    ]
    deepeval_results = evaluate(test_cases=test_cases, metrics=metrics)

    # 计算检索指标
    retrieval_metrics = []
    for i, item in enumerate(meta_info):
        rm = compute_retrieval_metrics(
            retrieval_results[i]["docs"],
            item["reference_answer"],
        )
        rm["retrieved_count"] = retrieval_results[i]["count"]
        retrieval_metrics.append(rm)

    return deepeval_results, meta_info, retrieval_metrics


def run_ragas_batch():
    """跑 RAGAS 评测"""
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


def load_eval_dataset(path="eval_dataset.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ============================================================
# 4. 报告生成
# ============================================================

class AzureJudgeLLM(DeepEvalBaseLLM):
    def __init__(self):
        self._client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        self._model = OPENAI_MODEL

    def load_model(self):
        return self._client

    def generate(self, prompt, schema=None):
        if schema is None:
            r = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
            return r.choices[0].message.content
        r = self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema,
        )
        return r.choices[0].message.parsed

    async def a_generate(self, prompt, schema=None):
        if schema is None:
            r = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
            return r.choices[0].message.content
        r = await self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema,
        )
        return r.choices[0].message.parsed

    def get_model_name(self):
        return self._model


METRIC_CN = {
    "de_answer_relevancy":  "Answer Relevancy (DeepEval)",
    "de_faithfulness":      "Faithfulness (DeepEval)",
    "de_context_precision": "Context Precision (DeepEval)",
    "ragas_faithfulness":      "Faithfulness (RAGAS)",
    "ragas_context_precision": "Context Precision (RAGAS)",
    "ragas_context_recall":    "Context Recall (RAGAS)",
    "ragas_answer_relevancy":  "Answer Relevancy (RAGAS)",
    "mrr":  "MRR",
    "ndcg": "NDCG@5",
}


def generate_report(
    deepeval_results, deepeval_meta, retrieval_metrics,
    ragas_result, ragas_meta,
    regressions=None,
    output_path="eval_report.md",
):
    """合并 DeepEval + RAGAS + 检索指标，生成 Markdown 报告"""
    lines = []
    lines.append("# RAGuard 评测报告")
    lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"评测数据集：{len(deepeval_meta)} 条法律咨询问答")
    lines.append(f"评测框架：DeepEval (3) + RAGAS (4) + 检索 (MRR/NDCG)")
    lines.append(f"通过阈值：0.7\n")

    # ---- 回归告警 ----
    if regressions:
        lines.append("## ⚠️ 回归告警\n")
        lines.append("以下指标相比上次评测下降超过 5%：\n")
        lines.append("| 指标 | 上次 | 本次 | 变化 |")
        lines.append("|------|------|------|------|")
        for r in regressions:
            name = METRIC_CN.get(r["metric"], r["metric"])
            lines.append(
                f"| {name} | {r['previous']:.3f} | {r['current']:.3f} | "
                f"**{r['delta']:+.3f}** |"
            )
        lines.append("")

    lines.append("---\n")

    # ============ 1. 总体得分 ============
    lines.append("## 总体得分\n")

    # DeepEval
    de_score = []
    for tr in deepeval_results.test_results:
        row = {}
        for md in tr.metrics_data:
            name = getattr(md, "name", None) or getattr(md, "metric_name", "Unknown")
            row[name] = round(md.score, 3)
            row[f"{name}_passed"] = md.success
        de_score.append(row)

    lines.append("### DeepEval\n")
    for metric in ["Answer Relevancy", "Faithfulness", "Contextual Precision"]:
        vals = [r.get(metric, 0) for r in de_score if metric in r]
        if vals:
            lines.append(f"- **{metric} 均分**: {sum(vals)/len(vals):.3f}")

    # RAGAS
    lines.append("\n### RAGAS\n")
    overall = ragas_result["overall"]
    ragas_cn = {
        "faithfulness":      "Faithfulness（忠实度）",
        "context_precision": "Context Precision（检索精度）",
        "context_recall":    "Context Recall（检索召回）",
        "answer_relevancy":  "Answer Relevancy（回答相关性）",
    }
    for k, v in overall.items():
        cn = ragas_cn.get(k, k)
        lines.append(f"- **{cn}**: {v:.3f}")

    # 检索指标
    lines.append("\n### 检索质量\n")
    mrr_vals = [r["mrr"] for r in retrieval_metrics]
    ndcg_vals = [r["ndcg"] for r in retrieval_metrics]
    avg_mrr = sum(mrr_vals) / len(mrr_vals) if mrr_vals else 0
    avg_ndcg = sum(ndcg_vals) / len(ndcg_vals) if ndcg_vals else 0
    lines.append(f"- **MRR 均分**: {avg_mrr:.3f}")
    lines.append(f"- **NDCG@5 均分**: {avg_ndcg:.3f}")

    # ============ 2. 按类别分组 ============
    lines.append("\n## 按法律类别分组\n")
    categories = sorted(set(m["category"] for m in deepeval_meta))
    for cat in categories:
        lines.append(f"### {cat}\n")
        # DeepEval
        cat_de = [r for r, m in zip(de_score, deepeval_meta) if m["category"] == cat]
        if cat_de:
            lines.append("**DeepEval:**")
            for metric in ["Answer Relevancy", "Faithfulness", "Contextual Precision"]:
                vals = [r.get(metric, 0) for r in cat_de if metric in r]
                if vals:
                    lines.append(f"- {metric}: {sum(vals)/len(vals):.3f}")
        # RAGAS
        cat_ragas = [r for r, m in zip(ragas_result["per_question"], ragas_meta) if m["category"] == cat]
        if cat_ragas:
            lines.append("\n**RAGAS:**")
            for k in ["faithfulness", "context_precision", "context_recall", "answer_relevancy"]:
                vals = [r.get(k) for r in cat_ragas if r.get(k) is not None]
                if vals:
                    lines.append(f"- {ragas_cn.get(k, k)}: {sum(vals)/len(vals):.3f}")
        # 检索
        cat_rm = [r for r, m in zip(retrieval_metrics, deepeval_meta) if m["category"] == cat]
        if cat_rm:
            lines.append("\n**检索:**")
            cat_mrr = [r["mrr"] for r in cat_rm]
            cat_ndcg = [r["ndcg"] for r in cat_rm]
            lines.append(f"- MRR: {sum(cat_mrr)/len(cat_mrr):.3f}")
            lines.append(f"- NDCG@5: {sum(cat_ndcg)/len(cat_ndcg):.3f}")
        lines.append("")

    # ============ 3. Bad Cases ============
    lines.append("## Bad Cases\n")

    # DeepEval bad cases
    de_bad = []
    for r, m in zip(de_score, deepeval_meta):
        failed = [k.replace("_passed", "") for k, v in r.items() if k.endswith("_passed") and v is False]
        if failed:
            de_bad.append((m, failed, r))
    if de_bad:
        lines.append("### DeepEval 未达标用例\n")
        for m, failed, r in de_bad:
            lines.append(f"- **{m['question'][:40]}...** [{m['category']}/{m['difficulty']}]")
            lines.append(f"  未通过: {', '.join(failed)}")
        lines.append("")

    # RAGAS bad cases
    ragas_bad = []
    for r, m in zip(ragas_result["per_question"], ragas_meta):
        failed = [k for k in ["faithfulness", "context_precision", "context_recall", "answer_relevancy"]
                  if r.get(k) is not None and r[k] < 0.7]
        if failed:
            ragas_bad.append((m, failed, r))
    if ragas_bad:
        lines.append("### RAGAS 未达标用例\n")
        for m, failed, r in ragas_bad:
            lines.append(f"- **{m['question'][:40]}...** [{m['category']}/{m['difficulty']}]")
            for f in failed:
                lines.append(f"  - {ragas_cn.get(f, f)}: {r[f]:.3f}")
        lines.append("")

    # 低 MRR 用例
    low_mrr = [(m, rm) for m, rm in zip(deepeval_meta, retrieval_metrics) if rm["mrr"] < 0.5]
    if low_mrr:
        lines.append("### 低检索质量用例（MRR < 0.5）\n")
        for m, rm in low_mrr:
            lines.append(f"- **{m['question'][:40]}...** MRR={rm['mrr']:.2f} NDCG={rm['ndcg']:.2f} (检索到 {rm['retrieved_count']} 条)")
        lines.append("")

    # ---- 写文件 ----
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ 评测报告已生成: {output_path}")
    return content


# ============================================================
# 5. 主流程
# ============================================================

if __name__ == "__main__":
    conn = init_db()

    # 检查上一次结果
    last_run = get_last_run(conn)

    # DeepEval + 检索指标
    deepeval_results, deepeval_meta, retrieval_metrics = run_full_evaluation()
    # RAGAS
    ragas_result, ragas_meta = run_ragas_batch()

    # 汇总本次分数
    de_scores = []
    for tr in deepeval_results.test_results:
        row = {}
        for md in tr.metrics_data:
            name = getattr(md, "name", None) or getattr(md, "metric_name", "Unknown")
            row[name] = round(md.score, 3)
        de_scores.append(row)

    ragas_overall = ragas_result["overall"]
    mrr_vals = [r["mrr"] for r in retrieval_metrics]
    ndcg_vals = [r["ndcg"] for r in retrieval_metrics]

    run_meta = {
        "run_time":              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_size":          len(deepeval_meta),
        "de_answer_relevancy":   sum(r.get("Answer Relevancy", 0) for r in de_scores) / len(de_scores),
        "de_faithfulness":       sum(r.get("Faithfulness", 0) for r in de_scores) / len(de_scores),
        "de_context_precision":  sum(r.get("Contextual Precision", 0) for r in de_scores) / len(de_scores),
        "ragas_faithfulness":    ragas_overall.get("faithfulness", 0),
        "ragas_context_precision": ragas_overall.get("context_precision", 0),
        "ragas_context_recall":  ragas_overall.get("context_recall", 0),
        "ragas_answer_relevancy": ragas_overall.get("answer_relevancy", 0),
        "mrr":                   sum(mrr_vals) / len(mrr_vals) if mrr_vals else 0,
        "ndcg":                  sum(ndcg_vals) / len(ndcg_vals) if ndcg_vals else 0,
        "llm_model":             OPENAI_MODEL,
        "embedding_model":       "shibing624/text2vec-base-chinese",
        "chunk_size":            400,
        "chunk_overlap":         200,
    }

    # 合并各题分数
    q_scores = []
    for i, m in enumerate(deepeval_meta):
        de = de_scores[i] if i < len(de_scores) else {}
        ra = ragas_result["per_question"][i] if i < len(ragas_result["per_question"]) else {}
        rm = retrieval_metrics[i] if i < len(retrieval_metrics) else {}
        q_scores.append({
            "question":            m["question"],
            "category":            m["category"],
            "difficulty":          m["difficulty"],
            "de_answer_relevancy": de.get("Answer Relevancy"),
            "de_faithfulness":     de.get("Faithfulness"),
            "de_context_precision": de.get("Contextual Precision"),
            "ragas_faithfulness":      ra.get("faithfulness"),
            "ragas_context_precision": ra.get("context_precision"),
            "ragas_context_recall":    ra.get("context_recall"),
            "ragas_answer_relevancy":  ra.get("answer_relevancy"),
            "mrr":                 rm.get("mrr"),
            "ndcg":                rm.get("ndcg"),
            "retrieved_count":     rm.get("retrieved_count", 0),
        })

    # 回归对比
    regressions = None
    if last_run:
        regressions = compare_runs(run_meta, last_run)
        if regressions:
            print(f"\n⚠️ 发现 {len(regressions)} 个回退指标！")
            for r in regressions:
                print(f"  {METRIC_CN.get(r['metric'], r['metric'])}: {r['previous']:.3f} → {r['current']:.3f} ({r['delta']:+.3f})")
        else:
            print("\n✅ 无回归，所有指标持平或提升。")

    # 保存到 SQLite
    run_id = save_run(conn, run_meta, q_scores)
    print(f"💾 结果已保存到 {DB_PATH} (run_id={run_id})")

    # 生成报告
    generate_report(
        deepeval_results, deepeval_meta, retrieval_metrics,
        ragas_result, ragas_meta,
        regressions=regressions,
    )

    conn.close()
