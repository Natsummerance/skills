# Skills · AI Agent 技能集合

个人开发的 AI Agent 技能库（兼容 Codex / Claude Code / Hermes 的 SKILL.md 规范），三大板块、15 个技能：

| 板块 | 内容 |
|------|------|
| 📚 [books/](books/README.md) | **书籍蒸馏技能库**——6 本书 → 49 个原子化 Agent Skills |
| 🛠 通用技能（根目录 9 个） | 项目理解 / 信息改写 / 开发与 UX / 内容发布 |
| ⚙️ [Hermes/](Hermes/) | Hermes Agent 平台运维技能 5 个（实盘沉淀） |

---

## 📚 books/ · 书籍蒸馏技能库

用 cangjie RIA-TV++ 流水线把高价值书籍蒸馏成**原子化、可被 Agent 直接调用**的 skills：不是书摘，而是把书里的方法论抽成带触发条件、执行步骤、边界声明的可执行框架。每个 skill 保证原文引用可溯源、同类 skill 触发场景互斥。

| 分类 | 书 | skills |
|------|-----|--------|
| philosophy | 《哲学史方法论十四讲》邓晓芒 | 14 |
| philosophy | 《游心之路：〈庄子〉与现代西方哲学》Moeller & D'Ambrosio | 7 |
| art | 《如何听爵士》Ted Gioia | 7 |
| art | 《然而，很美：爵士乐之书》Geoff Dyer | 4 |
| art | 《美的历史》《丑的历史》Umberto Eco | 3 |
| psychology | 《第二性》Ⅰ+Ⅱ 波伏瓦 | 12 |
| science | 《学术写作原来是这样》易莉 | 5 |
| science | 《新教伦理与资本主义精神》《学术与政治》韦伯 | 3 |
| art | 《爵士乐群英谱》村上春树×和田诚 | 1 |
| art | 《见证：肖斯塔科维奇回忆录》伏尔科夫 | 2 |
| art | 《人人都该懂的古典音乐》朱利安·约翰逊 | 1 |

**合计 11 本书 / 60 个 skills**。总导航见 [books/README.md](books/README.md)，分类索引在 `books/<category>/INDEX.md`，每本书有独立文件夹与书级 INDEX（含使用导航与质量记录）。

示例入口：
- 想学「怎么听懂一首爵士曲」→ [`books/art/how-to-listen-jazz/jazz-listening-framework`](books/art/how-to-listen-jazz/jazz-listening-framework/SKILL.md)（七步聆听法）
- 被社会角色压得喘不过气 → [`books/philosophy/genuine-pretending/zhuangzi-true-pretending`](books/philosophy/genuine-pretending/zhuangzi-true-pretending/SKILL.md)（庄子式「真实假装」）
- 论文写完想自查论证 → [`books/science/xueshu-xiezuo/academic-argument-logic`](books/science/xueshu-xiezuo/academic-argument-logic/SKILL.md)

## 🛠 通用技能

| 技能 | 用途 |
|---|---|
| `project-learning` | 代码库 onboarding：架构识别 → README 优先 → 交互确认深挖 → 产出 `ONBOARDING_NOTES.md` |
| `document-learning` | 知识库/文档库深度理解：索引优先 → 渐进采样 + 交叉引用追踪 |
| `info-rewrite` | 工程化信息改写：脱敏 → 子代理「改写+独立审查」双角色 → 机械校验 → 改写稿 + 变更对照表 + 校验报告 |
| `dev-ux-optimizer` | 既有应用全周期开发与 UX 优化：工程基线 → 增量里程碑 → UX 重塑（token/暗色/动效）→ 部署验证；内置 agent 集群协议 |
| `xhs-publish` | 小红书图文发布全流程：CDP 桥接真实浏览器（Edge 9222），自动发布/编辑/多图/话题标签，12 条实战坑位记录 |
| `scheduled-social-campaign` | 零 token 批量定时发布：预生成内容矩阵 JSON → 状态机脚本 → no_agent cron 驱动，发完自动静默 |
| `github-promo-post` | GitHub 项目推广 + 小红书图文：compare/Release 核查、推文撰写、1080×1440 海报生成 |
| `weekly-report-creator` | 周报生成/优化/精简，Markdown 转 Word/PDF |
| `skill-comparator` | Skill 版本 A/B 对比：独立子智能体实验隔离上下文污染，量化评估选优 |

## ⚙️ Hermes/ · 平台运维技能

本机 Hermes Agent 实盘运维沉淀，均带完整排障记录：

| 技能 | 用途 |
|---|---|
| [`codex-bridge`](Hermes/codex-bridge/) | 飞书/微信 `@codex` 遥控本机 Codex 会话：fire-and-forget 注入、`--wait` 同步、`/switch` 切会话 |
| [`codex-bridge-debugging`](Hermes/codex-bridge-debugging/) | Codex 会话监控排查：新会话无提醒时的 Z 盘优先阶梯排查 |
| [`wechat-desktop-automation`](Hermes/wechat-desktop-automation/) | 微信桌面端自动回复机器人：BitBlt+RapidOCR 读取、Win32 发送、OCR 验证 |
| [`llm-api-cost-monitoring`](Hermes/llm-api-cost-monitoring/) | LLM API 成本/余额 cron 监控与告警 |
| [`person-watchdog`](Hermes/person-watchdog/) | 摄像头人形监控守护：YOLO 检测→飞书通知，部署/自启/省电/相机排障方法论 |

## 安装

把对应文件夹复制到技能目录，重启会话即可生效：

- Codex：`~/.codex/skills/<skill-name>/`
- Claude Code：`~/.claude/skills/<skill-name>/`
- Hermes：`<hermes-home>/skills/<category>/<skill-name>/`

## 设计原则

交互式推进（不臆断）、省 token、只讲真实内容、中文输出、增量更新。
书籍蒸馏红线：每 skill 带原文短引可溯源；解耦复查（触发互斥）+ 遗漏复查（对照全书目录）；慢就是快。
