"""
RAGAS 0.4.3 升级后的冒烟测试 —— 你自己跑
用法：/opt/miniconda3/envs/pytorch/bin/python3 smoke_ragas.py

⚠️ RAGAS 0.4.3 的坑：collections.* 的类不继承 Metric，evaluate() 校验失败。
   必须用旧路径（from ragas.metrics import ...）
"""
import sys, time, warnings
sys.path.insert(0, "/Users/mac/Project/RAGuard")

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        Faithfulness,
        ContextPrecision,
        ContextRecall,
        AnswerRelevancy,
    )
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

print("== 1. 构造 LLM judge ==")
t0 = time.time()
llm = LangchainLLMWrapper(
    ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        temperature=0,
    )
)
print(f"   OK ({time.time()-t0:.1f}s)")

print("== 2. 构造 embeddings（HF 中文模型）==")
t0 = time.time()
emb = LangchainEmbeddingsWrapper(
    HuggingFaceEmbeddings(model_name="shibing624/text2vec-base-chinese")
)
print(f"   OK ({time.time()-t0:.1f}s)")

print("== 3. 构造 4 个 metric（每个都传 llm，AnswerRelevancy 加 embeddings）==")
metrics = [
    Faithfulness(llm=llm),
    ContextPrecision(llm=llm),
    ContextRecall(llm=llm),
    AnswerRelevancy(llm=llm, embeddings=emb),
]
print("   OK | names:", [m.name for m in metrics])

print("== 4. 跑最小 evaluate（1 题）==")
data = {
    "question":     ["试用期最长多久"],
    "answer":       ["根据劳动合同法第十九条，试用期最长不得超过六个月。"],
    "contexts":     [["第十九条 劳动合同期限三个月以上不满一年的，试用期不得超过一个月；一年以上不满三年的不得超过二个月；三年以上固定期限和无固定期限的不得超过六个月。"]],
    "ground_truth": ["三个月以上不满一年不得超过一个月；一年以上不满三年不得超过二个月；三年以上不得超过六个月。"],
}
ds = Dataset.from_dict(data)

t0 = time.time()
res = evaluate(
    dataset=ds,
    metrics=metrics,
    raise_exceptions=False,
)
print(f"   evaluate cost: {time.time()-t0:.1f}s")

df = res.to_pandas()
print("\n== 5. 结果 ==")
print("COLUMNS:", list(df.columns))
print("ROW:", df.iloc[0].to_dict())
