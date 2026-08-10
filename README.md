# Skills：技能集合（项目理解 + 信息改写 + 开发与 UX 优化 + 小红书发布 + Hermes 运维）

六个互相独立、可按需调用的 AI Agent 技能（兼容 Codex / Claude Code / Hermes 的 SKILL.md 规范）：`project-learning` 与 `document-learning` 覆盖“吃透一个新项目”的两种形态；`info-rewrite` 提供工程化信息改写流水线；`dev-ux-optimizer` 提供既有应用的全周期开发与 UX 优化（工程基线 → 增量里程碑 → UX 重塑 → 部署验证），并配套可执行的 agent 集群；`xhs-publish` 与 `scheduled-social-campaign` 提供小红书内容发布与零 token 批量定时发布能力。

`Hermes/` 子目录存放 Hermes Agent 平台专用技能（本机 Hermes 实盘运维沉淀）：`codex-bridge-debugging`（Codex 会话监控排查方法论）、`wechat-desktop-automation`（微信自动回复机器人运维）、`llm-api-cost-monitoring`（LLM API 成本/余额 cron 监控）、`person-watchdog`（摄像头人形监控守护：部署/自启/省电/自动学习/飞书通知 + 相机监控排障方法论）。

## 包含的技能

| 技能 | 用途 |
|---|---|
| `project-learning` | 代码库 onboarding：识别架构类型 → README 优先 → 索取设计文档 → 交互确认深挖模块 → 访谈式探索 → 产出/增量更新 `ONBOARDING_NOTES.md` |
| `document-learning` | 知识库/文档库深度理解：识别知识库形态 → 索引优先（TOC/nav/index）→ 交互确认深挖主题 → 渐进采样 + 交叉引用追踪 → 产出/增量更新 `ONBOARDING_NOTES.md` |
| `info-rewrite` | 工程化信息改写：脱敏（过程脱敏+交付恢复）→ 子代理「改写执行+独立审查」双角色 → 主线程复核 + 机械校验 → 交付改写稿 + 逐条变更对照表 + 校验报告（可选导出 A4 中文 PDF），内置人称/称谓替换模板 |
| `dev-ux-optimizer` | 全周期开发 + UX 优化：工程基线加固 → 数据闭环（记录→算法→回填验证）→ UX 重塑（token/暗色/动效/无障碍/移动端）→ 部署验证与排障；内置 agent 集群（角色/spawn 规则/并行与交接协议）与完整实战案例 |
| `xhs-publish` | 小红书图文发布全流程：自动发布/编辑/草稿/状态查询/登录/多图配图/话题标签，CDP 桥接真实浏览器（Edge 9222），内置 12 条实战坑位与内容红线 |
| `scheduled-social-campaign` | 零 token 批量定时发布（每小时一篇、内容不重复、N 篇后自动静默）：一次性预生成内容矩阵 JSON → 状态机发布脚本 → no_agent cron 驱动，发完零成本空转；附赫尔佐格回顾展 12 篇实战案例 |
| `Hermes/codex-bridge-debugging` | Codex 会话监控排查：`@codex` 新会话无提醒 / `/switch` 列表缺失时的 Z 盘优先阶梯排查（数据目录迁移根因、死路清单、修复模板、验证清单） |
| `Hermes/wechat-desktop-automation` | 微信桌面客户端自动回复机器人运维（`watch_eruting.py`）：完整链路（BitBlt+RapidOCR 读取、Win32 发送、OCR 验证去空白）+ 全部已知坑与排障记录 |
| `Hermes/llm-api-cost-monitoring` | LLM API 成本/余额监控（cron watchdog 模式）：DeepSeek 余额查询、零 token 告警、凭据安全读取纪律 |
| `Hermes/person-watchdog` | 摄像头人形监控守护（PersonWatchdog）：部署/自启/省电/自动学习/飞书通知 + 相机监控类排障方法论（进程消失、CPU 飙高、ONNX 线程、画面亮度诊断、计划任务 LastRun=1999 等实测结论） |

每个技能目录内含各自的 `references/` 说明与模板：`project-learning` / `document-learning` 的 `references/skill-ecosystem.md` 列出可引用的技能生态（skill-search 类技能、llm-wiki、research 等），用于扩展学习项目时的知识来源；`info-rewrite` 的 `references/pronoun-rewrite-template.md` 内置人称/称谓替换矩阵与轻顺稿边界。

## 判定与交接

| 项目形态 | 使用技能 |
|---|---|
| 以代码为主 | project-learning |
| 以文档/知识库为主（文档站点、Wiki、规范库、帮助中心） | document-learning |
| 混合（代码 + 大文档） | 先确认主次，两部分由两个技能接力完成 |
| 既有应用要系统性完善功能与体验（或部署/线上故障排障） | dev-ux-optimizer |
| 定时批量发布小红书/社交内容（每小时一篇、N 篇后暂停） | scheduled-social-campaign（配 xhs-publish 发布） |
| 需要手动/单次发布小红书图文 | xhs-publish |
| 检测摄像头前经过的人并飞书通知 / 相机监控排障 | Hermes/person-watchdog |

> `info-rewrite` 与项目形态无关，用于任意文本的工程化改写（脱敏 + 子代理改写/审查 + 对照表 + 校验报告）。
> `dev-ux-optimizer` 同样与项目形态无关，用于既有 Web 应用的开发完善与体验优化（React/Vite + Serverless + Postgres 栈已有完整排障经验沉淀）。

## 共享产物

- `ONBOARDING_NOTES.md`：`project-learning` / `document-learning` 增量维护同一文件的不同章节（代码部分 / 文档部分）
- `CONTEXT.md` 术语表：共用
- `AGENTS.md` / `CLAUDE.md`：摸清项目后提议创建，用户同意后写入
- `info-rewrite` 交付：改写稿 + 逐条变更对照表 + 校验报告（用户要求时另出 PDF）

## 安装

把对应文件夹复制到技能目录，重启会话即可生效：

- Codex：`~/.codex/skills/<skill-name>/`
- Claude Code：`~/.claude/skills/<skill-name>/`
- Hermes：`<hermes-home>/skills/<category>/<skill-name>/`（如 `social-media/xhs-publish`）

## 设计原则

交互式推进（不臆断）、省 token、多架构适配、只讲真实内容、中文输出、增量更新、提议后创建。
