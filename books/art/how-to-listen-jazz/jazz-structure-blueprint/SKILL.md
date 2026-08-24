---
name: jazz-structure-blueprint
description: 爵士曲式结构蓝图：12小节布鲁斯、32小节AABA、节奏变化，以及如何跟着贝斯数拍子听出结构。
version: 0.1.0
author: Summer (Natsumer), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [爵士乐, 曲式, 布鲁斯, AABA, 蒸馏技能]
    related_skills: [jazz-listening-framework, jazz-improvisation-anatomy, jazz-rhythm-decode, jazz-history-map]
---

# 爵士曲式结构蓝图

> 蒸馏自 Ted Gioia《如何听爵士》第三章"爵士乐的结构"。把作者讲的结构知识抽成可跟着音乐数拍子的操作手册。原书章节存于 `knowledge/book-library/distill/ruhetingjazz/chapters/`。

## When to Use

- 用户问"爵士曲子是怎么组织的""12小节布鲁斯/AABA 是什么"
- 用户想跟着音乐数拍子、画出某曲结构图
- 用户听到曲子"突然转向、重心在乐器间乱跳"想弄懂规律
- **Don't use for**: 想听即兴独奏内部句法（去 `jazz-improvisation-anatomy`）、想听节奏摇摆（去 `jazz-rhythm-decode`）

## 核心命题（I）

1. **95% 的爵士遵循"主题与变奏"**：旋律（主题）→ 按和声即兴、轮流独奏（变奏）→ 回归主题。极端情况也有，但录音/现场超 95% 符合（ch.3）。
2. **三种主流长度**：32 小节（AABA 等）、12 小节（布鲁斯）、16 小节——自 1930 年代初主导；你能数到 32 就能跟上（ch.3）。
3. **录音技术塑造结构**：爱迪生录音一次<3分钟，逼出简单结构；78转唱片时长限制让艾灵顿《褐景》回文对称被打断（ch.3）。
4. **以 4 小节为单位呼吸**：爵士乐手不爱质数，独奏/鼓对话几乎都以 4 小节（或 8/12/16）为单位，从不在 3/5/7 小节（ch.3）。

## E — 可执行结构辨认步骤

### 步骤 1：锁定基本框架
- 先判断主题长度：32 / 16 / 12 小节？大部分标准曲（Gershwin、Cole Porter、Irving Berlin 改编）主题 32 小节。
- 12 小节多为布鲁斯；短曲常开头结尾各奏两次旋律。

### 步骤 2：辨认 32 小节 AABA
- A（8小节）+ A（8小节）+ B（8小节，过门 Bridge/Release，近关系调对位）+ A（8小节再现）。
- 另一种 32 小节：16 小节旋律奏两遍，第二遍结尾略变。
- 最简：单一主题 12 或 26 小节不断重复。

### 步骤 3：跟着贝斯数 4/4 拍
- 注意力放**贝斯**而非鼓（现代鼓已脱离奠定节拍角色）；贝斯常每拍都奏=漫步低音 (walking bass)，是数拍参照（ch.3）。
- 以 2 或 4 小节为节奏单位感受脉动；爵士最常见结构都能被 4 整除。
- 非传统拍子线索：曲名常明示——Paul Desmond《十一四》(Eleven Four)=11/4；Pat Metheny《5-5-7》=5+5+7；Denny Zeitlin《六与七》(At Sixes and Sevens)=6/7 迂回（ch.3）。

### 步骤 4：画结构图（用书中三份图纸练习）
- **艾灵顿公爵《褐景》(Sepia Panorama, 1940)**：A(12)+B(16)+C(8)+D(12)+D(12)+C(8)+B(8)+A(12)+尾声(2) — ABCDDCBA 回文。
- **杰利·罗尔·莫顿《人行道布鲁斯》(Sidewalk Blues, 1926)**：序曲+10小节序曲+12A+12B+12A+4间奏+32C+32C+6尾声 — 罕见地把 12 小节布鲁斯与 32 小节歌曲曲式结合。
- **查利·帕克《突尼斯之夜》(Night in Tunisia, 1946)**：基本 AABA，但插入迪齐·吉莱斯皮写的 12 小节间奏 + 帕克 4 小节无伴奏华彩。
- ✅完成标准：能徒手画出任一首的结构字母图，并标出"轮奏四"(Trading Four) 的 4 小节对话处。

### 步骤 5：训练资源
- 《爵士乐：史密森尼选集》(Jazz: Smithsonian Anthology) 百首 + 详细结构描述。
- 练"轮奏四"：Sonny Rollins + Coltrane《次中音萨克斯之狂》(Tenor Madness, 1956)、Dexter Gordon + Wardell Gray《竞赛》(The Chase, 1952)、Clifford Brown/Max Roach《布鲁斯漫步》(Blues Walk, 1955)。

## B — 边界

- **局限**：作者承认 20 世纪初（1920s 前）与近年许多爵士乐手尝试超越主导结构，特殊案例不赘述；本 skill 聚焦 95% 主流框架。
- 偏美国流行歌曲/爵士标准曲视角；非洲/拉美复合节拍仅提及未深究。
- 不适用：严格作曲法/对位学术分析、非爵士曲式（赋格等）。

## 相关 skills

- composes-with: jazz-listening-framework（步骤5）、jazz-improvisation-anatomy（变奏段即 Solo 容器）、jazz-rhythm-decode（4小节节奏单位）
- contrasts-with: 无互斥

## 审计信息

- 蒸馏来源：ch.3 爵士乐的结构（主题与变奏、三种长度、AABA、爱迪生录音限制、4/4 与质数、贝斯数拍、三份音乐图纸、轮奏四）
- 书中具体论据：艾灵顿《褐景》《搭乘A线》、莫顿《人行道布鲁斯》、帕克《突尼斯之夜》、史密森尼选集、Sonny Rollins/Coltrane《Tenor Madness》
- 蒸馏时间: 2026-08-24
