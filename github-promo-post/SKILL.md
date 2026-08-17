---
name: github-promo-post
description: 推广 GitHub 开源项目并制作小红书图文，支持版本更新、GitHub compare/README/Release 核查、标题正文、1080×1440 海报和发布 artifact。用户要求推广项目、写 GitHub 更新推文、生成小红书配图或处理 vX→vY 更新时使用。
---

# github-promo-post — GitHub 项目小红书推广推文

把用户的 GitHub 开源项目写成能涨 star 的小红书推文。核心原则：**切真实痛点，不写功能清单，人味 > 正确**。

## 触发场景

- 用户说「推广我的 GitHub 项目」「写开源项目安利笔记」「小红书推 readMD/doAI/…」
- 为任意 GitHub 项目（自己的或第三方的）写小红书推广文案

## Codex 版本更新模式

用户提出 `vX → vY` 更新时，按以下顺序执行：

1. 读取 GitHub compare、README、Release 和 commit subject；动态事实只使用这些来源。
2. 先检查目标版本是否存在正式 Release。若不存在，正文只能写「更新线」「准备中」或「主分支已准备」，不能写「已发布」。
3. 对 readMD 使用 `assets/readmd-v2-template/` 的 6 张已验证模板；保留 HTML 的 CSS、画布、字号和版式，只替换与更新事实相关的文字。
4. 每张图输出 1080×1440 JPG，运行 `references/poster-spec.md` 与 `scripts/validate_poster.py` 要求的校验；不要输出 `_raw_*.png`。

### readMD v2.1.1 → v2.2.2 事实重点

- v2.2.0：AI schema v2、隐私与自定义连接、单行编辑工具栏、命令面板、公式选择器和图片编辑升级。
- v2.2.1：原生 macOS 发布线。
- v2.2.2 主分支准备内容：网页转 Markdown 双级抽取、WebView/Readability 降级、同站最多 10 页、可选图片本地化，以及统一 Windows/macOS 包。
- 不编造性能数字、下载量、用户数量或未被来源支持的功能。

### 跨 skill 输出契约

写作和配图完成后，写入同一 `artifacts/` 目录：

```text
title.txt
body.txt
topics.txt
metadata.json
images/xhs-01-cover.jpg ... images/xhs-06-cta.jpg
```

`metadata.json` 必须包含 `title`、`body`、`topics`、`images`、`source_urls`、`version_state`。`images` 使用绝对路径，`topics` 为不带 `#` 的 5 个话题。

交付前执行：

```powershell
python scripts/validate_artifacts.py artifacts
python scripts/validate_poster.py artifacts/images
```

两个命令均通过后，`artifacts/` 可直接交给 `xhs-publish`：不再手工复制文案、重排话题或选择图片。

## 流程

### Step 1 — 调研仓库（先做，别跳）

1. 读 README：抓 `raw.githubusercontent.com/<owner>/<repo>/main/README.md`（失败试 master）
2. 提取素材卡片：**一句话定位 / 3-6 个亮点（每点带具体数字）/ 差异化（vs 主流方案）/ 上手成本 / 适用人群 / star 数**
3. 无本地 README 就 curl GitHub API 仓库详情（stargazers_count、description）
4. 输出素材卡片后再进入 Step 2（素材不齐禁止动笔）

### Step 2 — 定人群与痛点

- 一个项目只服务一个主人群（程序员 / 学生 / 效率党 / Agent 玩家…），写清楚：谁、在什么场景、有多痛
- 痛点必须具象（「Markdown 表格渲染出来是乱的」「配 Agent 要写几百行胶水代码」），禁止抽象概念（「效率低下」）
- 痛点开场 3-5 行，让目标读者对号入座，再引出项目

### Step 3 — 标题（≤20 字含标点）

用 dbs-xhs-title 的公式库出 5-8 个候选，标注公式编号，定稿 1 个。GitHub 推文高频命中：
- 数字锚定（#26-32）：「3 个 GitHub 上被低估的…」「1 个工具搞定…」
- 好奇缺口（#7-12）：「程序员不会告诉你的…」「藏在 GitHub 的宝藏…」
- 身份代入（#21-25）：「每个被 Markdown 折磨过的人都该看…」
- 反常识（#1-6）：「为什么你的 Markdown 渲染总出错」
- 结果承诺（#33-40）：「30 秒把 PDF 变成 Markdown」
标题铁律：前 8 字定生死、留悬念不说答案、≤20 字。

