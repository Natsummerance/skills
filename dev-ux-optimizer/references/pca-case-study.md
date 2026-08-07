# Case Study — PCA 女性周期健康应用（本方法的实战来源）

## 1. 项目概览

- 栈：React/Vite + Tailwind v4 + motion + PWA；Vercel Functions + Neon Postgres + DeepSeek；GitHub Actions CI。
- 核心闭环：记录周期/打卡（BBT、LH、宫颈粘液、OPK、睡眠、疼痛）→ Bayesian + AI 预测 → 实际经期回填验证 → 准确率看板。
- 域：`period-calculate-algorithm.vercel.app` / `pca.syminu.online`；中文 UI，毛玻璃 + 四阶段色（月经/卵泡/排卵/黄体）。

## 2. 推进路径（一次完整的大项目交付）

1. **M0 工程基线**：vitest/typecheck/CI；核心算法单测（后验更新、压力平移、置信度饱和、仲裁）；文档。
2. **M1 数据驱动**：Bayesian 引擎抽到 `shared/cycle/bayesian.ts`（零依赖，前后端同实现）；打卡数据周期分割 + 排卵校准（OPK>粘液>BBT）；无数据 28 天降级。
3. **M2 记录体验**：快捷打卡面板、补打卡、连续天数、新经期触发回填联动。
4. **M3 闭环反馈**：`PATCH /api/predictions/[id]` 回填实际日期；按 bayes/ai/ensemble 分桶的准确率看板；新周期自动回填。
5. **UX 重塑（wayfinder 决策地图）**：13 张决策票（审计/性能/无障碍 research 并行 → 字体/色彩/表面/IA/动效/文案 HITL 票 → 原型票）→ to-spec → 9 个语义 commit 落地：token 化（phase-tokens + --phase-* + 暗色跟随系统）、首启引导、桌面响应式、骨架屏、无障碍、文案指南。
6. **6 个月路线图**：60 问访谈 → docs/ROADMAP.md + 6 份分主题文档（预测/记录/健康信任/AI/留存/技术）。
7. **P0–P4 执行**：预测区间+概率日历+协变量+异常归因+就医提示；备孕/围绝经期；就诊摘要；Web Push + 导出 + 冷静期删除 + 指标；缓存/Sentry/性能门槛。
8. **医疗合规**：就医指引三档 + 8 篇知识库经用户审核通过后发布；SEO 静态文章页上线。

## 3. 部署排障实录（教训最密集的一段）

- **Hobby 12 函数上限** → 27 个 API 全 ERROR。收敛为单函数 `api/handler.ts` 分发 27 个 `server/routes/*`。
- **catch-all 无效**：`api/[...slug].ts` 自动路由排在 SPA fallback 之后且只匹配单段 → 线上所有 `/api/*` 返回 HTML/405。改为 vercel.json `"/api/(.*)" → "/api/handler?path=$1"`。
- **ESM 无扩展名导入**：`analysis.ts` 引 `shared/cycle/bayesian` 缺 `.js` → `ERR_MODULE_NOT_FOUND`。全仓相对导入补 `.js`。
- **pg DATE 列**：pg 把 `date` 解析为 Date → `localeCompare is not a function`、parseISO 崩溃。根因：`types.setTypeParser(1082, val => val)` 输出 `YYYY-MM-DD`；防御层：纯函数入口归一化 + 回归测试。
- **冒烟断言**：`/api/health/guidance` 返回 `{ items }` 而非数组 → 修脚本断言。
- 最终：冒烟 14/14 通过；typecheck 0 错、201 测试全绿、build 成功、主包 gzip 64.07 kB。

## 4. 沉淀的可复用经验

- 先稳再增量；每里程碑独立可交付 + 质量门 + 部署验证。
- 纯算法进 shared/ 单源，前后端一致由单测锁定。
- 大型 UX 重构走决策地图：research 并行 → HITL 逐张决议 → 折叠成规格 → 逐票实现。
- 部署排障三件套：本地 `vercel build --yes` 查路由表与函数包 → 运行时日志定位 → 冒烟+端点抽查验证。
- 医疗/健康类文案必须有用户确认的审核关口，测试断言与文档同步锁定口径。

## 5. 遗留待办（作为下一步示例）

- 配置 OTP_WEBHOOK_URL（短信通道）、Web Push VAPID、Sentry DSN。
- 移动端 Lighthouse 补录；PATCH 非数字 id 的 404 优化。
- 推送通知、数据导出增强、i18n、社交分享等列入 backlog（明确不做项）。