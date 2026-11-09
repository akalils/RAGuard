# 目录和运行说明

## 文件放在哪里

| 目录 | 内容 |
| --- | --- |
| `raguard/` | RAG 核心、配置、知识检索封装和 FastAPI 服务 |
| `evaluation/` | RAG 评测、报告生成和模型基座评测脚本 |
| `tests/` | DeepEval、RAGAS 评测测试入口，会调用模型 |
| `data/documents/` | 原始法律文档和 `urls.txt` |
| `data/datasets/` | 评测数据集 |
| `data/chroma_db/` | 已有向量库，本地保存 |
| `reports/` | Markdown 报告、评测历史数据库和模型评测结果 |
| `notebooks/` | Jupyter 学习笔记 |
| `docs/` | 操作说明、目录迁移对照和面试笔记 |

`.env`、`.env.example`、依赖清单、README、GitHub 工作流和客户端配置仍放在项目根目录或各自规定的隐藏目录。

`raguard/config.py` 统一从项目根目录加载 `.env`，并提供数据集、原始文档、向量库、报告和历史数据库的绝对路径。默认路径不再随终端当前目录变化。命令中主动传入的相对路径仍按终端当前目录解释。

## 常用命令

在项目根目录执行；`python` 使用原来已安装依赖的环境。

```bash
# RAG 交互式问答
python -m raguard.rag_pipeline

# FastAPI
python -m uvicorn raguard.api:app --host 127.0.0.1 --port 8000

# RAG 评测与报告生成（会调用模型并写入 reports/）
python -m evaluation.generate_report

# 评测测试（会调用模型）
python -m pytest tests/test_rag_batch.py
python -m pytest tests/test_rag_ragas.py

# 基座模型评测
python evaluation/model_eval/run_ceval.py --help
python evaluation/model_eval/run_mtbench.py --help
```

MCP 练习、演示服务和探针在旁边的 `../mcp-lab`，说明见该项目的 `docs/MCP_LAB.md`。本仓库的 `.cursor/mcp.json` 和 `.codex/config.toml` 只保留知识检索服务的客户端路径。Notebook 在项目根目录或 `notebooks/` 下打开，先运行新增的项目路径初始化单元格。

## 整理后的路径

| 旧位置 | 新位置 |
| --- | --- |
| `config.py` | `raguard/config.py` |
| `rag_pipeline.py` | `raguard/rag_pipeline.py` |
| `api.py` | `raguard/api.py` |
| `knowledge_service.py` | `raguard/knowledge_service.py` |
| `mcp_server.py` 及 MCP 演示、探针 | 旁边的 `../mcp-lab` |
| `generate_report.py`、`ragas_eval.py`、`smoke_ragas.py` | `evaluation/` 内同名文件 |
| `model_eval/` 脚本与说明 | `evaluation/model_eval/` |
| `model_eval/*_results/` | `reports/model_eval/*_results/` |
| `test_rag_batch.py`、`test_rag_ragas.py` | `tests/` 内同名文件 |
| `document/` | `data/documents/` |
| `eval_dataset.yaml` | `data/datasets/eval_dataset.yaml` |
| `chroma_db/` | `data/chroma_db/` |
| `eval_report.md`、`eval_history.db` | `reports/` 内同名文件 |
| `study_deepeval.ipynb` | `notebooks/study_deepeval.ipynb` |
| `INTERVIEW.md` | `docs/INTERVIEW.md` |

原始文档、向量库、数据集、已有报告和历史数据库按原内容迁移。已有评测报告与模型结果中的历史描述不作改写。