### Step 4 — 正文结构（600-900 字，上限 1000）

```
[痛点开场 3-5 行：具象场景，让读者对号入座]

[一句话定位：这项目是什么，一句话说清]

[核心亮点 3-5 条：1️⃣2️⃣3️⃣ 短行 + 换行，每条一个场景+一个数字/效果，
不用加粗；按「先解决最痛的」排序]

[上手成本：多简单（下载即用/两条命令），降低行动门槛]

[适用人群 1-2 行：谁适合用，谁不适合（真实感）]

[仓库信息：GitHub 搜 <项目名>（或放链接），求 star/收藏]

[结尾提问：评论区聊什么，引导互动]
```

写作纪律：
- 每条亮点对应一个真实场景（「写毕业论文时表格全乱 → 打开 ReadMD 自动修好」），禁止罗列技术名词
- 人味 > 正确：句子长短错落、允许口语、禁 AI 腔（空洞排比、连续祈使句「请你记住」「真相是」）
- 数据必须真实（秒开 1.5s、650 个测试、12 个岗位…都来自 README，禁止编造）
- 不用 emoji 堆砌；分点用 1️⃣2️⃣3️⃣ 或数字+换行

### Step 5 — 配图（HTML 设计，不草率）

- 封面：3:4 竖版 1080×1440，**文字大字报 ≤15 字**，信息流 0.5-1 秒内看懂
- **配色死板 = 投诉项**（2026-08-15 用户硬要求：v3 配色方案不能太死，不然每篇都一样甚至一个模板）：**每篇推文必须专属强调色 + 版式轮换**，禁止多篇同色同版式。做法：\n  - 强调色从色盘轮换：荧光黄（readMD 已用）/荧光青（doAI 已用）/琥珀橙（scheduled 已用）/荧光绿/玫红/电光紫/冰蓝/亮白… 新篇避开已用色，选新色；同色至少隔 N 篇再用\n  - 版式轮换：6 种版式（封面 2×2 卖点/痛点卡/大数字/前后对比/流程管道/CTA）不是固定顺序，每篇可换序、换主版式、微调布局（标题位置/卡片数/装饰语言）\n  - 范式不变：深蓝底 #0B1B3A 系 + 专属荧光强调色 + 三明治布局 + build_v3.py 链路 + poster-spec 校验；变的是强调色与版式组合，不是生成链路\n- **多套卡组必须统一设计系统**（用户实测教训：两套主题混用=「风格割裂」）：同一底色系（全深底）+ 同一版式模板（头栏/标题/内容区/底条三明治）+ 同字体同装饰语言，仅品牌强调色不同（readMD=荧光黄、doAI=荧光青）
- 卡组结构（每项目封面+5 内容页），**每张卡版式不同**（封面满版色块/痛点 2×2 卡/大数字对比/代码前后对比/管道图/仪表盘/荧光底 CTA），避免六张卡同构=AI 感
- 版式硬规则（用户实测教训）：
  - **禁止绝对定位堆叠卡片**（倾斜堆叠/负 margin 重叠 → 文字重叠）；内容全部流式布局
  - 内容区三明治：头栏 + `flex:1` 内容（grid/flex 填满）+ 底部条 `margin-top:auto`，杜绝大面积空白
  - 装饰元素（水印/星标/圆点）只放背景层，不与文字区重叠；不出血（不超出 poster 边界）
  - 字体：微软雅黑 + Consolas，禁 Inter/Roboto（AI 默认字体）
  - **字号阶梯与「放大消除空白」策略**（2026-08-14 用户两轮验收定稿）：1080×1440 卡内主标题 80-98px、内容区主元素（卡片标题/代码）30-40px、正文 24-28px、辅助 18-26px——元素普遍偏小（标题 60px、正文 20px）是「中间大面积空白」的根因；修法=字号/padding 整体上调 20-40% 让内容自然撑满，而不是 flex 拉伸。验证标准：视觉复核必须确认「标题明显变大」「中间空白显著减小」「无溢出换行」
