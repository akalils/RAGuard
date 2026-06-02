# RAGuard 评测报告

生成时间：2026-06-02 17:18:45
评测数据集：39 条法律咨询问答
评测框架：DeepEval (3 指标) + RAGAS (4 指标)
通过阈值：0.7

---

## 总体得分

### DeepEval

- **Answer Relevancy 均分**: 0.749
- **Faithfulness 均分**: 0.956
- **Contextual Precision 均分**: 0.398

### RAGAS

- **Faithfulness（忠实度）**: 0.725
- **Context Precision（检索精度）**: 0.268
- **Context Recall（检索召回）**: 0.341
- **Answer Relevancy（回答相关性）**: 0.465

## DeepEval · 按法律类别分组

### 劳动法

- Answer Relevancy: 0.800
- Faithfulness: 0.951
- Contextual Precision: 0.434

### 刑法

- Answer Relevancy: 0.689
- Faithfulness: 0.963
- Contextual Precision: 0.357


## RAGAS · 按法律类别分组

### 劳动法

- Faithfulness（忠实度）: 0.701
- Context Precision（检索精度）: nan
- Context Recall（检索召回）: 0.158
- Answer Relevancy（回答相关性）: 0.381

### 刑法

- Faithfulness（忠实度）: 0.753
- Context Precision（检索精度）: nan
- Context Recall（检索召回）: 0.554
- Answer Relevancy（回答相关性）: nan


## DeepEval · Bad Cases（未达标用例）

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** [劳动法/easy]
  未通过: Contextual Precision
- **试用期的最长时间是多久？...** [劳动法/easy]
  未通过: Contextual Precision
- **平时加班工资怎么算？周末加班呢？法定节假日呢？...** [劳动法/easy]
  未通过: Contextual Precision
- **什么情况下劳动者可以要求签订无固定期限劳动合同？...** [劳动法/medium]
  未通过: Answer Relevancy, Contextual Precision
- **用人单位可以单方面解除劳动合同的情形有哪些？...** [劳动法/medium]
  未通过: Contextual Precision
- **劳动者想辞职，需要提前多久通知用人单位？...** [劳动法/easy]
  未通过: Contextual Precision
- **竞业限制的期限最长是多久？竞业限制期间用人单位需要支付补偿吗？...** [劳动法/medium]
  未通过: Contextual Precision
- **经济补偿金的计算标准是什么？...** [劳动法/medium]
  未通过: Contextual Precision
- **用人单位未依法为劳动者缴纳社会保险费，劳动者可以解除劳动合同并要求经济补偿吗？...** [劳动法/medium]
  未通过: Answer Relevancy, Contextual Precision
- **年休假的天数怎么确定？哪些情形不能享受年休假？...** [劳动法/medium]
  未通过: Contextual Precision
- **用人单位裁员需要满足什么条件？程序是什么？...** [劳动法/hard]
  未通过: Answer Relevancy, Contextual Precision
- **什么是正当防卫？正当防卫需要承担刑事责任吗？...** [刑法/easy]
  未通过: Contextual Precision
- **自首的认定条件是什么？自首可以从轻处罚吗？...** [刑法/easy]
  未通过: Contextual Precision
- **什么是累犯？累犯会有什么法律后果？...** [刑法/medium]
  未通过: Contextual Precision
- **盗窃罪的入罪标准是什么？量刑怎么分档？...** [刑法/medium]
  未通过: Answer Relevancy, Contextual Precision
- **诈骗罪和盗窃罪的核心区别是什么？...** [刑法/hard]
  未通过: Answer Relevancy
- **抢劫罪和抢夺罪有什么区别？...** [刑法/medium]
  未通过: Contextual Precision
- **故意伤害罪的量刑标准是什么？...** [刑法/easy]
  未通过: Answer Relevancy
- **危险驾驶罪包括哪些行为？最高判多久？...** [刑法/easy]
  未通过: Contextual Precision
- **受贿罪和非国家工作人员受贿罪的区别是什么？...** [刑法/hard]
  未通过: Answer Relevancy, Contextual Precision
- **非法拘禁罪的构成要件是什么？量刑标准是什么？...** [刑法/medium]
  未通过: Answer Relevancy, Contextual Precision
- **什么是紧急避险？紧急避险造成损害需要担责吗？...** [刑法/medium]
  未通过: Contextual Precision
- **犯罪未遂和犯罪中止有什么区别？...** [刑法/medium]
  未通过: Contextual Precision
- **未成年人犯罪是否一律从轻处罚？...** [刑法/easy]
  未通过: Contextual Precision
- **用人单位可以扣押劳动者的身份证吗？...** [劳动法/easy]
  未通过: Contextual Precision
- **试用期工资最低标准是什么？...** [劳动法/easy]
  未通过: Contextual Precision
- **员工在工作中造成损失，用人单位可以扣工资吗？有限额吗？...** [劳动法/medium]
  未通过: Answer Relevancy, Contextual Precision
