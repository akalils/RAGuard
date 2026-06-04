"""
C-Eval 中文基座模型评测
覆盖 6 个代表性学科：计算机网络、计算机组成、操作系统、马克思主义、中国历史、高等数学

使用方法：
    python model_eval/run_ceval.py --model deepseek-chat --n_shot 5
    python model_eval/run_ceval.py --model gpt-5.4-nano --n_shot 0
"""
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import sys
import json
import time
import argparse
import requests
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL


# 6 个代表性学科
CEVAL_SUBJECTS = {
    "computer_network":  "计算机网络",
    "computer_architecture": "计算机组成",
    "operating_system":  "操作系统",
    "marxism":           "马克思主义基本原理",
    "chinese_history":   "中国近现代史",
    "college_math":      "高等数学",
}


# 极简 C-Eval 数据集（每学科 5-10 道示例题）
# 来源：C-Eval 公开数据集（https://cevalbenchmark.com/）
CEVAL_QUESTIONS = {
    "computer_network": [
        {
            "id": 1,
            "question": "OSI 参考模型的第 3 层是（ ）。",
            "A": "物理层", "B": "数据链路层", "C": "网络层", "D": "传输层",
            "answer": "C"
        },
        {
            "id": 2,
            "question": "TCP 协议是一种（ ）协议。",
            "A": "无连接的、不可靠的", "B": "无连接的、可靠的",
            "C": "面向连接的、不可靠的", "D": "面向连接的、可靠的",
            "answer": "D"
        },
        {
            "id": 3,
            "question": "HTTP 协议默认使用的端口号是（ ）。",
            "A": "21", "B": "23", "C": "80", "D": "443",
            "answer": "C"
        },
        {
            "id": 4,
            "question": "下列哪一项不属于网络拓扑结构？（ ）",
            "A": "星型", "B": "环型", "C": "总线型", "D": "分支型",
            "answer": "D"
        },
        {
            "id": 5,
            "question": "IP 地址 192.168.1.1 属于哪类地址？（ ）",
            "A": "A 类", "B": "B 类", "C": "C 类", "D": "D 类",
            "answer": "C"
        },
    ],
    "computer_architecture": [
        {
            "id": 1,
            "question": "冯·诺依曼计算机的基本工作原理是（ ）。",
            "A": "串行工作", "B": "存储程序",
            "C": "并行工作", "D": "分时工作",
            "answer": "B"
        },
        {
            "id": 2,
            "question": "在计算机系统中，Cache 位于（ ）之间。",
            "A": "CPU 和主存", "B": "主存和磁盘",
            "C": "CPU 和寄存器", "D": "磁盘和磁带",
            "answer": "A"
        },
        {
            "id": 3,
            "question": "下列哪种存储器的速度最快？（ ）",
            "A": "硬盘", "B": "内存", "C": "Cache", "D": "寄存器",
            "answer": "D"
        },
        {
            "id": 4,
            "question": "CPU 中的 ALU 负责执行（ ）。",
            "A": "算术运算和逻辑运算", "B": "存储数据",
            "C": "控制指令流", "D": "内存访问",
            "answer": "A"
        },
        {
            "id": 5,
            "question": "指令周期由若干个 CPU 周期组成，一个 CPU 周期又由若干个（ ）组成。",
            "A": "指令", "B": "时钟周期", "C": "总线周期", "D": "存储周期",
            "answer": "B"
        },
    ],
    "operating_system": [
        {
            "id": 1,
            "question": "进程和线程的根本区别是（ ）。",
            "A": "大小不同", "B": "是否拥有资源",
            "C": "是否独立运行", "D": "数量不同",
            "answer": "B"
        },
        {
            "id": 2,
            "question": "在操作系统中，进程间通信方式不包括（ ）。",
            "A": "管道", "B": "信号量", "C": "消息队列", "D": "中断",
            "answer": "D"
        },
        {
            "id": 3,
            "question": "死锁的四个必要条件不包括（ ）。",
            "A": "互斥条件", "B": "请求和保持",
            "C": "可剥夺条件", "D": "循环等待",
            "answer": "C"
        },
        {
            "id": 4,
            "question": "分页存储管理中，页大小的选择会影响（ ）。",
            "A": "页表大小", "B": "内部碎片", "C": "外部碎片", "D": "以上都是",
            "answer": "B"
        },
        {
            "id": 5,
            "question": "下列哪种调度算法可能导致进程长时间等待（饥饿）？（ ）",
            "A": "FCFS", "B": "时间片轮转",
            "C": "短作业优先", "D": "多级反馈队列",
            "answer": "C"
        },
    ],
    "marxism": [
        {
            "id": 1,
            "question": "马克思主义哲学的精髓是（ ）。",
            "A": "辩证唯物主义和历史唯物主义",
            "B": "实践论和认识论",
            "C": "矛盾论和方法论",
            "D": "剩余价值学说",
            "answer": "A"
        },
        {
            "id": 2,
            "question": "社会基本矛盾是（ ）。",
            "A": "生产力和生产关系、经济基础和上层建筑",
            "B": "人与自然的矛盾、人与社会的矛盾",
            "C": "先进和落后的矛盾、正确和错误的矛盾",
            "D": "主观和客观的矛盾、实践和认识的矛盾",
            "answer": "A"
        },
        {
            "id": 3,
            "question": "马克思主义认为，劳动是（ ）。",
            "A": "人类生存的唯一手段", "B": "人类和动物的本质区别",
            "C": "社会财富的唯一源泉", "D": "商品价值的唯一源泉",
            "answer": "B"
        },
        {
            "id": 4,
            "question": "商品二因素的矛盾是（ ）。",
            "A": "使用价值和价值的矛盾",
            "B": "具体劳动和抽象劳动的矛盾",
            "C": "私人劳动和社会劳动的矛盾",
            "D": "个别价值和社会价值的矛盾",
            "answer": "A"
        },
        {
            "id": 5,
            "question": "剩余价值率是（ ）的比率。",
            "A": "剩余价值与不变资本", "B": "剩余价值与可变资本",
            "C": "剩余价值与全部预付资本", "D": "剩余价值与利润",
            "answer": "B"
        },
    ],
    "chinese_history": [
        {
            "id": 1,
            "question": "中国近代史的开端是（ ）。",
            "A": "虎门销烟（1839）", "B": "鸦片战争（1840）",
            "C": "太平天国起义（1851）", "D": "甲午战争（1894）",
            "answer": "B"
        },
        {
            "id": 2,
            "question": "洋务运动的口号是（ ）。",
            "A": "师夷长技以制夷", "B": "中学为体，西学为用",
            "C": "民主与科学", "D": "三民主义",
            "answer": "B"
        },
        {
            "id": 3,
            "question": "五四运动爆发的导火线是（ ）。",
            "A": "巴黎和会中国外交失败", "B": "《凡尔赛和约》的签订",
            "C": "新文化运动的推动", "D": "十月革命的影响",
            "answer": "A"
        },
        {
            "id": 4,
            "question": "中国共产党成立于（ ）。",
            "A": "1919 年", "B": "1921 年", "C": "1927 年", "D": "1949 年",
            "answer": "B"
        },
        {
            "id": 5,
            "question": "中国改革开放开始的标志是（ ）。",
            "A": "1976 年粉碎四人帮", "B": "1978 年十一届三中全会",
            "C": "1982 年家庭联产承包责任制", "D": "1992 年邓小平南方谈话",
            "answer": "B"
        },
    ],
    "college_math": [
        {
            "id": 1,
            "question": "极限 lim(x→0) sin(x)/x =（ ）。",
            "A": "0", "B": "1", "C": "∞", "D": "不存在",
            "answer": "B"
        },
        {
            "id": 2,
            "question": "函数 f(x) = x² 在 x=1 处的导数是（ ）。",
            "A": "0", "B": "1", "C": "2", "D": "3",
            "answer": "C"
        },
        {
            "id": 3,
            "question": "∫₀¹ 2x dx =（ ）。",
            "A": "0", "B": "1", "C": "2", "D": "1/2",
            "answer": "B"
        },
        {
            "id": 4,
            "question": "矩阵 A = [[1,2],[3,4]] 的行列式值是（ ）。",
            "A": "-2", "B": "0", "C": "2", "D": "10",
            "answer": "A"
        },
        {
            "id": 5,
            "question": "级数 Σ(1/n²) (n=1→∞) 收敛于（ ）。",
            "A": "1", "B": "π/6", "C": "π²/6", "D": "∞",
            "answer": "C"
        },
    ],
}