- 生成方式：写单文件 HTML → Edge headless 截图 → **PIL 裁剪修复**（见下）
- **截图链路（Windows 实测，必坑）**：Edge headless 的渲染视口 < `--window-size`（本机实测 UI 占位吃 32×104px）→ 内容右/下被裁 + 露出 body 白边 =「底部显示不完全」「白边截断」。正确姿势：
  1. HTML：`html,body{width:100vw;height:100vh;overflow:hidden;background:#000}`，poster 固定 1080×1440 且背景非黑
  2. 截图：`--window-size=1400,1800`（视口 1368×1696 > poster，内容完整）
  3. PIL：扫描非黑像素 bbox → 裁剪 → LANCZOS resize 到精确 1080×1440
  4. **自检**：输出图四边 4px 内必须是背景色（非白非黑），bbox 必须 = (0,0,1080,1440)
- **卡内禁止真实链接/URL**（小红书限流红线，用户实测）：`github.com/xxx` 域名形式也不行；用「GitHub 搜 <项目名>」话术（见 Step 6）

### Step 5.5 — 严格范式校验（2026-08-14 用户硬要求：生成逻辑+校验逻辑+严格范式）

- **范式定义**：`references/poster-spec.md`（画布/字号阶梯/配色/版式硬规则 + 校验阈值）——生成前先读，生成器必须遵守
- **脚本校验**：`scripts/validate_poster.py <图或目录>`，像素级 7 项：尺寸精确 1080×1440 / 四边 4px 无白边 / 内容占比 ≥5% / **最大空白带 ≤120px**（逐行扫非背景像素，命中「中间大面积空白」）/ 底部内容距底 ≤90px / 顶部 ≤220px / 左右不出血。全 PASS 才可交付；build_v3.py 生成末尾自动调用，FAIL 即 exit 1
- **双轨校验缺一不可**：脚本抓像素级硬伤（空白带/白边/溢出），vision_analyze 抓语义级问题（换行断句、错别字、视觉平衡）——2026-08-14 实测脚本抓出 10/12 卡空白带超标并量化驱动修复，视觉抓出 readMD 04 代码 54px 下换行断裂（脚本检测不到）
- **空白带修复闭环**：先跑脚本定位最大空白带的 y 区间 → 对应 HTML 区块放大字号/padding 或加内容行 → 重建 → 复跑直到 PASS（本轮 12/12 从 2/12 迭代 4 轮修到全过）

### Step 6 — 红线与字数检查（发布前必查）

- 正文/标题**禁**：公众号、微信、闲鱼、转卖、出票、二维码、淘宝等站外引流词（详见 xhs-publish 内容红线）
- **配图卡内禁真实链接/URL**（小红书限流红线，用户实测 2026-08-14）：`github.com/xxx`、`www.`、http 形式一律不放；卡内只写「GitHub 搜 <用户名>/<项目名>」——**用户名必须写在前面**（用户硬要求，如「GitHub 搜 Natsummerance/readMD」，禁止只写 readMD）+「评论区蹲链接」话术；CTA 卡三处放全名：顶部标签 NATSUMMERANCE/READMD、主蓝块 Natsummerance/readMD、深蓝条 GitHub 搜索：Natsummerance/readMD
- 标题 ≤20 字含标点；正文 ≤1000 字（实用 600-900）
- 话题标签 3-8 个：#GitHub #开源 #程序员 #效率工具 #开发工具 #AI #编程（按项目选）
- 发布走 xhs-publish 技能（自动发布/草稿/状态查询）

## Step 7 — 自动推送链路（2026-08-14 建成，操作手册见 references/auto-pipeline.md）

四库（readMD/doAI/skills/agents）→ 小红书，零 token 定时任务 + 触发语双通道：

- **定时任务**（cron 94f34ec49e39，每 30 分钟）：`scripts/xhs_github_cycle.py` 依次跑
  ① `github_updates.py`（GitHub API 拉四库 commits，state 去重，新增条目入队）→
  ② `xhs_github_publish.py`（取队列一篇：T3 更新公告/T4 单条安利模板生成推文+封面→范式校验→发布）。
  无更新/队列空 → 静默。
- **触发语**：「帮我把GitHub更新发小红书」→ 会话内先跑 `python scripts/github_updates.py`
  查新 commit；有新 → 用类型库（poster-types.md）精细创作推文（非模板）+ 配图 → xhs_publish 发布；
  无新 → 直接回复「没有新更新」。
- **「没更新的不写」**：github_updates.py 与 state.json（xhs_github_state.json）比对 last_sha，
  只有新 commit 才入队；首跑自动建基线不发历史。

