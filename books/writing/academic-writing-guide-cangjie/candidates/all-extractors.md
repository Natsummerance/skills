# 五路 Extractor 合并产出 — 《学术写作指南》

## frameworks

```yaml
- id: f01
  title: 文献梳理器框架
  type: framework
  source_chapter: 文献综述章
  source_quote: |
    "被文献牵着鼻子走，文献说什么就写什么……读到'孟子云'的时候，就会想'孟子是同意还是不同意孔子说的呢'，但没有找到解释……这就是把梳理文献的工作丢给了读者，这样做是非常不负责任的。"
  summary: |
    综述的本质是梳理而非罗列。梳理四问：
    ①这些文献之间是什么关系（支持/反对/互补/延续）？
    ②分歧点在哪？③共识地基是什么？④缺口在哪里？
    「孔子云孟子云孙子云」式罗列=把综合工作甩锅给读者。
  tags: [literature-review, synthesis, method]

- id: f02
  title: 摘要六句结构法
  type: framework
  source_chapter: 摘要章
  source_quote: |
    "第二、三句话介绍了研究方法；第四、五句话介绍了主要的结果；第六句话概括了结论。这就是比较经典的摘要写法。"
  summary: |
    经典摘要模板：①问题(1句)②方法(2-3句)③结果(4-5句)
    ④结论(6句)。附加纪律：题目关键词须在摘要首句呼应——
    否则读者「感觉有意思但发现内容和标题没关系」。
    可迁移至：项目简介、产品说明、邮件首段。
  tags: [abstract, structure, template]
```

## principles

```yaml
- id: p01
  title: 题目-摘要呼应原则
  type: principle
  source_chapter: 摘要章
  source_quote: |
    "摘要的第一句话应该呼应题目。对于题目中的关键词，在摘要中应该都有所提及。"
```

## cases

```yaml
- id: c01
  title: 孔子云孟子云孙子云反例
  type: case
  source_chapter: 文献综述章
  source_quote: |
    "当读者读到'孔子、孟子、孙子云'的文章，读到'孔子云'的时候，还可以理解，到'孟子云'的时候，就会想'孟子是同意还是不同意孔子说的呢'，但没有找到解释，正在疑惑，又读到一句'孙子云'。"
  summary: |
    绑定方法论：文献梳理器。罗列式综述的读者体验标本——
    连续三问无解答，认知负担层层加码。
```

## counter-examples

```yaml
- id: x01
  title: 文献驱动写法
  type: counter-example
  source_chapter: 文献综述章
  source_quote: |
    "(批判)literature driven写法，即被文献牵着鼻子走，文献说什么就写什么，欠缺对文献更深层次的理解以及对文献观点的梳理。"
  failure_mechanism: |
    被动转述→无观点组织→读者做综合→
    论文失去作者声音→综述沦为读书笔记汇编。
```

## glossary

```yaml
- id: g01
  term: literature driven 写法
  author_definition: 被文献牵着走的被动写作——罗列观点而无组织。
  key_distinction: ≠文献综述——后者必须有作者的梳理框架。

- id: g02
  term: 摘要六句结构
  author_definition: 问题一句+方法两句+结果两句+结论一句的经典压缩模板。
  key_distinction: ≠全文缩写——是独立可读的微型论证。

- id: g03
  term: 题目-摘要呼应
  author_definition: 题目关键词在摘要首句出现的对应纪律。
  key_distinction: ≠重复题目——是用关键词建立阅读预期。
```
