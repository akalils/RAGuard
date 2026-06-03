# 面试话术 — 5 个核心故事点

## 1. 项目背景（1 分钟）

"我搭建了一个 RAG 质量评测框架 RAGuard，给法律领域 RAG 应用做自动化质量检测。核心是 7 个评测指标（DeepEval 3 + RAGAS 4），GitHub Actions CI 自动跑评测，每次 push 或 PR 都会生成评测报告。"

**关键词**: RAG、评测、自动化、CI/CD、质量保障

---

## 2. 技术选型（2 分钟）

"技术栈选型考虑了三个维度：
- **LLM 评测**: DeepEval 开箱即用，支持 Answer Relevancy、Faithfulness、Contextual Precision
- **RAG 专项评测**: RAGAS 专门针对 RAG 场景，有 Context Recall 和 Context Precision，能区分是检索问题还是生成问题
- **Judge LLM**: 用 Azure OpenAI gpt-5.4-nano 作为评判模型，但 DeepEval 的 GPTModel 有白名单，所以我自己实现了 `AzureJudgeLLM` 继承 `DeepEvalBaseLLM`，用 OpenAI SDK 直接调用"

---

## 3. 踩坑故事（3 分钟，最能体现技术深度）

### 坑 1：RAGAS 0.4.3 API Breakage

"升级到 RAGAS 0.4.x 后，`Faithfulness` 等类从 `ragas.metrics` 移到了 `ragas.metrics.collections`，但新路径的类继承 `BaseMetric` 而非 `Metric`，`evaluate()` 在 `evaluation.py:133` 检查 `isinstance(m, Metric)` 直接抛异常。我通过对比两个版本的源码找到问题，用旧路径导入 + `warnings.catch_warnings()` 抑制 DeprecationWarning 解决。"

**面试官问**: 你怎么发现是继承链的问题？
**答**: 看 `evaluate()` 的报错栈，它在 `evaluation.py:133` 做 `isinstance(m, Metric)` 检查。我去看了新路径的 `BaseMetric` 源码，发现它没有继承 `Metric`，所以不通过检查。

### 坑 2：DeepEval Azure 模型白名单

"DeepEval 1.x 的 `GPTModel` 在 `openai_model.py:165` 硬编码了支持的模型名列表，我的 Azure 部署名 `gpt-5.4-nano` 不在白名单里。我看了 DeepEval 的源码，发现 `DeepEvalBaseLLM` 是公开的抽象基类，直接继承它，用 `openai.AsyncOpenAI` 直接调 Azure API 绕过了限制。"

**面试官问**: 为什么不用 LiteLLM？
**答**: DeepEval 1.0.x 没有 `LiteLLMModel`，要 1.1+ 才有。而且 `DeepEvalBaseLLM` 更简单，直接控制 API 调用。

### 坑 3：`__pycache__` 导致检索空

"本地直接调 `ask()` 返回 5 个文档，但通过 `generate_report.py` 调用就返回空列表。查了 2 小时发现是 `__pycache__` 缓存了旧版 `rag_pipeline.py`，新版的 `ask()` 修改没生效。删除 `__pycache__` + 重建向量库后解决。"

**面试官问**: 怎么排查到是缓存问题？
**答**: 先验证了 `as_retriever().invoke()` 直接调用返回 4 个文档，再看 `ask()` 内部也调了同一个 retriever，但结果不同。怀疑是模块加载问题，清了 `__pycache__` 就好了。

---

## 4. CI/CD 设计（1 分钟）

"GitHub Actions 工作流支持 push / PR / 手动触发 / 每周一定时跑。缓存了 HuggingFace 模型和 ChromaDB 向量库，首次构建后后续跑只要 2 分钟。评测报告自动 commit 到 main 分支，badge 显示最新状态。"

**关键词**: 缓存策略、定时评测、自动提交、badge

---

## 5. 量化成果 + 未来方向（1 分钟）

"当前基线：DeepEval Faithfulness 0.886，Answer Relevancy 0.822；RAGAS Faithfulness 0.754。Context Precision 偏低（0.228），因为检索返回空是已知问题。

下一步计划：
- 换 bge-m3 embedder 提升检索质量
- 加 BM25 混合检索
- Prompt 注入安全测试

这些在 README 里有详细的 roadmap。"

---

## 面试常见追问

**Q: 为什么选 DeepEval + RAGAS 两个框架？**
A: DeepEval 侧重生成质量（回答是否忠实、是否相关），RAGAS 侧重检索质量（检索是否覆盖、是否精准）。两个维度都要看。

**Q: 评测数据集怎么设计的？**
A: 39 条法律问答，3 类别（劳动法/刑法/民法），3 难度（easy/medium/hard），每条有 reference_answer 作为 ground truth。

**Q: 你怎么保证评测结果的可靠性？**
A: Judge LLM 用的 gpt-5.4-nano，temperature=0 保证可复现。评测集有 ground truth。CI 定时跑可以发现回归。

**Q: 这个项目最大的挑战是什么？**
A: 两个框架的 API 不兼容问题。RAGAS 0.4.x 的 breaking change 和 DeepEval 1.x 的白名单都是要读源码才能解决的。
