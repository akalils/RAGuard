# RAGuard — RAG应用质量评测框架

基于 DeepEval 的 RAG 应用自动化质量评测框架，覆盖回答相关性、忠实度、检索精度三大维度，一键生成评测报告。

## 它解决什么问题

企业部署 RAG 应用（智能客服、知识库问答）后，缺乏系统化的质量评测手段。
RAGuard 提供标准化的评测流程：输入评测数据集 → 自动调用 RAG 应用 → 多维度评分 → 生成评测报告。

## 评测维度

| 维度 | 指标 | 含义 |
|------|------|------|
| 回答质量 | Answer Relevancy | 回答是否真正回应了问题 |
| 忠实度 | Faithfulness | 回答是否忠实于检索上下文（幻觉检测） |
| 检索精度 | Contextual Precision | 检索结果中相关内容的占比 |

## 技术栈

LangChain / DeepEval / ChromaDB / Pytest / YAML数据驱动

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/akalils/RAGuard.git
cd RAGuard

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 4. 构建向量库
python rag_pipeline.py --build

# 5. 运行评测
deepeval test run test_rag_batch.py

# 6. 生成评测报告
python generate_report.py
