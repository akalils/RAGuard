# RAGuard — RAG 应用质量评测框架

[![RAG Evaluation](https://github.com/akalils/RAGuard/actions/workflows/rag-eval.yml/badge.svg)](https://github.com/akalils/RAGuard/actions/workflows/rag-eval.yml)

> 自动化 RAG 质量评测：DeepEval 3 指标 + RAGAS 4 指标，GitHub Actions CI，一键生成评测报告。

## 解决什么问题

企业部署 RAG 应用（智能客服、知识库问答、法律咨询）后，缺乏系统化的质量评测手段。RAGuard 提供标准化评测流程：**评测数据集 → 自动调用 RAG → 多维度评分 → 生成报告**，覆盖检索质量和生成质量两个维度。

## 评测维度

| 框架 | 指标 | 含义 | 阈值 |
|------|------|------|------|
| DeepEval | Answer Relevancy | 回答是否回应了问题 | 0.7 |
| DeepEval | Faithfulness | 是否忠实于检索上下文（幻觉检测） | 0.7 |
| DeepEval | Contextual Precision | 检索结果中相关内容的占比 | 0.7 |
| RAGAS | Faithfulness | 回答与检索上下文的一致性 | 0.7 |
| RAGAS | Context Precision | 检索结果中相关内容的排名 | 0.7 |
| RAGAS | Context Recall | 检索是否覆盖了答案所需的信息 | 0.7 |
| RAGAS | Answer Relevancy | 回答与问题的相关性 | 0.7 |

## 技术栈

```
RAG:        LangChain 0.3 + ChromaDB + DashScope Embedding (text2vec-base-chinese)
评测:       DeepEval 1.x (3 指标) + RAGAS 0.4.x (4 指标)
Judge LLM:  Azure OpenAI (gpt-5.4-nano, custom DeepEvalBaseLLM)
CI/CD:      GitHub Actions (push/PR/schedule 触发, 自动生成 eval_report.md)
```

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/akalils/RAGuard.git
cd RAGuard

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 4. 构建向量库（首次运行）
python rag_pipeline.py --build

# 5. 交互式问答
python rag_pipeline.py

# 6. 运行评测
python generate_report.py
```

## 项目结构

```
RAGuard/
├── rag_pipeline.py          # RAG 核心流程（文档加载/分块/检索/生成）
├── config.py                # 环境变量配置
├── api.py                   # FastAPI 接口
├── eval_dataset.yaml        # 评测数据集（39 条法律问答，支持 3 类别 3 难度）
├── generate_report.py       # DeepEval + RAGAS 合并评测 + 报告生成
├── ragas_eval.py            # RAGAS 评测封装
├── test_rag_ragas.py        # RAGAS pytest 入口
├── eval_report.md           # 自动生成的评测报告
├── document/                # 法律文档（劳动法 .docx, 刑法 .docx）
├── chroma_db/               # ChromaDB 向量存储（347 chunks）
└── .github/workflows/
    └── rag-eval.yml         # CI 工作流
```

## CI/CD

GitHub Actions 工作流（`.github/workflows/rag-eval.yml`）：

- **触发**: push / PR / 手动 / 每周一 2:00 定时
- **流程**: 安装依赖 → 加载缓存模型 → 运行评测 → 上传 artifact → 自动提交报告
- **缓存**: HuggingFace 模型 + ChromaDB 向量库
- **产物**: `eval_report.md` + `eval_run.log`（30 天保留）

### 环境变量（GitHub Secrets）

| 变量 | 用途 |
|------|------|
| `OPENAI_API_KEY` | Azure OpenAI API Key |
| `OPENAI_BASE_URL` | Azure OpenAI Endpoint |
| `OPENAI_MODEL` | 部署名称（如 gpt-5.4-nano） |
| `DASHSCOPE_API_KEY` | DashScope Embedding API Key |

## 踩坑记录

### RAGAS 0.4.3 API 不兼容

**问题**: RAGAS 0.4.x 将 `Faithfulness` 等类从 `ragas.metrics` 移到了 `ragas.metrics.collections`，但新路径的类继承 `BaseMetric` 而非 `Metric`，导致 `evaluate()` 抛出 `NotImplementedError`。

**解决**: 用旧路径导入（`from ragas.metrics import ...`）+ `warnings.catch_warnings()` 抑制 DeprecationWarning。

```python
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import (
        Faithfulness,
        LLMContextPrecisionWithoutReference,
        AnswerRelevancy,
    )
```

### DeepEval Azure 模型白名单

**问题**: DeepEval 1.x 的 `GPTModel` 硬编码检查 `model_name` 是否在支持列表中，不识别 Azure 部署名称（如 `gpt-5.4-nano`）。

**解决**: 继承 `DeepEvalBaseLLM`，用 `openai.AsyncOpenAI` 直接调用 Azure API。

```python
class AzureJudgeLLM(DeepEvalBaseLLM):
    def __init__(self):
        self._client = AsyncOpenAI(api_key=..., base_url=...)
        self._model = OPENAI_MODEL

    def generate(self, prompt, schema=None):
        if schema is None:
            return self._client.chat.completions.create(...)
        return self._client.beta.chat.completions.parse(response_format=schema, ...)
```

### ChromaDB 版本兼容

**问题**: `chromadb>=0.6` 的内部 API 变更导致 `langchain-chroma` 报错。

**解决**: `chromadb>=0.5,<0.6`。

### HuggingFace SSL 错误

**问题**: `load_vector_store()` 调用 `HuggingFaceEmbeddings` 时，HTTPS 请求被代理/VPN 拦截，导致 `[SSL: UNEXPECTED_EOF_WHILE_READING]`。

**解决**: 设置 `HF_HUB_OFFLINE=1` 环境变量（模型已缓存，不需要联网）。

### Azure Content Filter

**问题**: "醉酒的人犯罪需要负刑事责任吗？"触发 Azure OpenAI 内容过滤（`ContentFilterFinishReasonError`）。

**解决**: 从评测数据集中注释掉该问题。

### `__pycache__` 缓存问题

**问题**: `generate_report.py` 调用 `ask()` 时返回空检索结果，但直接调用 `ask()` 正常。

**解决**: 删除 `__pycache__/` 目录 + 重建 `chroma_db`。根因是旧版 `rag_pipeline.py` 的 `ask()` 函数被缓存，新版修改未生效。

## 已知问题

| 问题 | 影响 | 临时方案 |
|------|------|---------|
| `retrieval_context` 在评测中为空 | Context Precision 和 Recall 偏低 | 需排查 `generate_report.py` 中 `ask()` 调用链 |
| RAGAS 部分题超时 | 个别题无 RAGAS 分数 | 增加超时时间或减少并发 |
| 刑法类别题目尚未补充 | 只有劳动法类别有评测数据 | 后续扩展 eval_dataset.yaml |

## Future Work

- [ ] **换 embedder**: 从 DashScope text2vec 切换到 bge-m3（多语言法律领域 SOTA）
- [ ] **BM25 混合检索**: 结合关键词检索 + 语义检索，提升法律条文匹配精度
- [ ] **Prompt 注入安全测试**: 测试恶意 prompt 是否能绕过 RAG 限制
- [ ] **A/B 评测**: 对比不同分块策略 / Prompt 模板的效果
- [ ] **评测结果持久化**: SQLite 存储历史评测结果，支持趋势分析
- [ ] **Web 看板**: Streamlit 可视化评测报告

## JD 技能映射

| JD 要求 | 本项目实现 |
|---------|-----------|
| 编写评测数据集 / 标注 | `eval_dataset.yaml`：39 条法律问答，3 类别 3 难度 |
| 自动化测试框架搭建 | `generate_report.py`：DeepEval + RAGAS 7 指标自动评测 |
| CI/CD 工具链实践 | GitHub Actions：push/PR 触发，缓存模型，自动提交报告 |
| LLM 模型评测 | Azure OpenAI Judge + HF Embedding 本地评测 |
| 编写技术文档 | 本 README + 踩坑记录 + 面试话术 |
| **大模型能力测评** | **`model_eval/`：C-Eval 6 学科 + MT-Bench 8 类别多轮对话评测 + LLM-as-Judge** |

---

## 大模型基座评测

RAGuard 不只评测 RAG 应用，还提供大模型基座能力评测，覆盖**知识广度**和**多轮对话质量**两个核心维度。

### C-Eval · 中文基座评测

| 学科 | 类别 | 题目数 |
|------|------|--------|
| 计算机网络 / 计算机组成 / 操作系统 | STEM | 5 × 3 |
| 马克思主义基本原理 | Social Science | 5 |
| 中国近现代史 | Humanities | 5 |
| 高等数学 | STEM | 5 |

```bash
python model_eval/run_ceval.py --model gpt-5.4-nano --n_shot 5
```

### MT-Bench · 多轮对话评测（LLM-as-Judge）

8 个类别（写作/角色扮演/推理/数学/编程/信息抽取/科学/人文），每类 2 轮对话，用强模型（GPT-4o）当 Judge 打 1-10 分。

```bash
python model_eval/run_mtbench.py --target gpt-5.4-nano --judge gpt-4o
```

**核心能力**：
- LLM-as-Judge 评分 Prompt 设计（4 维度：准确性/完整性/连贯性/表达）
- 理解 Judge 模型的 3 个偏差（位置/长度/自我偏好）

详见 [`model_eval/README.md`](model_eval/README.md)。
