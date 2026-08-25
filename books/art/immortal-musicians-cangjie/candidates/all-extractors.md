# 五路 Extractor 合并产出 — 《不朽的演奏家》

## frameworks

```yaml
- id: f01
  title: 国家学派溯源框架
  type: framework
  source_chapter: 演奏风格起源章
  source_quote: |
    "大约在十七世纪中期，演奏风格开始与国家性格相联系，意大利和法国在演奏风格上的差异更加明显了。至于其他国家的小提琴演奏的情况，在很大程度上是追随着这两大演奏学派。"
  summary: |
    个人风格的地基是国家学派：意大利派vs法国派的差异
    先于任何个体天才存在。分析一位演奏家先问：
    他属于哪个学派谱系？继承了什么、偏离了什么？
    警惕：国家性格论的本质主义风险。
  tags: [national-school, style-genealogy, framework]

- id: f02
  title: 诠释再创作论
  type: framework
  source_chapter: 全书核心命题
  source_quote: |
    (诠释是意义的再创作)同一作品在不同演奏家手下是不同的作品。
  summary: |
    演奏家不是作曲家的仆人：速度/力度/分句的每次选择
    都构成一次再创作。比较两个录音时问：
    各自把作品「变成了什么作品」？
  tags: [interpretation, re-creation, framework]
```

## principles

```yaml
- id: p01
  title: 录音证据原则
  type: principle
  source_chapter: 西盖蒂章等
  source_quote: |
    "这一点在录音中可以听得很清楚；两位演奏家之间有着很奇怪的'距离'。"
```

## cases

```yaml
- id: c01
  title: 西盖蒂与同行同台
  type: case
  source_chapter: 西盖蒂章
  source_quote: |
    "执，而西盖蒂也似乎突然放弃了他那冷静的态度，结果就失去了第三乐章快板的那种均衡性。……但是在慢乐章中巴赫成为仲裁人，所有的竞争都消除了。"
  summary: |
    绑定方法论：诠释竞争分析。同台即竞争——
    快板失衡暴露较劲，慢乐章共同臣服于文本。
    「巴赫成为仲裁人」=作品本身高于一切诠释。
- id: c02
  title: 意法学派的分野
  type: case
  source_chapter: 风格起源章
  source_quote: |
    "提琴已经有了辉煌的声音和丰富的表现手法，这两方面结合在一起日益普及起来，其结果是不同的演奏风格开始出现。那些为舞蹈提供伴奏的提琴手，不能与那些从事复杂演奏的独奏家相比。"
  summary: |
    绑定方法论：国家学派框架。功能分化（舞蹈伴奏vs独奏）
    是学派分野的物质起点——先有分工后有美学。
```

## counter-examples

```yaml
- id: x01
  title: 国家性格本质主义
  type: counter-example
  source_chapter: 方法论警示（由f01引申）
  source_quote: |
    (警惕)「民族性」解释常滑向刻板印象——意大利=热情、法国=优雅是概括不是因果。
  failure_mechanism: |
    用民族性解释个人风格→忽略个体训练与唱片市场→
    解释变成套话。矫正：先查师承与录音史实再谈学派。
```

## glossary

```yaml
- id: g01
  term: 国家学派
  author_definition: 与国家性格相联的演奏风格传统（意/法两大学派，他国追随）。
  key_distinction: ≠血统决定论——是历史形成的训练与审美传统。

- id: g02
  term: 诠释竞争
  author_definition: 同行同台时的暗中较量——演奏会同时是竞技场。
  key_distinction: ≠敌意——竞争可被作品文本消解。

- id: g03
  term: 巴赫成为仲裁人
  author_definition: 勋伯格语——当诠释者共同臣服于乐谱文本时，竞争消失。
  key_distinction: ≠作曲家权威崇拜——是文本对诠释的约束时刻。
```
