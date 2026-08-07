# UX Playbook — 优化方法、设计系统与决策协议

## 1. 三个 UX 小里程碑（每步独立 commit + 验证）

### UX-M1 状态与反馈
- 全局挂载 toast（sonner 等）替代 alert：成功=已保存，失败=具体原因。
- 保存进行中禁用按钮 + spinner，防重复提交。
- 数据渲染 hook 的 error 全部展示并带「重试」；用统一 StateViews（Loading/Error/Empty）。
- 空态给一句可行动 CTA（空态即邀请，不是死胡同）。
- 快捷面板与主抽屉的触觉反馈（vibrate）保持一致。

### UX-M2 动效与无障碍
- 根组件包 `MotionConfig reducedMotion="user"`；globals.css 加 `@media (prefers-reduced-motion: reduce)`。
- 全局 `:focus-visible` ring：2px、阶段色、offset 2；对比度 ≥3:1。
- 抽取 motion 常量（spring/tap），消除抽屉/底部导航/卡片内联重复。
- 数据读数（天数、置信度、历史日期）统一 `tabular-nums`。
- 所有纯图标按钮补 `aria-label`；dialog 补语义（role、焦点陷阱、Esc、初始焦点，优先复用 vaul）。

### UX-M3 文案与路径
- 全 UI 动作动词与 toast 措辞统一；错误文案具体、可行动、不道歉。
- 全页面返回路径走查（App 传 onBack；抽查占位页/聊天页/报告页）。
- 占位页（通知/隐私/帮助）保留但补「即将上线」说明与返回按钮，不新增功能。
- 文案规范沉淀为 `docs/UX_COPY_GUIDE.md`（动作动词/toast/空态/错误/医学免责声明）。

## 2. 设计系统 Token 化

- 阶段色单源：`phase-tokens.ts`（light/dark 两套 hex + gradient class + accent），全站从此导入，禁止散落硬编码。
- theme.css 定义：`--phase-*`、`--font-sans` 系统字体栈（PingFang SC/Hiragino Sans GB/Microsoft YaHei/Noto Sans CJK SC）、radius 阶梯、4px 间距基准、z-index scale。
- 毛玻璃标准：blur + border + 内高光；tinted shadow 规范。
- 暗色模式：跟随系统 + 手动切换（next-themes，`attribute="class"`、`storageKey`、默认 system）；设置页加「外观」分组；全站对比度达标。
- 修正色系统一致性问题（如背景与阶段色不一致 → 统一为阶段色衍生背景）。

## 3. 移动端优先 + 桌面响应式

- 移动端信息优先级：今日阶段 → 下次月经/排卵摘要卡 → 快捷打卡 → 洞察。
- 日历语义化：button 日期、完整日期 aria-label、相位色深色化、图例对比度 ≥3:1；触控目标 ≥44px。
- 桌面启用 `useIsDesktop`（≥1024px）：主容器限宽居中、首页双栏（左今日/右洞察）、子页面限宽、BottomNav 限宽居中。
- 不引入桌面框架，响应式增强即可。

## 4. 性能与加载

- 页面级 `React.lazy` + Suspense；vite `manualChunks` 拆 vendor-core / vendor-charts / vendor-markdown / page-*。
- 骨架屏替换全屏 Loading（保留「生成中」态给 AI 页）；图片 lazy + onError 回退。
- 验收以主包 gzip 回落为准（示例：397.55 kB → 180–230 kB）。
- PWA 预缓存排除私有目录；SEO 静态页（sitemap/robots/articles）生成到 dist。

## 5. 无障碍清单（WCAG AA 要点）

- 对比度：正文/图例/焦点环 ≥3:1；暗色逐项核对。
- 焦点：:focus-visible 可见、Tab 顺序合理、dialog 焦点陷阱。
- 语义：label 关联、role=status/alert、表格 th scope、图标按钮 aria-label。
- 触控：目标 ≥44px；动态效果：recharts isAnimationActive 与 vibrate() 随 reduced-motion 关闭。

## 6. 大规模 UX 重构：wayfinder 决策地图协议

- 建图：`.scratch/ux-overhaul/` 下 `map.md`（Destination/Notes/Decisions so far/Not yet specified/Out of scope）+ `issues/` 每票一文件（## Question + 类型 label + blocking 声明）。
- 先建票，第二遍再接阻塞边；初始 frontier 为无阻塞的 research 票（可并行）。
- research 票（审计/性能基线/无障碍清单）：并行解，产出带引用的文件并链接回票。
- 决策票按阻塞顺序逐张解：调研/原型 → 与用户逐张讨论 → 记录 resolution → 关票 → 更新 Decisions so far → 毕业 fog 中可规格化的部分。
- HITL 票（方向、取舍）不委托子代理代答；不越票、不替真人发言。
- 地图清空后折叠：to-spec（规格）→ to-tickets（含阻塞边）→ 逐票 implement（tdd + code-review + 质量门）。
- 每张票独立 commit 与可回滚；收尾归档 `.scratch` 决策记录到 docs/。

## 7. 手测清单（每 UX 里程碑后）

- 断网/失败场景显示错误态与重试。
- OS「减弱动态效果」开启后抽屉与粒子动画关闭。
- Tab 键盘遍历焦点环可见；移动端视口全页面走查。
- 保存/删除有明确反馈；返回路径一致；暗色切换即时生效且刷新持久化。