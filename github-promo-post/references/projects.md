# 已调研项目素材卡

> 数据全部来自各仓库 README（2026-08-14 抓取），写推文时直接引用，禁止编造。
> 仓库主：Natsummerance（GitHub）

## readMD — 轻量级 Markdown 阅读器（Windows）

- **一句话定位**：纯本地、秒开、离线可用的 Windows Markdown 阅读器，双击 .md 即读
- **star**：1 ⭐ ｜ **平台**：Windows 10/11 ｜ Python 3.9+ / WebView2
- **核心亮点**：
  - 秒开：冷启动 ≤1.5s（低配机/机械硬盘 ≤2s）；托盘常驻后双击 .md 瞬时唤起 <0.3s
  - 自动纠错：渲染前自动修 Markdown 错误（表格缺分隔行、未闭合 **/$、#标题缺空格、BOM、CRLF），只影响显示不改原文件
  - 万物转 MD：docx/pptx/xlsx/pdf/html/csv/json 一键转 Markdown（MarkItDown）
  - 扫描 OCR：图片/扫描 PDF 用 Win10/11 内置 OCR（离线免费支持中文）
  - 网页转 MD：输 URL 抓正文（trafilatura），同站批量最多 10 页合并一份
  - AI 助手：15+ 预设（OpenAI/DeepSeek/Kimi/GLM/通义/硅基流动/OpenRouter/Groq/xAI/Ollama/Anthropic），14 个 Prompt 模板，流式输出
  - 编辑：CodeMirror 6 高亮+自动补全 18 种语法，图片裁剪缩放旋转
  - 移动端共享：手机扫码同 Wi-Fi 阅读/转 MD/OCR/AI（随机令牌鉴权）
  - 大文档：>300KB 或 6000 行分块增量渲染不卡顿
  - 可设为 Windows 默认 .md 应用（用户级，免管理员）
- **上手成本**：Releases 下载安装包/便携版，双击即用；或 install.bat
- **差异化**：同类 Markdown 阅读器要么重（VS Code/Typora 启动慢）要么要联网；ReadMD = 本地 + 秒开 + 纠错 + 万物转 MD 一体

## doAI — 多 Agent 组织型全栈开发集群运行时

- **一句话定位**：像企业一样运转的多 Agent 开发集群——12 个岗位按「决策—管理—执行」三层治理开会写代码
- **star**：2 ⭐ ｜ Python 3.11+ ｜ React+Vite / Electron 桌面工作台
- **核心亮点**：
  - 12 岗位三层治理（产品/项目/前端/后端…），7 类会议以审批门（HITL）落地
  - YAML 流程 DSL 编译为 LangGraph StateGraph，无 LLM 也可运行（DSL 驱动）
  - 六步自我进化闭环：收集→提炼→提案→评审→生效→回滚
  - 23 工具三级权限（read / workspace_write / dangerous）+ MCP（stdio + Streamable HTTP）+ Docker 沙箱 + git worktree 隔离
  - 有界子代理：token 预算 + max_rounds 双截断
  - 桌面工作台：任务看板三轴仪表盘（成本/进度/健康）、审批弹窗、记忆库四级晋升、i18n 中英
  - 四平台安装包（Windows NSIS / macOS dmg+zip / Linux deb）+ electron-updater 自动更新 + GitHub Actions 五段 CI
  - **650 个测试通过**
- **上手成本**：桌面版下载即用；CLI：`pip install` + 一条命令
- **差异化**：vs LangGraph 裸写（要自己搭胶水）vs CrewAI（无审批门/无看板）；doAI = 组织化 + HITL 审批 + 可视化看板 + 发布就绪

## agents — 多端兼容 AI Agent 集合

- **一句话定位**：平台中立的 AI Agent 集合，同一 Agent 可部署到 OpenClaw / Codex / Hermes / Claude Code
- **star**：1 ⭐
- **现状**：fullstack-engineer v1.0.0（全栈开发专家，23 个技能，Superpowers 工程化 + 安全/性能红线）
- **结构标准**：IDENTITY.md / SOUL.md / AGENTS.md / USER.md / TOOLS.md / README.md + skills/（标准 YAML frontmatter）+ references/（相对链接）
- **上手成本**：clone 仓库 → 按 README 拷目录进对应平台技能目录
- **差异化**：一次性写 Agent，多平台复用；平台锁死是 Agent 圈最大的隐性成本

## skills — 个人开发技能集合

- **一句话定位**：项目理解 + 信息改写 + 开发与 UX 优化 + 小红书发布 + Hermes 运维的技能包（兼容 Codex / Claude Code / Hermes 的 SKILL.md 规范）
- **star**：2 ⭐
- **包含**：
  - project-learning / document-learning：吃透新项目/知识库的 onboarding 方法论
  - info-rewrite：工程化信息改写（脱敏→子代理改写+独立审查→校验报告）
  - dev-ux-optimizer：全周期开发+UX 优化（工程基线→里程碑→UX 重塑→部署验证）
  - xhs-publish：小红书图文全自动发布（CDP 桥接真实浏览器）
  - scheduled-social-campaign：零 token 批量定时发布（内容矩阵→状态机→no_agent cron）
  - weekly-report-creator / skill-comparator
  - Hermes/ 子目录：codex-bridge、wechat-desktop-automation、llm-api-cost-monitoring、person-watchdog 等实盘运维技能
- **上手成本**：clone → 拷进 agent 的 skills 目录即用
- **差异化**：不是理论教程，是「踩过坑的实战技能」——每个技能带坑位清单和验证清单
