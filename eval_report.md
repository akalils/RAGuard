# RAGuard 评测报告

生成时间：2026-06-04 06:28:00
评测数据集：10 条法律咨询问答
评测框架：DeepEval (3) + RAGAS (4) + 检索 (MRR/NDCG)
通过阈值：0.7

---

## 总体得分

### DeepEval

- **Answer Relevancy 均分**: 0.433
- **Faithfulness 均分**: 1.000
- **Contextual Precision 均分**: 0.000

### RAGAS

- **Faithfulness（忠实度）**: nan
- **Context Precision（检索精度）**: 0.000
- **Context Recall（检索召回）**: 0.389
- **Answer Relevancy（回答相关性）**: 0.075

### 检索质量

- **MRR 均分**: 0.000
- **NDCG@5 均分**: 0.000

## 按法律类别分组

### 劳动法

**DeepEval:**
- Answer Relevancy: 0.433
- Faithfulness: 1.000
- Contextual Precision: 0.000

**RAGAS:**
- Faithfulness（忠实度）: nan
- Context Precision（检索精度）: 0.000
- Context Recall（检索召回）: nan
- Answer Relevancy（回答相关性）: 0.075

**检索:**
- MRR: 0.000
- NDCG@5: 0.000

## Bad Cases

### DeepEval 未达标用例

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** [劳动法/easy]
  未通过: Answer Relevancy, Contextual Precision
- **试用期的最长时间是多久？...** [劳动法/easy]
  未通过: Answer Relevancy, Contextual Precision
- **平时加班工资怎么算？周末加班呢？法定节假日呢？...** [劳动法/easy]
  未通过: Answer Relevancy, Contextual Precision
- **什么情况下劳动者可以要求签订无固定期限劳动合同？...** [劳动法/medium]
  未通过: Contextual Precision
- **用人单位可以单方面解除劳动合同的情形有哪些？...** [劳动法/medium]
  未通过: Contextual Precision
- **劳动者想辞职，需要提前多久通知用人单位？...** [劳动法/easy]
  未通过: Answer Relevancy, Contextual Precision
- **竞业限制的期限最长是多久？竞业限制期间用人单位需要支付补偿吗？...** [劳动法/medium]
  未通过: Answer Relevancy, Contextual Precision
- **用人单位拖欠工资，劳动者可以怎么办？...** [劳动法/easy]
  未通过: Answer Relevancy, Contextual Precision
- **经济补偿金的计算标准是什么？...** [劳动法/medium]
  未通过: Answer Relevancy, Contextual Precision
- **女职工在孕期、产期、哺乳期内，用人单位可以解除劳动合同吗？...** [劳动法/medium]
  未通过: Answer Relevancy, Contextual Precision

### RAGAS 未达标用例

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **试用期的最长时间是多久？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.500
  - Answer Relevancy（回答相关性）: 0.000
- **平时加班工资怎么算？周末加班呢？法定节假日呢？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
- **什么情况下劳动者可以要求签订无固定期限劳动合同？...** [劳动法/medium]
  - Context Precision（检索精度）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **用人单位可以单方面解除劳动合同的情形有哪些？...** [劳动法/medium]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **劳动者想辞职，需要提前多久通知用人单位？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **竞业限制的期限最长是多久？竞业限制期间用人单位需要支付补偿吗？...** [劳动法/medium]
  - Context Precision（检索精度）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **用人单位拖欠工资，劳动者可以怎么办？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **经济补偿金的计算标准是什么？...** [劳动法/medium]
  - Context Precision（检索精度）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **女职工在孕期、产期、哺乳期内，用人单位可以解除劳动合同吗？...** [劳动法/medium]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000

### 低检索质量用例（MRR < 0.5）

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **试用期的最长时间是多久？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **平时加班工资怎么算？周末加班呢？法定节假日呢？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **什么情况下劳动者可以要求签订无固定期限劳动合同？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **用人单位可以单方面解除劳动合同的情形有哪些？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **劳动者想辞职，需要提前多久通知用人单位？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **竞业限制的期限最长是多久？竞业限制期间用人单位需要支付补偿吗？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **用人单位拖欠工资，劳动者可以怎么办？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **经济补偿金的计算标准是什么？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
- **女职工在孕期、产期、哺乳期内，用人单位可以解除劳动合同吗？...** MRR=0.00 NDCG=0.00 (检索到 0 条)
