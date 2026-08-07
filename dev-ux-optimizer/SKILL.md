---
name: dev-ux-optimizer
description: 全周期软件开发与 UX 优化方法：工程基线加固 → 增量里程碑交付 → UX 重塑（token 设计系统/暗色/动效/无障碍/移动端）→ 部署验证，并配套可执行的 agent 集群。适用于：(1) 既有 Web 应用（React/Vite + Serverless Functions + Postgres）需要系统性完善功能与体验；(2) 预测/数据类功能需要闭环（记录→算法→验证回填）；(3) 大规模 UX 重构或暗色/无障碍/性能达标；(4) Vercel/GitHub 自动部署链路排障与冒烟验证；(5) 需要多智能体并行协作的复杂开发任务。
---

# Dev + UX Optimizer

## Overview

把一次成功的大型项目交付（工程基线 → 数据驱动功能 → 记录体验 → 闭环反馈 → UX 重塑 → 部署排障）沉淀为标准流程。先稳再增量：每个里程碑独立交付、独立过质量门、独立部署验证。复杂任务用 agent 集群并行，HITL 决策不代答。

## Workflow Decision Tree

- **系统性完善既有应用**（功能+体验都要动）→ 按 Phase 0→4 全流程。
- **只做功能/数据闭环**（预测、记录、回填）→ Phase 1 基线 + Phase 2 里程碑。
- **只做 UX 优化**（状态/动效/文案/设计系统/暗色/无障碍）→ Phase 3。
- **部署/线上故障**（函数不执行、500、路由被吞）→ 直接看 references/dev-workflow.md 的「部署验证与排障」。
- **任务量大、可并行** → 先读 references/agent-cluster.md 再开 Phase 2/3。

## Phase 0 — 当前状态审计

1. 读 AGENTS.md、package.json、README.md、docs/，确认栈与已有约定。
2. 跑基线：pnpm typecheck、pnpm test、pnpm build，记录当前红绿。
3. 列出核心缺口（功能闭环断点、无测试/CI、UX 一致性、部署隐患），按 P0/P1 分级。
4. 产出简短审计结论，与用户确认范围与停机条件后再动手。

## Phase 1 — 工程基线（先稳）

- 补 vitest + test 脚本、tsc --noEmit 的 typecheck 脚本，修复存量类型错误。
- 为纯算法/纯函数补核心单测（边界、降级、空数据、数值手算样例）。
- 新增 CI：安装依赖 → typecheck → test → build。
- 清理重复类型/死代码；修正 README 与缺失文档（如 API 文档）。
- 验收：全绿、CI 通过、文档与代码一致。

## Phase 2 — 增量里程碑（M0→M3 模式）

每个里程碑独立可交付、独立验证后部署，再进下一个：

- **M0 稳定基线**：见 Phase 1。
- **M1 数据驱动**：把纯算法抽到共享模块（零依赖，前后端同一实现，单测锁定两端一致）；用真实打卡数据（BBT/OPK/粘液/压力）做周期分割与排卵校准；无数据时优雅降级（如 28 天），不再 500。
- **M2 记录体验**：快捷打卡、补打卡、连续天数与记录完整性提示；新经期开始联动预测回填。
- **M3 闭环反馈**：实际经期回填 API（PATCH）、准确率看板（按算法分桶）、新周期自动回填。

每个里程碑完成标准：typecheck 0 错 → test 全绿 → build 成功 → 手测清单 → commit → push → 线上验证。

## Phase 3 — UX 优化（3 个小里程碑，独立 commit）

- **UX-M1 状态与反馈**：alert→toast；保存中禁用按钮+spinner 防重复；错误态+重试；统一 Loading/Error/Empty 空态 CTA；触觉反馈一致。
- **UX-M2 动效与无障碍**：prefers-reduced-motion 全遵；统一 motion tokens；:focus-visible ring；数据读数 tabular-nums；图标按钮 aria-label；dialog 语义（role/焦点陷阱/Esc）。
- **UX-M3 文案与路径**：动作动词与 toast 措辞统一；错误文案具体、可行动、不道歉；全页面返回路径走查；占位页保留但补「即将上线」与返回。

设计系统与暗色、移动端/桌面响应式、性能拆包等详见 references/ux-playbook.md。

## Phase 4 — 部署验证

1. 质量门全绿后 commit + push（Git 集成自动部署）。
2. 轮询部署 READY；用运行时日志定位 500（vercel logs 或 API）。
3. 跑冒烟测试（登录/预测/记录/打卡/就医指引/导出/文章/SEO/SW）。
4. 关键端点抽查：未知路由 404 JSON、鉴权 401 JSON、公开接口 200 JSON（不被 SPA fallback 吞掉）。
5. 补部署结论到文档。

常见部署坑（Hobby 函数上限、catch-all 路由、ESM 导入、pg DATE 解析）见 references/dev-workflow.md。

## Agent 集群

复杂任务用子代理并行，主线程（编排者）负责拆分、整合与质量门：

- 并行 research（审计/性能/无障碍等）互不阻塞；实现任务按不相交写集拆给并行 worker。
- HITL 决策（方向、医疗合规、用户取舍）不委托给子代理。
- 每个 worker 返回：改动文件清单 + 验证结果；主线程 review 后过质量门。
- 角色、spawn 提示词与交接协议见 references/agent-cluster.md。

## 质量门与验收

- 每个 commit 前：pnpm typecheck 0 错 → pnpm test 全绿 → pnpm build 成功。
- 功能验收：手测清单（移动端视口、暗色、减弱动态效果、键盘遍历、错误/空态）。
- 数值/算法：用手算样例与回归测试锁定。
- 线上验收：冒烟 + 端点抽查 + 日志无 ERROR。

## 停机条件

- 方向分歧（用户价值取舍/医疗合规/范围扩展）→ 停下问用户，不擅自扩大。
- 质量门失败 → 返工修复后再继续。
- 越界需求 → 记 backlog，不并入当前波次。
- 安全/合规（就医提示、导出删除、隐私）→ 上线前必须经用户确认。

## References

- references/dev-workflow.md — 里程碑拆解、质量门、部署验证与排障（Vercel/Hobby/ESM/pg）。
- references/ux-playbook.md — UX 三个小里程碑、设计系统 token、暗色、无障碍、性能、wayfinder 决策地图。
- references/agent-cluster.md — agent 集群角色、spawn 提示词、并行与交接协议。
- references/pca-case-study.md — 本方法来源的完整实战案例（女性周期健康应用）。
