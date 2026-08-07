# Dev Workflow — 基线、增量交付与部署验证

## 1. 工程基线（M0）

- package.json 增加 `test`（vitest run）与 `typecheck`（tsc --noEmit）脚本。
- 核心纯函数补单测：后验更新、压力平移/方差膨胀、recency 加权、置信度饱和、空数据降级、相位边界、误差区间、仲裁分歧融合（≤1 天融合、>1 天取高置信度）。
- 数值断言用手算样例（如压力 2 周期后验均值偏移 2.5 天、置信度随样本饱和）。
- CI（GitHub Actions）：pnpm install → typecheck → test → build。
- 清理重复类型声明（如 ModelType 重复联合）、死依赖与死组件；README/API 文档与代码同步。

## 2. 数据驱动里程碑（M1）

- 纯算法放 `shared/`（零依赖），前端引擎与服务端共用同一实现；单测锁定两端同输入同输出。
- 用打卡表做周期分割：按 `period_start` 把日志归入周期；从 BBT 热位移、OPK 峰值、宫颈粘液峰值推导/校正排卵日。
- 校准信号按特异性排序：OPK 峰值 > 蛋清状粘液 > 持续 BBT 升温。
- 无数据/无校准信号时优雅降级（28 天 + 区间表达 + degraded 标记），绝不 500。
- 服务端 AI 预测继续消费全量日志；无 API Key 时整体降级为纯 Bayes。

## 3. 记录体验与闭环（M2/M3）

- 快捷打卡面板：点选日期弹出，经期开始/结束、点滴出血、疼痛、情绪、睡眠、压力一键记录；支持补打卡。
- 连续打卡天数 + 近 7 日记录完整性提示。
- 回填 API：PATCH /api/predictions/[id]（body 含实际日期），校验鉴权/日期合法性/不存在 404。
- 准确率看板按算法分桶（bayes/ai/ensemble），误差天数分布；记录新周期时自动回填未回填预测。

## 4. 质量门与提交纪律

- 每个 commit 前：`pnpm typecheck` 0 错 → `pnpm test` 全绿 → `pnpm build` 成功。
- 语义化 commit 前缀：feat/fix/docs/refactor/ci/test + 范围（如 fix(deploy): …）。
- 一次 commit 只做一个关注点；每里程碑独立 commit 并 push。
- 不修改 .gitignore 与 dist/ 既有策略；CRLF 警告属既有策略不处理。

## 5. 部署验证与排障（Vercel + Git 集成）

### 5.1 Hobby 12 函数上限

- 症状：部署 ERROR `exceeded_serverless_functions_per_deployment`（27 个 API 全挂）。
- 方案：收敛为单函数路由分发器 `api/handler.ts`，按路径段分发到 `server/routes/*`，其余全部迁出 api/。
- 注意：`api/[...slug].ts` 自动路由只匹配单段且排在 SPA fallback 之后，会被 `/(.*) → /index.html` 吞掉（GET 返回 HTML、POST 405）。
- 正确做法：vercel.json 重写 `"/api/(.*)" → "/api/handler?path=$1"`（查询参数合并保留），路由表顺序在 SPA fallback 之前。

### 5.2 ESM 相对导入必须带扩展名

- 症状：函数运行时 `ERR_MODULE_NOT_FOUND: Cannot find module '/var/task/shared/cycle/bayesian'`。
- 原因：编译产物保留无扩展名相对导入，Node ESM 要求 `.js`。
- 修复：全仓相对导入补 `.js`（tsconfig moduleResolution: bundler 下 `.js` 可解析到 `.ts` 源）。
- 验证：本地 `vercel build --yes` 后检查 `.vercel/output/functions/api/handler.func` 内 trace 文件与编译产物；直接 import 编译后的 handler 做模块加载测试。

### 5.3 pg DATE 列返回 Date 对象

- 症状：`a.period_start.localeCompare is not a function`、parseISO 崩溃、API 输出 ISO 时间戳。
- 根因修复：`types.setTypeParser(1082, (val) => val)` 让 DATE 列直接返回 `YYYY-MM-DD` 字符串（TIMESTAMPTZ 不受影响）。
- 防御层：纯函数入口把 `Date` 幂等归一化为字符串，并补 pg 行为回归测试。

### 5.4 线上验证清单

- 轮询部署：`GET https://api.vercel.com/v6/deployments?projectId=...&limit=1&target=production&teamId=...`，等待 READY。
- 运行时日志：`vercel logs <deployment-url|id>`（CLI 需要 --token/--scope），或 Dashboard。
- 端点抽查：未知路由 404 JSON、鉴权 401 JSON、公开接口 200 JSON、静态 SEO 200。
- 冒烟脚本：登录 → 预测（写 1 条记录）→ 周期记录 → 每日打卡 → 就医指引 → 导出 → OTP 通道（200/503/429 均视为信息项）→ 文章 → sitemap/robots/SW。
- 注意 CDN 缓存：旧响应可能 max-age=0 缓存，换路径或等待自然过期。
- 待人工配置项要列出：短信通道、Web Push VAPID、Sentry、Cron Secret 等。

## 6. 常用工具

- 搜索用 `rg`；批量编辑用 Node 脚本（注意 CRLF：先探测 EOL 再替换，避免整文件换行污染）。
- 环境变量来自 `.vercel/.env.production.local`（不入库）；本地 dev 走 Vite 代理直连线上 API = 操作生产库，先告知用户。