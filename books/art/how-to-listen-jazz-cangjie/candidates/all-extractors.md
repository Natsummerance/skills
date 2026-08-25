# 五路 Extractor 合并产出 — 《如何听爵士》

## frameworks

```yaml
- id: f01
  title: 音乐图纸绘制法
  type: framework
  source_chapter: 聆听方法章
  source_quote: |
    "在这些音乐图谱的指引下，刚入门的爵士乐迷能逐渐意识到，原本听起来无拘无束甚至无影无形的音乐……"
  summary: |
    把即兴演奏画成结构图：前奏→主题（AABA）→各乐器轮流独奏（8小节为单位）
    →尾声。绘制四步：①数小节②标主题回归点③记独奏乐器轮换④标注特殊效果。
    让「无影无形」的音乐可追踪、可复述。
  tags: [chart, listening, method]

- id: f02
  title: 风格坐标定位法
  type: framework
  source_chapter: 风格史诸章（摇摆/比波普等）
  source_quote: |
    (摇摆与比波普的分野)知道一首歌在爵士谱系中的位置是聆听的坐标系。
  summary: |
    以风格史为坐标系定位任何曲目：摇摆（舞蹈性/大乐队）
    →比波普（反舞厅/小编制/高速和声）→冷爵士→自由爵士…
    听新曲目先问：它站在谱系哪里？反对什么？
  tags: [style-history, coordinates, framework]
```

## principles

```yaml
- id: p01
  title: 即兴非随意原则
  type: principle
  source_chapter: 结构章
  source_quote: |
    "(即兴)在和声框架内的实时作曲——每个8小节的独奏都有主题依据。"
```

## cases

```yaml
- id: c01
  title: 《人行道布鲁斯》图纸示范
  type: case
  source_chapter: 聆听方法章
  source_quote: |
    "先来看看钢琴师杰利·罗尔·莫顿和他的红辣椒乐队在1926年9月21日录制于芝加哥的《人行道布鲁斯》。前奏：调侃式对话，伴随着口哨和汽车喇叭音效。"
  summary: |
    绑定方法论：音乐图纸。从1926年录音逐段标注前奏/主题/独奏轮替，
    示范图纸如何还原一段「混乱」录音的结构。
```

## counter-examples

```yaml
- id: x01
  title: 无结构的「自由发挥」误解
  type: counter-example
  source_chapter: 结构章
  source_quote: |
    (初学者常误以为)即兴=想弹什么弹什么。
  failure_mechanism: |
    把即兴听成随机噪声→无法追踪主题→失去聆听锚点→
    断言「爵士就是乱吹」。矫正：先学曲式再谈自由。
```

## glossary

```yaml
- id: g01
  term: 音乐图纸
  author_definition: 焦亚的聆听工具——逐小节标注主题回归与独奏轮换的结构图。
  key_distinction: ≠乐谱——不记音符细节，只记结构与轮替。

- id: g02
  term: AABA曲式
  author_definition: 爵士标准曲常见骨架——32小节四段，第三段转折。
  key_distinction: ≠流行歌主副歌——A段重复而B段为bridge。

- id: g03
  term: 比波普 (bebop)
  author_definition: 1940年代兴起的小编制高速和声风格——从舞厅音乐转向艺术家音乐。
  key_distinction: ≠摇摆乐的加速版——是对摇摆功能的反叛。
```
