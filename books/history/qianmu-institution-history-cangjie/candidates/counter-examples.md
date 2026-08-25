# Counter-Example Extractor 产出 — 《中国历代政治得失》

```yaml
- id: x01
  title: 九品中正制的异化
  type: counter-example
  source_chapter: 汉代篇·选举制度综论
  source_quote: |
    "九品中正制，本想替当时用人定出一客观标准，还是不失此项制度所应有的传统精神的。但后来却变成拥护门第，把觅取人才的标准，无形中限制在门第的小范围内。"
  failure_mechanism: |
    救弊之制→依赖执行者（中正官）个人判断→无外部校准机制→
    执行者利益与制度初衷背离→制度被俘获为门第护符。
    识别信号：一项依赖「人的自觉」而无问责结构的制度。

- id: x02
  title: 八股取士的斲丧人才
  type: counter-example
  source_chapter: 明代篇·考试制度
  source_quote: |
    "八股文考试真是中国历史上最斲丧人才的。……然而明代推行八股文，早已在衰世。那时的皇帝，哪里会用心"
  failure_mechanism: |
    考试内容僵化为固定格式→筛选的是格式熟练度而非治理能力→
    人才结构单一化→帝国晚期无人可用。
    注意钱穆的辩护角度：八股初行非愚民设计，是衰世无力改革的将就。

- id: x03
  title: 清代部族政权的法术统治
  type: counter-example
  source_chapter: 清代篇
  source_quote: |
    "只有清代才不许人讲话。这成什么制度呢？这只是满洲部族政权便利他们统治中国的一些无理的法术。"
  failure_mechanism: |
    部族政权以私心治国→制度沦为法术（私下操纵的手段）→
    压制言论、废除廷议传统→政治失去纠错能力。
    钱穆批评最烈的朝代；注意此论在清史学界争议极大（新清史等）。

- id: x04
  title: 一条鞭法的南北失调
  type: counter-example
  source_chapter: 明代篇·赋税制度
  source_quote: |
    "但此制也如宋代的免役法一样，虽在南方觉得是便利，但在北方则各处深感不便，反对甚烈。实际上，一条鞭法经历时期也并不久，便紊乱了。"
  failure_mechanism: |
    在南方经济条件下设计的税制→强行推广到北方→
    货币化纳税对商品经济落后地区是灾难→制度紊乱。
    识别信号：忽视地域差异的一刀切改革。

- id: x05
  title: 府兵逃亡规避
  type: counter-example
  source_chapter: 唐代篇·兵役制度
  source_quote: |
    "下次遇到上番值宿，便多逃亡规避。"
  failure_mechanism: |
    兵士地位下降（等同苦工贱视）→荣誉感消失→
    逃亡成为理性选择→兵源枯竭→府兵制崩溃。
    与c04对照：同一制度的兴衰两面。
```
