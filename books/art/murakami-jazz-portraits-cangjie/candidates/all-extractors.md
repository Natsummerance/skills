# 五路 Extractor 合并产出 — 《爵士群像》

## frameworks

```yaml
- id: f01
  title: 场景嵌入式乐评框架
  type: framework
  source_chapter: 全书各篇
  source_quote: |
    "说来不可思议，总之这张唱片百听不厌。当然乐队的成员也个个身手不凡：霍奇斯、韦伯斯特、库蒂、毕加德、卡内……正是埃林顿乐队的黄金时代，夫复何求？"
  summary: |
    村上式乐评三件套：①私人场景（何时何地听）
    ②具体曲目与乐手点名 ③生活感官细节（酒/食物/天气）。
    乐评不装权威，只交出「我」的听觉记忆。
    用于乐评写作/公众号音乐文案的文风参考。
  tags: [murakami, scene, music-essay]

- id: f02
  title: 文学性悖论概括法
  type: framework
  source_chapter: 加农炮艾德利篇
  source_quote: |
    "'加农炮'这个人，直到最后也未能创造出真正一鸣惊人的音乐。他作为自然之子降生于大地，作为自然之子走完人生之旅，悠悠然消逝而去。推敲与省察……并非此人音乐的擅长之处。"
  summary: |
    用一对文学性悖论概括乐手人格：
    自然之子vs推敲省察者——不做技术分析而做气质速写。
    风险：修辞替代分析；收益：非乐迷也能瞬间抓住人格。
    用于人物介绍文案的钩子句设计。
  tags: [paradox, portrait, murakami]
```

## principles

```yaml
- id: p01
  title: 私人趣味诚实原则（B面偏好）
  type: principle
  source_chapter: 埃林顿篇
  source_quote: |
    "如果进一步从个人角度加以筛选，则B面喜欢得无以复加。"
```

## cases

```yaml
- id: c01
  title: 乔·扎夫努尔的单音节钢琴
  type: case
  source_chapter: 加农炮篇
  source_quote: |
    "乔·扎夫努尔屏息敛气小心翼翼弹出的单音节独奏，同样无比悦耳。"
  summary: |
    绑定方法论：场景嵌入式乐评。「屏息敛气小心翼翼」——
    演奏状态描写替代术语堆砌。
```

## counter-examples

```yaml
- id: x01
  title: 权威姿态乐评
  type: counter-example
  source_chapter: 全书反衬
  source_quote: |
    (村上的反衬立场)乐评的正当性来自具体的私人听觉经验而非权威姿态。
  failure_mechanism: |
    以史实罗列+地位评判替代个人经验→读者得到维基百科而非聆听邀请→
    乐评失去分享性。
```

## glossary

```yaml
- id: g01
  term: B面偏好
  author_definition: 从个人角度筛选后的偏爱——专辑B面的私藏乐趣。
  key_distinction: ≠反经典姿态——是趣味的诚实而非刻意叛逆。

- id: g02
  term: 自然之子
  author_definition: 不做推敲与省察、凭天性演奏的音乐人格类型（加农炮艾德利）。
  key_distinction: ≠天才论——强调的是无自觉的天性流淌。
```
