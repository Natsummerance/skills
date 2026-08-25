# Counter-Example Extractor 产出 — 《存在主义是一种人道主义》

```yaml
- id: x01
  title: 决定论开脱
  type: counter-example
  source_chapter: 正文§5
  source_quote: |
    "人们喜欢的是，一个人天生就是懦夫或者英雄。……如果你天生是个懦夫，你[就]可以心安理得地做个懦夫。"
  failure_mechanism: |
    宣称「我天生如此」→把选择伪装成命运→心安理得不行动→
    实际上是选择了不做懦夫所做的事。
    当代对应: 基因决定论/性格测试标签的滥用。
  tags: [counter-example, determinism, cowardice]

- id: x02
  title: 伪必然性
  type: counter-example
  source_chapter: 正文§5
  source_quote: |
    "如果我宣称某些价值是我非接受不可的，这也是自我欺骗；我自愿挑上这些价值，同时说这些价值是逼着我接受的，这不是自相矛盾吗？"
  failure_mechanism: |
    把自己选择的价值说成不可拒绝的义务→
    用「不得不」掩盖「我选的」→逃避改变的责任。
  tags: [counter-example, false-necessity, values]

- id: x03
  title: 千年王国先知
  type: counter-example
  source_chapter: 正文§62（政治演讲）
  source_quote: |
    "我还不能看清暴力与兄弟关系这两者的关系。"（附录《什么是主体性？》访谈）
  failure_mechanism: |
    心志伦理者宣称目的圣洁化手段→「最后一次暴力」→
    暴力永无最后。机制：把手段的道德成本转嫁给未来乌托邦。
  tags: [counter-example, utopia, violence]

- id: x04
  title: 讲台布道
  type: counter-example
  source_chapter: 正文§22（学术演讲）
  source_quote: |
    "我们必须看出人们是否确实生活在民主政治之中，是否确实民主地生活着。"（附录《什么是主体性？》——原引文属韦伯《学术演讲》，此处改为萨特的介入性自省）
  failure_mechanism: |
    利用讲台的不可反驳性（学生无法当场质疑）灌输立场→
    以学术权威包装价值判断→剥夺听众的自由选择。
  tags: [counter-example, classroom, authority]
```
