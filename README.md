# Skills · AI Agent 技能集合

个人开发的 AI Agent 技能库（兼容 Codex / Claude Code / Hermes 的 SKILL.md 规范），包含三大板块：

| 板块 | 说明 | 索引链接 |
| :--- | :--- | :--- |
| 📚 **[books/](books/INDEX.md)** | **书籍蒸馏技能库**——全量 59 本高价值书籍 → 326 个原子化 RIA-TV++ Agent Skills | [进入书籍总索引](books/INDEX.md) |
| 🛠 **通用技能** | 项目理解 / 信息改写 / 开发与 UX / 内容发布等通用开发与效能工具 | 见根目录 |
| ⚙️ **[Hermes/](Hermes/)** | Hermes Agent 平台运维技能（实盘沉淀） | [查看运维技能](Hermes/) |

---

## 📚 books/ · 书籍蒸馏技能库 (RIA-TV++)

用 **cangjie RIA-TV++** 流水线把高价值经典书籍深度蒸馏为**原子化、可被 Agent 直接调用执行**的专业技能（SKILL.md）：
- **非单纯书摘**：将书中的核心思想抽离为带触发条件、执行机制、工作流步骤、正反案例对比、判停标准的工业级方法论。
- **100% 原文溯源**：每一篇技能均具备精准的原文引用与章节锚点，杜绝断章取义与幻觉。
- **多级解耦索引**：按领域（`philosophy`、`art`、`science`、`psychology`、`history`、`literature`、`film`、`writing`）与书目建立层层索引。

👉 **完整分类与书目导航请访问：[books/ 深度索引 (books/INDEX.md)](books/INDEX.md)**

---

## 🛠 通用技能

| 技能 | 用途 |
| :--- | :--- |
| `project-learning` | 代码库 onboarding：架构识别 → README 优先 → 交互确认深挖 → 产出 `ONBOARDING_NOTES.md` |
| `document-learning` | 知识库/文档库深度理解：索引优先 → 渐进采样 + 交叉引用追踪 |
| `info-rewrite` | 工程化信息改写：脱敏 → 子代理「改写+独立审查」双角色 → 机械校验 → 改写稿 + 变更对照表 + 校验报告 |
| `dev-ux-optimizer` | 既有应用全周期开发与 UX 优化：工程基线 → 增量里程碑 → UX 重塑（token/暗色/动效）→ 部署验证 |
| `xhs-publish` | 小红书图文发布全流程：CDP 桥接真实浏览器（Edge 9222），自动发布/编辑/多图/话题标签 |
| `scheduled-social-campaign` | 零 token 批量定时发布：预生成内容矩阵 JSON → 状态机脚本 → no_agent cron 驱动 |
| `github-promo-post` | GitHub 项目推广 + 小红书图文：compare/Release 核查、推文撰写、1080×1440 海报生成 |
| `weekly-report-creator` | 周报生成/优化/精简，Markdown 转 Word/PDF |
| `skill-comparator` | Skill 版本 A/B 对比：独立子智能体实验隔离上下文污染，量化评估选优 |

---

## ⚙️ Hermes/ · 平台运维技能

本机 Hermes Agent 实盘运维沉淀，均带完整排障记录：

| 技能 | 用途 |
| :--- | :--- |
| [`codex-bridge`](Hermes/codex-bridge/) | 飞书/微信 `@codex` 遥控本机 Codex 会话：fire-and-forget 注入、`--wait` 同步、`/switch` 切会话 |
| [`codex-bridge-debugging`](Hermes/codex-bridge-debugging/) | Codex 会话监控排查：新会话无提醒时的 Z 盘优先阶梯排查 |
| [`wechat-desktop-automation`](Hermes/wechat-desktop-automation/) | 微信桌面端自动回复机器人：BitBlt+RapidOCR 读取、Win32 发送、OCR 验证 |
| [`llm-api-cost-monitoring`](Hermes/llm-api-cost-monitoring/) | LLM API 成本/余额 cron 监控与告警 |
| [`person-watchdog`](Hermes/person-watchdog/) | 摄像头人形监控守护：YOLO 检测→飞书通知，部署/自启/省电/相机排障方法论 |

---

## 📦 安装与使用

把对应技能目录复制到本地 Agent 技能目录，重启会话即可生效：
- **Codex**：`~/.codex/skills/<skill-name>/`
- **Claude Code**：`~/.claude/skills/<skill-name>/`
- **Hermes**：`<hermes-home>/skills/<category>/<skill-name>/`

---

## 📐 设计原则与质量红线

1. **真实内容**：严禁无原文依据的凭空捏造，所有方法论均有文本出处。
2. **解耦清晰**：同书内各个技能触发场景互斥，杜绝同义反复与逻辑重叠。
3. **层级管理**：根 README 保持轻量，依托子目录 `INDEX.md` 实现无限扩展的多层级索引。
