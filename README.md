# Skills：技能集合（项目理解 + 信息改写）

三个互相独立、可按需调用的 AI Agent 技能（兼容 Codex / Claude Code 的 SKILL.md 规范）：`project-learning` 与 `document-learning` 覆盖“吃透一个新项目”的两种形态；`info-rewrite` 提供工程化信息改写流水线。

## 包含的技能

| 技能 | 用途 |
|---|---|
| `project-learning` | 代码库 onboarding：识别架构类型 → README 优先 → 索取设计文档 → 交互确认深挖模块 → 访谈式探索 → 产出/增量更新 `ONBOARDING_NOTES.md` |
| `document-learning` | 知识库/文档库深度理解：识别知识库形态 → 索引优先（TOC/nav/index）→ 交互确认深挖主题 → 渐进采样 + 交叉引用追踪 → 产出/增量更新 `ONBOARDING_NOTES.md` |
| `info-rewrite` | 工程化信息改写：脱敏（过程脱敏+交付恢复）→ 子代理「改写执行+独立审查」双角色 → 主线程复核 + 机械校验 → 交付改写稿 + 逐条变更对照表 + 校验报告（可选导出 A4 中文 PDF），内置人称/称谓替换模板 |

每个技能目录内含各自的 `references/` 说明与模板：`project-learning` / `document-learning` 的 `references/skill-ecosystem.md` 列出可引用的技能生态（skill-search 类技能、llm-wiki、research 等），用于扩展学习项目时的知识来源；`info-rewrite` 的 `references/pronoun-rewrite-template.md` 内置人称/称谓替换矩阵与轻顺稿边界。

## 判定与交接

| 项目形态 | 使用技能 |
|---|---|
| 以代码为主 | project-learning |
| 以文档/知识库为主（文档站点、Wiki、规范库、帮助中心） | document-learning |
| 混合（代码 + 大文档） | 先确认主次，两部分由两个技能接力完成 |

> `info-rewrite` 与项目形态无关，用于任意文本的工程化改写（脱敏 + 子代理改写/审查 + 对照表 + 校验报告）。

## 共享产物

- `ONBOARDING_NOTES.md`：`project-learning` / `document-learning` 增量维护同一文件的不同章节（代码部分 / 文档部分）
- `CONTEXT.md` 术语表：共用
- `AGENTS.md` / `CLAUDE.md`：摸清项目后提议创建，用户同意后写入
- `info-rewrite` 交付：改写稿 + 逐条变更对照表 + 校验报告（用户要求时另出 PDF）

## 安装

把对应文件夹复制到技能目录，重启会话即可生效：

- Codex：`~/.codex/skills/<skill-name>/`
- Claude Code：`~/.claude/skills/<skill-name>/`

## 设计原则

交互式推进（不臆断）、省 token、多架构适配、只讲真实内容、中文输出、增量更新、提议后创建。