**模板配图布局定案**（脚本内置，勿回退到纯 flow——那方案已被证伪）：
- **DPI 根因**：Windows 125% 缩放时 Edge headless 按物理像素输出（CSS 视口被缩到 864px 裁切 body）→ 必须 `--force-device-scale-factor=1`；此前所有 absolute/flex 漂移皆为 DPI 所致
- **布局**：body flex column + `justify-content:space-between` + foot `position:absolute;bottom:60px`；**所有 flex 子项 `flex-shrink:0`**（uptitle 曾被压到 5px）
- **截图**：`--screenshot=路径` 等号语法 + `file:///` URL；window-size 1080×1544 → 裁剪 1080×1440（Edge UI 占 104px）
- **空白带原理**：校验器空白带 = 行盒空白 + margin + space-between 段距 三者累加；内容不足时**放大 li 字号吃满空间**（58→72→88→104）而不是拉伸间距；单条 li 时加「怎么用」CTA 区块 + date 放大
- **内容填充**：4 个话题 chips（#GitHub #开源 #程序员 等）固定区块，每图多 ~120px 内容，更小红书风
- **line-height**：1.1-1.4 收紧（行盒空白是空白带主要来源）；rule 与 sub 之间 margin 48/40

## 已调研项目素材卡

见 `references/projects.md`（readMD / doAI / agents / skills 四仓库亮点、差异化、数字）。新项目按 Step 1 自行采集后追加。

## Pitfalls