- **什么是寻衅滋事罪？包括哪些行为？...** [刑法/medium]
  未通过: Answer Relevancy, Contextual Precision
- **醉酒的人犯罪需要负刑事责任吗？...** [刑法/easy]
  未通过: Answer Relevancy, Contextual Precision

## RAGAS · Bad Cases（任一指标 < 0.7）

- **劳动合同期满，用人单位不续签，需要支付经济补偿金吗？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **试用期的最长时间是多久？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
- **平时加班工资怎么算？周末加班呢？法定节假日呢？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.500
- **什么情况下劳动者可以要求签订无固定期限劳动合同？...** [劳动法/medium]
  - Context Precision（检索精度）: 0.500
  - Context Recall（检索召回）: 0.250
- **用人单位可以单方面解除劳动合同的情形有哪些？...** [劳动法/medium]
  - Context Recall（检索召回）: 0.571
- **劳动者想辞职，需要提前多久通知用人单位？...** [劳动法/easy]
  - Context Recall（检索召回）: 0.500
- **竞业限制的期限最长是多久？竞业限制期间用人单位需要支付补偿吗？...** [劳动法/medium]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **用人单位拖欠工资，劳动者可以怎么办？...** [劳动法/easy]
  - Faithfulness（忠实度）: 0.577
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.642
- **经济补偿金的计算标准是什么？...** [劳动法/medium]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **女职工在孕期、产期、哺乳期内，用人单位可以解除劳动合同吗？...** [劳动法/medium]
  - Faithfulness（忠实度）: 0.594
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
- **劳务派遣的用工比例有什么限制？...** [劳动法/hard]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **用人单位未依法为劳动者缴纳社会保险费，劳动者可以解除劳动合同并要求经济补偿吗？...** [劳动法/medium]
  - Faithfulness（忠实度）: 0.576
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **工伤认定的一般条件是什么？...** [劳动法/hard]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **年休假的天数怎么确定？哪些情形不能享受年休假？...** [劳动法/medium]
  - Faithfulness（忠实度）: 0.625
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **用人单位裁员需要满足什么条件？程序是什么？...** [劳动法/hard]
  - Context Precision（检索精度）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **什么是累犯？累犯会有什么法律后果？...** [刑法/medium]
  - Context Recall（检索召回）: 0.667
- **盗窃罪的入罪标准是什么？量刑怎么分档？...** [刑法/medium]
  - Context Precision（检索精度）: 0.500
- **诈骗罪和盗窃罪的核心区别是什么？...** [刑法/hard]
  - Faithfulness（忠实度）: 0.455
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **抢劫罪和抢夺罪有什么区别？...** [刑法/medium]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.500
- **故意伤害罪的量刑标准是什么？...** [刑法/easy]
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.637
- **交通肇事罪怎么认定？量刑标准是什么？...** [刑法/medium]
  - Context Precision（检索精度）: 0.250
- **危险驾驶罪包括哪些行为？最高判多久？...** [刑法/easy]
  - Faithfulness（忠实度）: 0.583
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **贪污罪的立案标准和量刑是什么？...** [刑法/medium]
  - Context Recall（检索召回）: 0.500
- **受贿罪和非国家工作人员受贿罪的区别是什么？...** [刑法/hard]
  - Faithfulness（忠实度）: 0.512
  - Context Recall（检索召回）: 0.333
  - Answer Relevancy（回答相关性）: 0.000
- **非法拘禁罪的构成要件是什么？量刑标准是什么？...** [刑法/medium]
  - Faithfulness（忠实度）: 0.654
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **什么是紧急避险？紧急避险造成损害需要担责吗？...** [刑法/medium]
  - Faithfulness（忠实度）: 0.538
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **未成年人犯罪是否一律从轻处罚？...** [刑法/easy]
  - Context Precision（检索精度）: 0.333
  - Context Recall（检索召回）: 0.667
- **用人单位可以扣押劳动者的身份证吗？...** [劳动法/easy]
  - Faithfulness（忠实度）: 0.200
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **试用期工资最低标准是什么？...** [劳动法/easy]
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000
- **员工在工作中造成损失，用人单位可以扣工资吗？有限额吗？...** [劳动法/medium]
  - Faithfulness（忠实度）: 0.556
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
- **公司违法解除劳动合同，劳动者可以要求什么赔偿？...** [劳动法/medium]
  - Faithfulness（忠实度）: 0.622
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
- **劳动争议的仲裁时效是多久？...** [劳动法/hard]
  - Faithfulness（忠实度）: 0.556
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
- **醉酒的人犯罪需要负刑事责任吗？...** [刑法/easy]
  - Context Recall（检索召回）: 0.500
- **劳动合同中可以约定违约金吗？什么情况下可以约定？...** [劳动法/hard]
  - Faithfulness（忠实度）: 0.561
  - Context Precision（检索精度）: 0.000
  - Context Recall（检索召回）: 0.000
  - Answer Relevancy（回答相关性）: 0.000