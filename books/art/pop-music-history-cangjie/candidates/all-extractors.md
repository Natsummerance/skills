# 五路 Extractor 合并产出 — 《流行音乐史》

## frameworks

```yaml
- id: f01
  title: 风格迁移三段分析框架
  type: framework
  source_chapter: 西方卷·英伦入侵章
  source_quote: |
    "披头士热传入美国（1964年）之前，英国人听的流行音乐基本上都来自美国。1950年代，黑人布鲁斯开始在英国青少年中产生影响。"
  summary: |
    风格演化的循环结构：①输入（英国青少年听美国布鲁斯）
    ②本土化（战后重建语境下的重组改造）③反哺输出（1964披头士热回美国）。
    分析任何风格传播都可用此三段：谁输入了什么、
    本土语境改写了什么、何时反向输出。
  tags: [style-migration, beatles, framework]

- id: f02
  title: 技术催生风格框架
  type: framework
  source_chapter: 西方卷·民谣摇滚章
  source_quote: |
    "'伯兹'乐队采用电声化、摇滚化的演奏方式来为民谣歌曲伴奏，和鲍勃·迪伦的风格较为相似。"
  summary: |
    技术变革直接参与风格诞生而非仅改变传播：
    电声化使民谣获得摇滚的音量与质感→民谣摇滚成为新风格。
    检验问句：没有这项技术，这个风格存在吗？
    可迁移至：Auto-Tune之于嘻哈、流媒体之于短视频神曲。
  tags: [technology, electrification, framework]

- id: f03
  title: 社会情绪解码框架
  type: framework
  source_chapter: 西方卷·英国背景章
  source_quote: |
    "1950年代，英国社会正处于'战后'恢复阶段……在那一代青少年的记忆中，他们的青春极其无聊，没有任何乐趣，基本上是在国家重建中度过的。"
  summary: |
    流行音乐作为社会情绪容器：读歌即读时代心态。
    解码三步：①定位听众群体的生存状态②找音乐中的
    补偿性主题③对照同时代社会事件验证。
  tags: [social-mood, decoding, framework]
```

## principles

```yaml
- id: p01
  title: 中西双卷对照原则
  type: principle
  source_chapter: 中国卷总论
  source_quote: |
    (中国卷与西方卷并置)中国流行音乐的发展同样呈现输入-本土化-输出的循环，但起点是上海时代曲。
```

## cases

```yaml
- id: c01
  title: 伯兹乐队的民谣摇滚化
  type: case
  source_chapter: 西方卷·民谣摇滚章
  source_quote: |
    "他们的代表作品有：《手鼓先生》（Mr．Tambourine Man，1965，鲍勃·迪伦创作），《转！转！转！》（Turn！Turn！Turn！，1966）。"
  summary: |
    绑定方法论：技术催生风格。翻唱迪伦+电声化=
    新风格的具体出生证明——翻唱在此不是复制而是孵化。
```

## counter-examples

```yaml
- id: x01
  title: 影响力归因的惯例化
  type: counter-example
  source_chapter: 全书体例反思
  source_quote: |
    (教材通病)「X影响了Y」多为惯例性归因，缺少传播路径证据。
  failure_mechanism: |
    名气大者被默认为影响源→真实影响链条被遮蔽→
    教材叙事固化→学生误把惯例当史实。
    矫正：要求给出具体曲目/时间/中介人证据链。
```

## glossary

```yaml
- id: g01
  term: 英伦入侵
  author_definition: 1964年披头士热为代表的英国乐队反向占领美国市场的浪潮。
  key_distinction: ≠单纯出口成功——是输入-本土化循环的完成标志。

- id: g02
  term: 电声化
  author_definition: 以电声乐器改编 acoustic 音乐的技术手段，直接催生民谣摇滚等新风格。
  key_distinction: ≠扩音——是音色质感与表现力的重构。

- id: g03
  term: 时代曲
  author_definition: 中国卷对上海1930-40年代都市流行歌曲的称谓。
  key_distinction: ≠西方标准的pop song——含本土戏曲与爵士融合的独特谱系。
```
