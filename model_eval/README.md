# RAGuard · 大模型基座评测

针对大语言模型基座（base model）的能力评测，覆盖**知识广度**（C-Eval）和**多轮对话质量**（MT-Bench）两个核心维度。

## 评测框架

| 框架 | 评测目标 | 评测方式 | 工具 |
|------|----------|----------|------|
| [C-Eval](https://cevalbenchmark.com/) | 中文基础学科知识 | 选择题，few-shot 准确率 | `run_ceval.py` |
| [MT-Bench](https://arxiv.org/abs/2306.05685) | 多轮对话质量 | LLM-as-Judge，1-10 分 | `run_mtbench.py` |

---

## 1. C-Eval · 中文基座评测

### 覆盖学科

| 学科 | 类别 | 题目数 | 评测目的 |
|------|------|--------|----------|
| 计算机网络 | STEM | 5 | 计算机基础能力 |
| 计算机组成 | STEM | 5 | 计算机基础能力 |
| 操作系统 | STEM | 5 | 计算机基础能力 |
| 马克思主义基本原理 | Social Science | 5 | 中文人文社科理解力 |
| 中国近现代史 | Humanities | 5 | 中文人文历史理解力 |
| 高等数学 | STEM | 5 | 数学推理能力 |

### 使用方法

```bash
# 默认（5-shot，6 个学科）
python model_eval/run_ceval.py

# 指定模型 + zero-shot
python model_eval/run_ceval.py --model gpt-5.4-nano --n_shot 0

# 只评测 3 个学科
python model_eval/run_ceval.py --subjects computer_network operating_system college_math

# 评测 DeepSeek
python model_eval/run_ceval.py --model deepseek-chat
```

### 关键概念：Few-shot vs Zero-shot

| 模式 | Prompt | 适用场景 |
|------|--------|----------|
| **Zero-shot** | 直接问，模型自己答 | 测试模型的零样本能力 |
| **Few-shot (5-shot)** | 先给 5 个示例，再问 | 测试模型 in-context learning 能力 |

C-Eval 官方推荐 **5-shot**，因为选择题有固定的答案格式（ABCD），few-shot 能让模型学会输出格式。

### 输出格式

结果保存到 `model_eval/ceval_results/{model}_{n_shot}shot_{timestamp}.json`：

```json
{
  "run_time": "2026-06-04 10:00:00",
  "model": "gpt-5.4-nano",
  "n_shot": 5,
  "total_questions": 30,
  "total_correct": 18,
  "avg_accuracy": 0.6,
  "per_subject": [
    {
      "subject": "computer_network",
      "subject_zh": "计算机网络",
      "total": 5,
      "correct": 4,
      "accuracy": 0.8,
      "details": [...]
    }
  ]
}
```

---

## 2. MT-Bench · 多轮对话评测

### 8 个类别

| 类别 | 中文 | 评测能力 |
|------|------|----------|
| writing | 写作 | 文本生成质量 |
| roleplay | 角色扮演 | 指令遵循 |
| reasoning | 推理 | 逻辑推理 |
| math | 数学 | 数学计算 |
| coding | 编程 | 代码生成 |
| extraction | 信息抽取 | 结构化输出 |
| stem | 科学 | 科学知识 |
| humanities | 人文 | 人文知识 |

### 使用方法

```bash
# 默认评测（target=judge=当前模型）
python model_eval/run_mtbench.py

# 强模型当 judge，弱模型当 target
python model_eval/run_mtbench.py --target gpt-5.4-nano --judge gpt-4o

# 调试：只评测 3 个类别
python model_eval/run_mtbench.py --limit 3
```

### 核心：LLM-as-Judge 评分逻辑

**为什么用 LLM 当 Judge？**
- 传统指标（BLEU、ROUGE）只能比字面相似度，无法评估"回答好不好"
- 人类评分贵且不一致
- 强模型（GPT-4o）评分和人类一致性达到 80%+

**评分 Prompt 设计**（4 个维度）：
1. 准确性：回答是否正确
2. 完整性：是否覆盖要点
3. 连贯性：多轮是否逻辑一致
4. 表达：语言是否清晰

**打分规则**：
- 1-3 分：严重错误或不相关
- 4-6 分：基本正确但有缺漏
- 7-8 分：高质量回答
- 9-10 分：完美回答

**Judge 模型的潜在偏差**（面试加分项）：
- **位置偏差**：倾向给先出现的回答打高分 → 用 pair-wise 比较消除
- **长度偏差**：倾向给长回答打高分 → 在 prompt 中显式说明
- **自我偏好**：GPT-4 倾向给 GPT-4 自己的回答高分

### 输出格式

结果保存到 `model_eval/mtbench_results/{model}_{timestamp}.json`：

```json
{
  "run_time": "2026-06-04 10:00:00",
  "target_model": "gpt-5.4-nano",
  "judge_model": "gpt-4o",
  "overall_avg_score": 7.5,
  "per_category": [
    {
      "category": "coding",
      "category_zh": "编程",
      "turn_scores": [8, 7],
      "avg_score": 7.5,
      "turn_judgments": [
        {
          "turn": 1,
          "question": "...",
          "response": "...",
          "score": 8,
          "judgment": "..."
        }
      ]
    }
  ]
}
```

---

## 3. 面试话术

### C-Eval
> "我跑过 C-Eval，用 5-shot 测了 6 个学科。xx 模型在计算机类目上得分 xx，人文社科类目得分 xx。few-shot 和 zero-shot 的差距反映了模型的 in-context learning 能力。"

### MT-Bench
> "我实现过 MT-Bench 的 LLM-as-Judge 流程：用 GPT-4o 当 judge，给目标模型的多轮对话打 1-10 分。核心是评分 prompt 的设计——4 个维度（准确性/完整性/连贯性/表达）。Judge 模型有 3 个已知偏差：位置偏差、长度偏差、自我偏好。"

---

## 4. 已知限制

| 限制 | 原因 | 解决方案 |
|------|------|----------|
| 题目数量少（每科 5 题） | 本地跑，无完整数据集 | 下载完整 C-Eval 数据集 |
| MT-Bench 只有 8 类 × 2 轮 | 简化版 | 完整版 80 题 × 2 轮 = 160 题 |
| LLM-as-Judge 有偏差 | 强模型自身的偏好 | 用 pair-wise + 多个 judge 取平均 |

---

## 5. 快速开始

```bash
# 1. 评测 C-Eval（约 1 分钟）
python model_eval/run_ceval.py

# 2. 评测 MT-Bench（约 3 分钟）
python model_eval/run_mtbench.py

# 3. 查看结果
ls model_eval/ceval_results/
ls model_eval/mtbench_results/
```
