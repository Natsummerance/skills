---
name: document-learning
description: 帮助用户深度理解庞大的项目知识库/文档库（文档站点、Wiki、规范库、帮助中心、多格式混合知识库等文档型项目，而非代码库）。当用户说“帮我读懂这套文档/知识库”、“这个文档站我摸不透”、“深入理解产品文档/规范体系”、“知识库 onboarding”、“文档太多不知道从哪看起”等场景时触发。技能会先识别知识库形态，索引优先（TOC/nav/README/index/标签体系），向用户索取关键文档入口与领域术语，交互确认要深挖的主题后渐进采样阅读、追踪交叉引用、标记文档矛盾，产出/增量更新 ONBOARDING_NOTES.md（可选 CONTEXT.md 术语表与知识地图），提议创建 AGENTS.md/CLAUDE.md；与 project-learning 技能组成集合体：文档为主交接给本技能、代码为主交接给 project-learning。全程交互式、不臆断、省 token，输出中文。
---

# Document Learning：深度理解庞大项目知识库

> 目标：当"项目"本身是海量文档/知识库（文档站点、Wiki、规范库、帮助中心）时，让用户在最短时间内建立对整个知识体系的方位感与深挖路径，并把理解沉淀为可维护文档。与 project-learning（代码库 onboarding）组成技能集合体，互相引用、互相调用。

## 触发场景

- 用户说“帮我读懂这套文档/知识库”、“这个文档站我摸不透”、“深入理解产品文档/规范体系”、“知识库 onboarding”、“文档太多不知道从哪看起”
- 项目以文档为主：文档站点（mkdocs/docusaurus/vitepress）、Wiki（Obsidian/Confluence/MediaWiki 导出）、规范/标准库、帮助中心、多格式混合知识库
- project-learning 识别到“文档/知识库站点”类型时切换过来

## 核心原则

1. **只讲真实内容**：结论必须来自文档原文、索引、元数据；不确定就写“需要向团队确认”
2. **索引优先**：先读 TOC/nav/README/index/标签体系，再进正文（借鉴 LLM-Wiki 的 read-first 模式）
3. **交互式，不臆断**：形态判断、深挖主题、产出文件都先与用户确认
4. **渐进采样**：先全景后聚焦；大文档只读目录+摘要+关键节，不整读
5. **多形态适配**：先识别知识库形态，再选阅读策略，不套用单一模板
6. **矛盾标记**：文档之间、文档与代码矛盾或版本不一致时，显式标记并问用户
7. **省 token + 输出中文**（除非用户明确要求英文）
8. **联动与复用**：需要理解代码时交接 project-learning；非 Markdown 格式调用已装 docx/pdf/pptx/xlsx 技能读取

## 工作流程

### 第 0 步：识别知识库形态

轻量侦察（目录结构、文件名、配置文件），判断属于哪类形态，再选阅读策略：

| 形态 | 特征信号 | 侦察重点 | 深入重点 |
|---|---|---|---|
| 文档站点 | mkdocs.yml / docusaurus.config / vitepress + docs/ | nav 配置、目录树 | 主题与功能模块 |
| Markdown 知识库 / Obsidian Wiki | *.md + [[wikilinks]] / .obsidian / index.md | 索引、标签、双向链接 | 概念网络、原子页 |
| 规范/标准库 | specs/ standards/ 接口规范、编码规范、SOP | 规范清单与版本 | 核心规范与依赖关系 |
| 帮助中心/用户手册 | help/ manual/ docs + 多语言/版本目录 | 目录与版本 | 功能域、FAQ |
| 多格式混合库 | pdf/docx/pptx/xlsx/md 混排 | 格式分布、索引文件 | 各格式内容提取与关联 |
| 文档+代码混合仓库 | docs/ 与 src/ 同仓 | 文档/代码比例 | 判断主次，决定本技能 or project-learning |
| 学术/报告/论文库 | papers/ reports/ + bib/ | 索引、引用网络 | 研究主题与引用链 |
| 其他（Notion/Confluence/HTML 导出等） | *.html / export 包 | 目录结构 | 按形态定制 |

把“形态 + 一句判断依据”先告诉用户，让用户确认或纠正。混合形态（如 文档站点+代码同仓）并列说明，并问用户以哪个为主。

### 第 1 步：索引优先

- 找索引入口：README.md / index.md / mkdocs.yml nav / docusaurus sidebars / TOC / sitemap.xml / tags / SCHEMA.md（LLM-Wiki read-first）
- 只读结构不整读：目录树 + 各节标题 + 首页/简介
- 输出 3-5 行摘要 + 知识体系草图（主题 → 子主题），**请用户确认理解是否正确**

### 第 2 步：向用户索取入口（不臆断）

问用户（1-3 个必要问题）：
- 这套文档里哪些是最核心/最常用的入口？（避免在次要文档上浪费时间）
- 有哪些领域术语/黑话需要先对齐？（为 CONTEXT.md 术语表做准备）
- 你的目标是什么：整体摸底，还是围绕某个任务/模块深挖？

### 第 3 步：交互确认要深挖的主题

- 从索引 + 用户回答得到主题清单（控制在 5-8 项，省 token）
- 请用户选 1-3 个深挖主题并说明原因；不一次性全铺开

### 第 4 步：渐进采样阅读 + 交叉引用追踪