def build_prompt(question: Dict, n_shot: int = 0, examples: List[Dict] = None) -> str:
    """构建 few-shot prompt"""
    prompt = "以下是单项选择题，请只输出答案字母（A/B/C/D）。\n\n"
    if n_shot > 0 and examples:
        for ex in examples[:n_shot]:
            prompt += f"题目：{ex['question']}\nA. {ex['A']}\nB. {ex['B']}\nC. {ex['C']}\nD. {ex['D']}\n答案：{ex['answer']}\n\n"
    prompt += f"题目：{question['question']}\nA. {question['A']}\nB. {question['B']}\nC. {question['C']}\nD. {question['D']}\n答案："
    return prompt


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
        "temperature": 0,
        "max_completion_tokens": 50,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def extract_answer(text: str) -> str:
    """从 LLM 输出中提取选项字母"""
    text = text.strip().upper()
    # 优先匹配第一个出现的 A/B/C/D
    match = re.search(r"[ABCD]", text)
    if match:
        return match.group()
    return text[0] if text else ""


def evaluate_subject(subject: str, questions: List[Dict], model: str, n_shot: int) -> Dict:
    """评测单个学科"""
    correct = 0
    total = len(questions)
    results = []

    # few-shot 示例从学科内前 n_shot 题取
    examples = questions[:n_shot] if n_shot > 0 else []

    for q in questions:
        prompt = build_prompt(q, n_shot=n_shot, examples=examples)
        try:
            output = call_llm(prompt, model)
            predicted = extract_answer(output)
            is_correct = predicted == q["answer"]
        except Exception as e:
            output = f"ERROR: {e}"
            predicted = ""
            is_correct = False

        if is_correct:
            correct += 1
        results.append({
            "id": q["id"],
            "question": q["question"],
            "correct_answer": q["answer"],
            "predicted": predicted,
            "raw_output": output,
            "is_correct": is_correct,
        })
        time.sleep(0.5)  # 避免 rate limit

    accuracy = correct / total if total > 0 else 0
    return {
        "subject": subject,
        "subject_zh": CEVAL_SUBJECTS.get(subject, subject),
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "details": results,
    }


