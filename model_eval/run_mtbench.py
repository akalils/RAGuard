"""
MT-Bench 多轮对话评测 + LLM-as-Judge
简化版：8 类别，2 轮对话，强模型（judge）给 1-10 分

使用方法：
    python model_eval/run_mtbench.py --target gpt-5.4-nano --judge gpt-4o
    python model_eval/run_mtbench.py --target deepseek-chat --judge gpt-4o --limit 3
"""
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import sys
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


# 8 个 MT-Bench 类别（简化版，每类 1 个示例 2 轮对话）
MT_BENCH_QUESTIONS = {
    "writing": {
        "category_zh": "写作",
        "turns": [
            "请写一个关于人工智能对未来教育影响的短文，要求有具体例子，字数 200 字左右。",
            "现在请把上面的短文改写成适合初中生阅读的版本，语言要更通俗易懂。",
        ],
    },
    "roleplay": {
        "category_zh": "角色扮演",
        "turns": [
            "请你扮演一位资深 Python 开发者，向一个有 1 年经验的工程师解释什么是装饰器。",
            "如果我想装饰一个带参数的函数，比如记录函数调用时间，能再给个例子吗？",
        ],
    },
    "reasoning": {
        "category_zh": "推理",
        "turns": [
            "一个房间里有三个人：张三、李四、王五。已知：① 张三比李四大 3 岁；② 王五比李四年轻 5 岁；③ 三人平均年龄 28 岁。问：各是多少岁？",
            "如果再加一个条件：张三的年龄是王五的 2 倍，能重新求解吗？",
        ],
    },
    "math": {
        "category_zh": "数学",
        "turns": [
            "求解方程 x² - 5x + 6 = 0，给出详细步骤。",
            "如果把方程改成 x² - 5x + k = 0，k 取什么值时方程有两个相等的实数根？",
        ],
    },
    "coding": {
        "category_zh": "编程",
        "turns": [
            "请用 Python 写一个函数，输入一个字符串，返回其中最长的回文子串。要求时间复杂度优于 O(n³)。",
            "如果输入是空字符串或单个字符，你的代码能正确处理吗？边界条件测试一下。",
        ],
    },
    "extraction": {
        "category_zh": "信息抽取",
        "turns": [
            "从下面这段话中提取所有人物的姓名、职位和公司：'李华是腾讯云的首席架构师，王芳是阿里巴巴的资深算法工程师，张三是字节跳动的产品经理。'",
            "如果再加上人物的所在城市：李华在深圳、王芳在杭州、张三在北京，重新整理成 JSON 格式。",
        ],
    },
    "stem": {
        "category_zh": "科学",
        "turns": [
            "请用初中生能理解的方式解释什么是光合作用。",
            "如果植物长时间见不到光，会发生什么？光合作用的哪个环节会先受到影响？",
        ],
    },
    "humanities": {
        "category_zh": "人文",
        "turns": [
            "请简述《红楼梦》的主题思想。",
            "鲁迅对《红楼梦》的评价'经学家看见《易》，道学家看见淫，才子看见缠绵，革命家看见排满'反映了什么文学批评现象？",
        ],
    },
}


JUDGE_PROMPT_TEMPLATE = """请你作为一个严格的评分员，对下面的多轮对话中【模型回答】的质量进行 1-10 分的评分。

评分维度：
1. 准确性：回答是否正确、有无明显错误
2. 完整性：是否覆盖了问题的所有要点
3. 连贯性：多轮对话之间是否逻辑连贯、是否考虑上下文
4. 表达：语言是否清晰、有条理

【用户问题】
{question}

【模型回答】
{answer}

请先给出一段简短的分析（1-2 句话），然后在最后一行输出：
分数：<1-10 的整数>
"""


def call_llm(prompt: str, model: str) -> str:
    """调用 LLM API（Azure OpenAI 兼容模式）"""
    url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_completion_tokens": 1500,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_llm_multiturn(turns: List[str], model: str) -> List[str]:
    """多轮对话：每一轮都基于之前的对话历史"""
    messages = []
    responses = []
    for turn in turns:
        messages.append({"role": "user", "content": turn})
        url = f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_completion_tokens": 800,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        responses.append(content)
        messages.append({"role": "assistant", "content": content})
        time.sleep(0.5)
    return responses


