# 补充 Extractor 产出 — 《爵士群像》（数量补齐轮）

> 目标：2→5 skills。新增3个skill所需的候选单元

## frameworks（补充）

```yaml
- id: f03
  title: 唱片纪念物叙事法
  type: framework
  source_chapter: 比克斯·贝德拜克篇
  source_quote: |
    "这两首曲收于美国哥伦比亚唱片公司的《比克斯·贝德拜克作品第2辑》。我离开'SWING'的时候作为纪念品得到了这张唱片，一直视为珍品。"
  summary: |
    村上乐评的物件锚点技法：以一张唱片的获得场景
    （离开酒吧时的纪念品）承载人物记忆。
    物件=私人音乐史的时间戳。用于回忆性写作的细节设计。

- id: f04
  title: 乐手谱系速写法
  type: framework
  source_chapter: 迈尔斯·戴维斯篇
  source_quote: |
    "在查理·帕克手下演奏。1948年得到吉尔·埃文思等人的协助，组建重视编曲的历史性的九重乐队。……他总是引领爵士乐的走向（例如大胆采用电声键盘）。"
  summary: |
    用「师承+关键转折+风格预言」三笔勾勒一个乐手的
    历史位置：帕克手下→九重乐队→电声键盘。
    与fragmentary-portrait-writing互补：
    那是精神碎片，这是谱系骨架。
```

## cases（补充）

```yaml
- id: c02
  title: 比克斯的白人爵士第一人
  type: case
  source_chapter: 比克斯篇
  source_quote: |
    "一位在爵士乐史上首次确立白人爵士乐地位的天才。可惜酗酒损害了健康，致使他过早结束了怀才不遇的一生。"
  summary: |
    绑定jazz-life-music-unity补充案例：
    天赋/酒精/早逝的三位一体——怀才不遇的叙事原型。
- id: c03
  title: 迈尔斯的电声键盘
  type: case
  source_chapter: 迈尔斯篇
  source_quote: |
    "他总是引领爵士乐的走向（例如大胆采用电声键盘），留下大量专辑唱片。1975年一度隐退，1981年戏剧性地东山再起。"
  summary: |
    绑定f04谱系速写：「引领走向」的判断+
    隐退/再起的戏剧弧线——速写法的完整示范。
```

## glossary（补充）

```yaml
- id: g03
  term: 纪念品唱片
  author_definition: 与特定时空绑定获得的唱片——私人音乐史的物证。
  key_distinction: ≠收藏品——价值在记忆锚点不在版本稀缺性。

- id: g04
  term: 引领走向者
  author_definition: 不跟随流派而创造流派的乐手类型（迈尔斯）。
  key_distinction: ≠大师——强调方向感而非完成度。
```