def main():
    parser = argparse.ArgumentParser(description="C-Eval 评测脚本")
    parser.add_argument("--model", type=str, default=OPENAI_MODEL,
                        help=f"模型名称（默认：{OPENAI_MODEL}）")
    parser.add_argument("--n_shot", type=int, default=5,
                        help="few-shot 数量（0=zero-shot, 5=five-shot，默认 5）")
    parser.add_argument("--subjects", type=str, nargs="+", default=None,
                        help="指定学科（默认全部 6 个）")
    parser.add_argument("--output", type=str, default=None,
                        help="结果输出路径")
    args = parser.parse_args()

    subjects = args.subjects if args.subjects else list(CEVAL_SUBJECTS.keys())
    print(f"=" * 60)
    print(f"C-Eval 评测 | model={args.model} | n_shot={args.n_shot}")
    print(f"=" * 60)

    all_results = []
    for subject in subjects:
        if subject not in CEVAL_QUESTIONS:
            print(f"⚠️ 未知学科: {subject}，跳过")
            continue
        questions = CEVAL_QUESTIONS[subject]
        print(f"\n📚 评测学科: {CEVAL_SUBJECTS[subject]} ({len(questions)} 题)...")
        result = evaluate_subject(subject, questions, args.model, args.n_shot)
        all_results.append(result)
        print(f"  ✅ {CEVAL_SUBJECTS[subject]}: {result['correct']}/{result['total']} = {result['accuracy']*100:.1f}%")

    # 汇总
    total_correct = sum(r["correct"] for r in all_results)
    total_questions = sum(r["total"] for r in all_results)
    avg_accuracy = total_correct / total_questions if total_questions > 0 else 0

    summary = {
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": args.model,
        "n_shot": args.n_shot,
        "subjects": subjects,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "avg_accuracy": round(avg_accuracy, 4),
        "per_subject": all_results,
    }

    # 输出
    print(f"\n{'=' * 60}")
    print(f"📊 汇总")
    print(f"{'=' * 60}")
    print(f"模型: {args.model} | n_shot: {args.n_shot}")
    print(f"总题数: {total_questions} | 总正确: {total_correct}")
    print(f"平均准确率: {avg_accuracy*100:.1f}%")
    print(f"\n各学科:")
    for r in all_results:
        print(f"  {r['subject_zh']:<25} {r['correct']}/{r['total']} = {r['accuracy']*100:.1f}%")

    # 写文件
    if args.output:
        out_path = args.output
    else:
        n_shot_tag = f"{args.n_shot}shot"
        out_path = f"model_eval/ceval_results/{args.model.replace('/', '_')}_{n_shot_tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存: {out_path}")


if __name__ == "__main__":
    main()