def judge_response(question: str, answer: str, judge_model: str) -> Tuple[int, str]:
    """用 judge LLM 评分，返回 (分数, 评判理由)"""
    prompt = JUDGE_PROMPT_TEMPLATE.format(question=question, answer=answer)
    try:
        raw = call_llm(prompt, judge_model)
        # 提取分数
        import re
        match = re.search(r"分数[：:]\s*(\d+)", raw)
        if match:
            score = int(match.group(1))
            score = max(1, min(10, score))  # 限制在 1-10
        else:
            score = -1  # 解析失败
        return score, raw
    except Exception as e:
        return -1, f"ERROR: {e}"


def evaluate_category(cat: str, data: Dict, target_model: str, judge_model: str) -> Dict:
    """评测单个类别"""
    print(f"\n📝 评测类别: {data['category_zh']} ({cat})")

    # 1. 让 target 模型进行多轮对话
    try:
        responses = call_llm_multiturn(data["turns"], target_model)
    except Exception as e:
        print(f"  ❌ target 模型调用失败: {e}")
        return {
            "category": cat,
            "category_zh": data["category_zh"],
            "error": str(e),
        }

    # 2. judge 模型给每轮评分
    turn_scores = []
    turn_judgments = []
    for i, (q, r) in enumerate(zip(data["turns"], responses)):
        score, judgment = judge_response(q, r, judge_model)
        turn_scores.append(score)
        turn_judgments.append({
            "turn": i + 1,
            "question": q,
            "response": r,
            "score": score,
            "judgment": judgment,
        })
        print(f"  轮次 {i+1}: 分数={score}")

    # 3. 汇总（MT-Bench 官方：每轮单独评分，最终分 = 各轮均分）
    valid_scores = [s for s in turn_scores if s > 0]
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0

    return {
        "category": cat,
        "category_zh": data["category_zh"],
        "turn_scores": turn_scores,
        "avg_score": round(avg_score, 2),
        "turn_judgments": turn_judgments,
    }


def main():
    parser = argparse.ArgumentParser(description="MT-Bench 评测脚本")
    parser.add_argument("--target", type=str, default=OPENAI_MODEL,
                        help=f"被评测模型（默认：{OPENAI_MODEL}）")
    parser.add_argument("--judge", type=str, default=OPENAI_MODEL,
                        help="评判模型（默认用同一个模型）")
    parser.add_argument("--limit", type=int, default=None,
                        help="只评测前 N 个类别（调试用）")
    parser.add_argument("--output", type=str, default=None,
                        help="结果输出路径")
    args = parser.parse_args()

    print(f"=" * 60)
    print(f"MT-Bench 评测 | target={args.target} | judge={args.judge}")
    print(f"=" * 60)

    categories = list(MT_BENCH_QUESTIONS.keys())
    if args.limit:
        categories = categories[:args.limit]

    all_results = []
    for cat in categories:
        data = MT_BENCH_QUESTIONS[cat]
        result = evaluate_category(cat, data, args.target, args.judge)
        all_results.append(result)

    # 汇总
    valid_results = [r for r in all_results if "avg_score" in r and r["avg_score"] > 0]
    overall_avg = sum(r["avg_score"] for r in valid_results) / len(valid_results) if valid_results else 0

    summary = {
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_model": args.target,
        "judge_model": args.judge,
        "categories": [r["category"] for r in all_results],
        "overall_avg_score": round(overall_avg, 2),
        "per_category": all_results,
    }

    print(f"\n{'=' * 60}")
    print(f"📊 汇总")
    print(f"{'=' * 60}")
    print(f"被评测模型: {args.target}")
    print(f"评判模型:   {args.judge}")
    print(f"总均分:     {overall_avg:.2f} / 10")
    print(f"\n各类别:")
    for r in all_results:
        if "avg_score" in r:
            print(f"  {r['category_zh']:<10} {r['avg_score']:.2f} / 10 (轮次分: {r['turn_scores']})")

    # 写文件
    if args.output:
        out_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = f"model_eval/mtbench_results/{args.target.replace('/', '_')}_{timestamp}.json"

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存: {out_path}")


if __name__ == "__main__":
    main()
