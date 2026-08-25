# 五路 Extractor 合并产出 — 《电影双书合蒸》

## frameworks

```yaml
- id: f01
  title: 摄影影像本体论分析
  type: framework
  source_chapter: 巴赞卷·01 摄影像影的本体论
  source_quote: |
    "如果用精神分析法研究造型艺术，就可以把涂防腐香料殓藏尸体视为造型艺术产生的基本因素。……大概会找到木乃伊'情结'。"
  summary: |
    造型艺术起源=对抗时间的心理需求（木乃伊情结）；
    摄影的独特性：无人类中介的物理印记（光化学过程）。
    分析任何影像媒介的「真实性主张」时问：
    它有物理成因链吗？数字影像动摇了这一根基。
  tags: [ontology, bazin, framework]

- id: f02
  title: 完整电影神话框架
  type: framework
  source_chapter: 巴赞卷·02 完整电影的神话
  source_quote: |
    "(对萨杜尔)经济技术的演进与探索者想象力之间主次关系颠倒的印象。"
  summary: |
    电影起源不是技术决定论：先有「完整再现生命」的神话想象，
    技术只是逐步追认。技术史与观念史的因果方向需重估。
    用于分析AI等新媒介的「技术驱动」叙事。
  tags: [myth-of-total-cinema, origin, framework]

- id: f03
  title: 蒙太奇伦理审查框架
  type: framework
  source_chapter: 巴赞卷·禁用蒙太奇诸篇
  source_quote: |
    (蒙太奇滥用)使现实的暧昧性丧失——导演替观众做了选择。
  summary: |
    巴赞不反蒙太奇本身，反其越界使用：
    当剪接把单一意义强加于现实时即背叛现实的暧昧。
    审查三问：这个剪接是在引导注意还是替代思考？
    现实的多义性被保留了吗？
  tags: [montage-ethics, ambiguity, framework]

- id: f04
  title: 跳接语法识别器
  type: framework
  source_chapter: 戈达尔卷·筋疲力尽镜头组分析
  source_quote: |
    "4个连续的跳接，镜头205到镜头209，他们躲在床单下面的镜头被切分开来了。"
  summary: |
    跳接=同机位同景别的时空省略——连续性剪辑的禁忌被戈达尔变成宣言：
    电影不必伪装成现实。
    识别三步：①确认机位未变②确认时间跳跃③判断其功能
    （节奏/间离/心理时间）。
  tags: [jump-cut, godard, grammar]

- id: f05
  title: 内部分段法（segmentation）
  type: framework
  source_chapter: 戈达尔卷·分析方法
  source_quote: |
    "我们提供一种内部分段法（segmentation）来说明一系列运动，它可以被当作是一条主线。"
  summary: |
    影片分析的标准化工具：把影片切分为镜头组，
    逐组记录镜头号与动作内容，形成可引用的分析底稿。
    任何逐镜头影评/论文的第一步操作。
  tags: [segmentation, method, tool]
```

## principles

```yaml
- id: p01
  title: 现实暧昧性原则
  type: principle
  source_chapter: 巴赞卷
  source_quote: |
    (景深镜头的价值)让观众与现实的距离保持完整——意义由观众自己选择。
```

## cases

```yaml
- id: c01
  title: 镜头组7的分镜头示范
  type: case
  source_chapter: 戈达尔卷
  source_quote: |
    "镜头组7的分镜头：镜头152到157：帕特里夏从公共汽车上下来，向旅馆的门房要钥匙。镜头158—159：她发现米歇尔在床上。"
  summary: |
    绑定方法论：内部分段法。逐镜编号+动作摘要的实操示范。
```

## counter-examples

```yaml
- id: x01
  title: 技术决定论叙事
  type: counter-example
  source_chapter: 巴赞卷·02
  source_quote: |
    "(批评萨杜尔)给人留下经济技术的演进与探索者想象力之间主次关系颠倒的印象。"
  failure_mechanism: |
    把媒介史写成技术进化史→遮蔽观念先行的事实→
    新媒介叙事（如AI电影）同样犯此错误。
```

## glossary

```yaml
- id: g01
  term: 木乃伊情结
  author_definition: 造型艺术的心理起源——以形式保存肉体对抗时间流逝。
  key_distinction: ≠死亡崇拜——是以生抗死的保存冲动。

- id: g02
  term: 完整电影的神话
  author_definition: 电影起源的想象性前提——对完整再现生命的憧憬先于并驱动技术发明。
  key_distinction: ≠技术乌托邦——是心理原型的史学功能。

- id: g03
  term: 跳接 (jump cut)
  author_definition: 同机位同景别下的时空省略；《筋疲力尽》将其从剪辑错误变为风格宣言。
  key_distinction: ≠普通转场——它暴露而非掩盖媒介性。

- id: g04
  term: 分段法 (segmentation)
  author_definition: 把影片按镜头组切分编号的分析工具，形成可引用的分析主线。
  key_distinction: ≠分镜表——是对成品的解剖而非拍摄计划。

- id: g05
  term: 场面调度 (mise-en-scène)
  author_definition: 单镜头内部的空间/表演/构图组织——巴赞美学的核心价值所在。
  key_distinction: ≠蒙太奇——调度保留时间连续性与观众选择权。
```