1. 禁止只列功能名（「支持 OCR」「支持 AI」）——每条都要带场景+效果
2. 禁止编造 star 数/测试数/性能数字，全用 README 实测数据
3. 标题超 20 字会被平台拦截（toast「标题最多输入20字哦~」）
4. 一个项目一篇文章，别把四个项目塞一篇（分条目推广）
5. GitHub 链接可放正文，但「公众号/微信/淘宝」类引流词一票否决；**配图卡内一律不放 URL**（限流），用「GitHub 搜 XX」
6. Edge headless 截图坑：`--window-size` ≠ 渲染视口（UI 占位 32×104px）→ 必须大窗口截图 + PIL 裁剪非黑 bbox + resize 到精确尺寸 + 边缘自检，否则底部截断/白边（详见 Step 5）
7. 卡组版式：禁绝对定位堆叠（文字重叠）、内容三明治填满（防空白）、装饰不出血、多套卡组统一设计系统（防割裂）
9. **视觉自检协议（交付前必做）**：用 vision_analyze 逐张读图，固定五问——重叠？空白？底部完整？白边/截断？主要排版问题？2026-08-14 实测靠它抓到：CTA「搜」字被蓝块遮挡（line-height 1.1 < 雅黑字形 1.32em 跨行侵入）、封面 50% 空白、YAML 拼写疑点
10. 微软雅黑大标题 line-height 必须 ≥1.25（字形实际高度 1.32em，1.1 会跨行重叠）；flex 封面中 title 与 strip(margin-top:auto) 之间的空隙要主动填内容（chips 网格等），否则大面积空白
11. 英文术语（YAML/HITL/LLM/Agent）发布前 grep 自查拼写
12. **内容区禁止 `flex:1` 拉伸稀疏内容 + `space-between` 拉间距**（2026-08-14 实测：四卡 2×2 仅 3 行小字被拉高=大面积空白；三层组织图 space-between=层间空洞；流程 4 步 space-between=步距巨大）。正确姿势：内容区 `flex:1 + align-content:center`（网格整体居中、卡片保持自然高度）或固定紧凑间距；内容少的卡片要**加码填充**（emoji 图标层 + 标题 + 说明 + 底部典型场景/关键词 chips 层），而不是靠拉伸
13. 左右对比代码块不要 `min-height:100%` 拉满——代码块自然高度 + 外层 align-content:center 居中，行距 ≤1.6，否则整卡发虚空旷；左右代码行数对齐（如各 5 行）
14. 放大修复时要**成对改 CSS+HTML**（inline style 优先级高于 CSS 类，body 里 `style="font-size:60px"` 会压住 css_extra 的 .title 覆盖）；所有卡统一放大时先改 base 再逐卡覆盖；放大后立即重建+视觉复核，防止标题换行/卡片溢出（如 98px 标题在 928px 内容宽内极限约 9-10 个汉字）
15. **代码块/等宽内容必须按行宽预算核文案**（2026-08-14 实测：readMD 04 代码 54px 时「✓ 重复标题合并」等 7 字+前缀行 = 381px > 内容宽 324px → 静默换行断句，视觉复核才抓到）。预算公式：列内容宽 = (928 − 中列宽 − 列间距×2) / 2 − 代码块 padding×2；54px Consolas 下中文=1em、前缀符号+空格≈1.1em，单行安全字符数 = 内容宽/字号 − 1。放大字号后必须重算每行字符数，超了就缩短文案（「重复标题合并」→「标题去重」）
16. **多卡迭代时先脚本后视觉**：脚本量化（空白带 y 区间定位问题区块）→ 改 HTML/CSS → 重建 → 脚本确认 → 视觉复核语义。别一上来就 vision_analyze 盲猜（12 张卡每次视觉全量复核前先跑脚本，能砍掉 70% 的视觉往返）
17. **Edge headless 截图必须 `--force-device-scale-factor=1`**（2026-08-14 根因）：Windows 125% DPI 下视口被缩到 864px 裁切 1080px body，所有 absolute/flex 布局漂移皆源于此；修复后回归 flex 方案（详见 references/auto-pipeline.md §6）
18. **截图参数语法**：`--screenshot=路径` 必须等号语法 + `file:///` URL；`--window-size=1080,1544` 后 PIL 裁剪回 1080×1440（Edge UI 占 104px）
19. **模板封面空白带 = 行盒空白 + margin + space-between 段距累加**：内容不足时放大 li 字号（58→72→88→104）吃满空间，禁止靠拉伸间距；所有 flex 子项 `flex-shrink:0`；单条 li 时加「怎么用」CTA 区块 + chips 填充（详见 references/auto-pipeline.md §6）
20. **CTA 卡 head 长词溢出被视口裁切**（2026-08-15 实测）：`_card_html` 的 `.head` 96px 下「Natsummerance/skills」≈1065px 宽 > 1080 视口 → 右侧「lls」被 Edge 静默裁掉，CTA 显示「Natsummerance/ski」（vision 三次才抓到，像素检测右边界 1042 < 视口 1080 有 38px 幽灵间隙）。修复：cta 模式 head_font=80px（≈887px 整行放下，全仓库 cn 最长即 skills）；84px 仍超内容区 928px 导致末字符断行。校验法：大窗口 1600px 重渲染对比右边界 + vision 逐字符读 CTA 主标题。
21. **封面 gen_cover 硬切 headline 会切碎英文单词**（2026-08-15 实测）：`head_lines = headline[i:i+per_line]` 按固定字符数切，`llm-api-cost-monitoring`（23 字符）被切成 `llm-api-c / ost-monit / oring`（cost 切碎、可读性崩），视觉复核才发现。已修复：`_wrap_headline()` 优先按 `-` 边界断行（结果 `llm-api / cost / monitoring`），仅当 >3 行才回退硬切。教训：封面长英文名（≥15 字符）必须查 head HTML 断行点 + vision 逐字读标题；断行要按词边界，别按字符数。
22. **CTA head 字号必须按 BOLD 字形宽度估算**（2026-08-15 实测，Pitfall 20 方案对 agents/readMD 失效）：`font-weight:900` 渲染比 PIL regular 测宽 ~5-8%，@80px BOLD 实测 skills=902px（勉强放下）、agents=973px（拆行成 agen/ts）、readMD=1027px（超内容区 928px）。脚本 head_font 已统一降为 68px（readMD=873px ≤880px 安全线，全仓库 cn 一行放下）。教训：估算用 `msyhbd.ttc`（微软雅黑 Bold）测宽，安全线 = 内容区宽 − 5%；CTA 视觉复核必须逐字符读主标题（裁剪 head 区域放大 2× 再看）。
23. **clean_msg 截断会切碎单词**（2026-08-15 实测）：`m[:40]` 恰好把「首个多端兼容 Agent」第 40 字符（t）切掉 → 卡 3 与模板正文显示「Agen」。已修复：上限放宽 45 + 超长时回退到词边界（`——`/空格/`、`/`）再断 + 省略号。教训：commit message 清洗后的中文+英文串常在 38-45 字符之间，40 硬切必踩；生成后 grep 正文与卡内「…」前字符完整性。