- 先读主题的入口页/概述页，再按需下钻
- 大文档：只读目录 + 摘要 + 关键节；用 grep 定位关键词，不整读
- 跟随交叉引用（wikilink/超链接/引用）补齐概念网络，记录“谁引用谁”
- 多格式：调用已装 docx/pdf/pptx/xlsx 技能提取；超长 PDF 先读目录页
- 矛盾/缺失：文档间矛盾、文档与代码矛盾、版本不一致 → 显式标记并问用户哪个为准
- 输出：主题理解（定义、要点、关联、风险/坑）+ 仍待确认问题，保持精炼

### 第 5 步：产出文档（确认后写）

- **主文档**：`ONBOARDING_NOTES.md`，增量更新（不存在则创建；已存在先读再做增量，保留用户内容）
  结构：知识库概述 / 形态 / 目录地图（知识体系） / 核心主题速查 / 术语表 / 矛盾与待确认 / 更新日志
- **与 project-learning 共享同一份 `ONBOARDING_NOTES.md`**：文档+代码混合项目由两个技能各自增量维护不同章节
- **可选**：`CONTEXT.md` 术语表——确有实质术语澄清时，问用户是否创建（与 project-learning 共用）
- **可选**：知识地图——Mermaid 概念图/主题关系图，写入 ONBOARDING_NOTES.md 或单独 `docs/map.md`
- **可选**：提议创建 `AGENTS.md` / `CLAUDE.md`（记录文档约定：索引入口、术语、更新流程），用户同意后创建
- 写前给用户看结构/变更点，确认后写

### 第 6 步：持续使用建议

- 检索式提问：“在知识库里搜一下 XX”（用 grep/索引定位，不重读全文）
- 维护建议：文档更新时同步 ONBOARDING_NOTES.md；发现失效链接/过期章节时提议修复
- 反复查询同一类问题时，考虑沉淀成 FAQ 页或封装 skill

## 联动：与 project-learning 组成技能集合体

- **判定规则**：项目以文档/知识库为主 → 本技能；以代码为主 → project-learning；混合 → 先确认主次，两部分由两个技能接力完成
- **交接协议**：本技能发现需读代码（如“文档里描述的实现细节”）→ 明确告诉用户“这部分建议交给 project-learning”，并附上已获得的上文摘要；反之 project-learning 发现文档量远超代码 → 交接给本技能
- **共享产物**：`ONBOARDING_NOTES.md`（同一文件，各技能增量更新各自章节）、`CONTEXT.md` 术语表（共用）
- **触发互补**：两个技能的 description 互相提及对方，避免同类触发词漏配


## 可引用技能（refs：更广阔的知识库）

学习项目时可按需引用已装技能扩展能力，清单见 `references/skill-ecosystem.md`（只加载需要的 1-2 个，不一次性全加载）：
- **技能搜索/发现**：`skillsmp-find-install`、`skill-grep`、`skill-installer`（.system）——遇到需要专业/领域知识时，先搜技能再学习
- **代码库理解补充**：`acquire-codebase-knowledge`（结构化产出模板）、`project-understanding`（token 预算视图）、`codebase-knowledge-builder`（知识产物沉淀）
- **知识沉淀**：`llm-wiki`（把项目理解编译成交叉引用知识库，长期复用）
- **方法论**：`research`（一手资料）、`domain-modeling`（术语）、`grill-with-docs`（访谈）

## 省 token 规则（硬性）

- 索引/目录/配置整读（通常很小）；正文只读入口页 + 关键节
- grep 优先于通读；大文件采样，不整读
- 多格式文档先看页数/目录再决定读法
- 输出摘要化，不贴大段原文、不列冗长文件清单
- 用户说“够了”就停；每轮只问 1-3 个必要问题

## 边界与兜底

- 无索引/无导航：按目录树 + 文件名推断，并告诉用户“建议补一份索引”
- 文档损坏/乱码/格式不兼容：标注并跳过，不硬猜
- 版本混乱：标记多版本并存，问用户以哪个为准
- 超大体量（数万页）：先地图后聚焦，主动询问优先级
- 无网络：不联网搜索，基于本地内容分析

## 参考来源（GitHub 现成技能 + 个性化改造）

- Karpathy LLM-Wiki 模式（win4r/llm-wiki-claude-skill）：read-first 索引、原子页、交叉引用、矛盾标记、分片分治
- github/awesome-copilot 的 acquire-codebase-knowledge：结构化“摸底 → 产出”流程框架
- yugasun/llm-wiki-skills（跨平台移植）、llmrix/llm-wiki-skill（知识图谱）：知识地图思路
- pdebruin/docs-skill、evil-skills/project-understanding：文档结构与 token 预算化视图
- **个性化改造点**：交互式确认（不臆断）、省 token 硬规则、8 种知识库形态表、与 project-learning 双向联动与共享产物、中文输出、增量更新与“提议后创建”策略

## 测试用例（验证用）

1. “这个 mkdocs 文档站太大了，帮我摸清楚结构和核心主题”（文档站点 → 完整流程）
2. “这是个 Obsidian 知识库，帮我理解里面关于智能体的概念网络”（Wiki → 交叉引用追踪）
3. “把这份接口规范库梳理成文档，重点看鉴权规范”（规范库 → 聚焦）
4. “这个仓库文档和代码都有，帮我整体摸底”（混合 → 判定主次并联动 project-learning）
5. “帮我更新 ONBOARDING_NOTES.md 的文档部分”（增量更新流程）