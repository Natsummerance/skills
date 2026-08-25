# 五路 Extractor 合并产出 — 《诺顿音乐史》四卷合蒸

## frameworks

```yaml
- id: f01
  title: 统一性机制更替框架
  type: framework
  source_chapter: 四卷总纲（中世纪仪式→古典调性→20世纪序列）
  source_quote: |
    "十二音序列是一种规则，而不是'主题'。但是，因为现在用另一种方式获得了统一性……序列保证了统一性。"（韦伯恩语）
  summary: |
    西方音乐千年的主线是「统一性机制」的不断更换：
    ①中世纪：仪式与圣咏模式统一音乐
    ②古典时期：调性与奏鸣曲式统一
    ③20世纪：调性瓦解后由序列重新保证统一。
    分析任何音乐变革先问：旧的统一机制为何失效？
    新机制用什么替代？
  tags: [unity, mechanism, framework]

- id: f02
  title: 危机-应答史观
  type: framework
  source_chapter: 各时代转折章
  source_quote: |
    (每个时代的技术革新都是对前一时代危机的回答——复调之于仪式需求、标题音乐之于表达危机)
  summary: |
    音乐史的动力学：不是进步叙事而是问题解决叙事。
    每个革新=对上一代危机的应答。分析链：
    找危机→找应答→评估新危机（应答本身埋下下一场危机）。
  tags: [crisis-response, historiography]

- id: f03
  title: 规则与主题张力框架
  type: framework
  source_chapter: 20世纪卷·序列主义章
  source_quote: |
    "我也就能在主题主义范围之外来进行创作——也就是说要自由得多；序列保证了统一性。"
  summary: |
    创作的永恒张力：靠主题灵感组织 vs 靠规则系统组织。
    韦伯恩的解放宣言：在主题主义之外获得自由。
    用于分析一切创作系统的取舍（格律vs自由诗、模板vs原创）。
  tags: [rule-vs-theme, serialism, tension]
```

## principles

```yaml
- id: p01
  title: 记谱塑造音乐原则
  type: principle
  source_chapter: 中世纪卷
  source_quote: |
    (复调的精确记谱需求)记谱技术的演进直接塑造了多声部音乐的可能性空间。
```

## cases

```yaml
- id: c01
  title: 格里高利与教会音乐制度
  type: case
  source_chapter: 中世纪卷·第一章
  source_quote: |
    "伟大的圣格里高利，最有影响力的早期教皇……在他的众多功业中，格里高利也关心过教会音乐生活。"
  summary: |
    统一机制的制度起点：圣咏曲目整理是权力行为——
    音乐统一服务于教会统一。
- id: c02
  title: 勋伯格《交响曲》的结构清晰性
  type: case
  source_chapter: 20世纪卷·序列主义章
  source_quote: |
    "随同这种精确的重复一起，《交响曲》结构上的清晰性——第一乐章明显地分为三个部"
  summary: |
    绑定方法论：统一性更替。序列并未带来混乱，
    反而以新规则重建了结构清晰性。
```

## counter-examples

```yaml
- id: x01
  title: 进步叙事陷阱
  type: counter-example
  source_chapter: 全书体例反思
  source_quote: |
    (警惕教材正典叙事)把音乐史读成从简单到复杂的进化，遮蔽了每个时代自身的完整性与选择逻辑。
  failure_mechanism: |
    进步叙事→晚期风格被默认为高级→早期音乐被当作
    未完成态→历史理解退化为排行榜。矫正：
    每个时代的统一机制在其语境内部评价。
```

## glossary

```yaml
- id: g01
  term: 格里高利圣咏
  author_definition: 罗马教会仪式的单声部拉丁歌曲目，以格里高利一世命名。
  key_distinction: ≠格里高利个人创作——是制度化整理的传统累积。

- id: g02
  term: 复调
  author_definition: 多条独立旋律线的组合写作，西方艺术音乐的独特路径。
  key_distinction: ≠和声——复调强调线条独立，和声强调纵向色彩。

- id: g03
  term: 标题音乐
  author_definition: 附有文字说明、指向音乐以外内容的器乐作品（浪漫主义典型）。
  key_distinction: ≠绝对音乐——后者拒绝文本外指。

- id: g04
  term: 十二音体系
  author_definition: 勋伯格创立的作曲法——半音阶十二音平等化，以序列规则取代调性中心。
  key_distinction: ≠无序偶然——恰恰是用最严格的规则换取统一性。
```
