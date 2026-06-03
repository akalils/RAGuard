# RAGuard 评测报告

生成时间：2026-06-03 02:50:17
评测数据集：1 条法律咨询问答
评测框架：DeepEval (3 指标) + RAGAS (4 指标)
通过阈值：0.7

---

## 总体得分

### DeepEval

- **Answer Relevancy 均分**: 0.286
- **Faithfulness 均分**: 1.000
- **Contextual Precision 均分**: 0.000

### RAGAS

- **Faithfulness（忠实度）**: 0.000
- **Context Precision（检索精度）**: 0.000
- **Context Recall（检索召回）**: 1.000
- **Answer Relevancy（回答相关性）**: 0.000

## DeepEval · 按法律类别分组

### 劳动法

- Answer Relevancy: 0.286
- Faithfulness: 1.000
- Contextual Precision: 0.000


## RAGAS · 按法律类别分组

### 劳动法

- Faithfulness（忠实度）: 0.000
- Context Precision（检索精度）: 0.000
- Context Recall（检索召回）: 1.000
- Answer Relevancy（回答相关性）: 0.000


## DeepEval · Bad Cases（未达标用例）

- **劳动合同中可以约定违约金吗？什么情况下可以约定？...** [劳动法/hard]
  未通过: Answer Relevancy, Contextual Precision

## RAGAS · Bad Cases（任一指标 < 0.7）

- **劳动合同中可以约定违约金吗？什么情况下可以约定？...** [劳动法/hard]
  - Faithfulness（忠实度）: 0.000
  - Context Precision（检索精度）: 0.000
  - Answer Relevancy（回答相关性）: 0.000