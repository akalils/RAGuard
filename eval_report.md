# RAGuard 评测报告

生成时间：2026-06-01 18:12:01
评测数据集：2 条法律咨询问答
评测框架：DeepEval (3 指标) + RAGAS (4 指标)
通过阈值：0.7

---

## 总体得分

### DeepEval

- **Answer Relevancy 均分**: 0.887
- **Faithfulness 均分**: 1.000
- **Contextual Precision 均分**: 0.250

### RAGAS

- **Faithfulness（忠实度）**: 0.675
- **Context Precision（检索精度）**: 0.000
- **Context Recall（检索召回）**: 0.000
- **Answer Relevancy（回答相关性）**: nan

## DeepEval · 按法律类别分组

### 劳动法

- Answer Relevancy: 0.887
- Faithfulness: 1.000
- Contextual Precision: 0.250


## RAGAS · 按法律类别分组

### 劳动法

- Faithfulness（忠实度）: 0.675
- Context Precision（检索精度）: 0.000
- Context Recall（检索召回）: 0.000
- Answer Relevancy（回答相关性）: nan


## DeepEval · Bad Cases（未达标用例）

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** [劳动法/easy]
  未通过: Contextual Precision
- **试用期的最长时间是多久？...** [劳动法/easy]
  未通过: Contextual Precision

## RAGAS · Bad Cases（任一指标 < 0.7）

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
- **试用期的最长时间是多久？...** [劳动法/easy]
  - Faithfulness（忠实度）: 0.571
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000