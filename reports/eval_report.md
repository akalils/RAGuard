# RAGuard 评测报告

生成时间：2026-09-04 14:48:11
评测数据集：3 条法律咨询问答
评测框架：DeepEval (3) + RAGAS (4) + 检索 (MRR/NDCG)
通过阈值：0.7

## ⚠️ 回归告警

以下指标相比上次评测下降超过 5%：

| 指标 | 上次 | 本次 | 变化 |
|------|------|------|------|
| Faithfulness (RAGAS) | 0.826 | 0.474 | **-0.351** |

---

## 总体得分

### DeepEval

- **Answer Relevancy 均分**: 0.935
- **Faithfulness 均分**: 0.905
- **Contextual Precision 均分**: 0.713

### RAGAS

- **Faithfulness（忠实度）**: 0.474
- **Context Precision（检索精度）**: 0.500
- **Context Recall（检索召回）**: 0.333
- **Answer Relevancy（回答相关性）**: 0.755

### 检索质量

- **MRR 均分**: 0.233
- **NDCG@5 均分**: 0.339

## 按法律类别分组

### 劳动法

**DeepEval:**
- Answer Relevancy: 0.935
- Faithfulness: 0.905
- Contextual Precision: 0.713

**RAGAS:**
- Faithfulness（忠实度）: 0.474
- Context Precision（检索精度）: 0.500
- Context Recall（检索召回）: 0.333
- Answer Relevancy（回答相关性）: 0.755

**检索:**
- MRR: 0.233
- NDCG@5: 0.339

## Bad Cases

### DeepEval 未达标用例

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** [劳动法/easy]
  未通过: Contextual Precision
- **平时加班工资怎么算？周末加班呢？法定节假日呢？...** [劳动法/easy]
  未通过: Contextual Precision

### RAGAS 未达标用例

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** [劳动法/easy]
  - Faithfulness（忠实度）: 0.333
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
- **试用期的最长时间是多久？...** [劳动法/easy]
  - Faithfulness（忠实度）: 0.167
  - Context Recall（检索召回）: 0.000
- **平时加班工资怎么算？周末加班呢？法定节假日呢？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.500
  - Answer Relevancy（回答相关性）: 0.543

### 低检索质量用例（MRR < 0.5）

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** MRR=0.00 NDCG=0.00 (检索到 5 条)
- **试用期的最长时间是多久？...** MRR=0.20 NDCG=0.39 (检索到 5 条)
