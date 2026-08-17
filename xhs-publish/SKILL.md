---
name: xhs-publish
description: 发布小红书图文、上传多图、处理话题并查询审核状态。接收 github-promo-post 的 title/body/topics/6 张 1080×1440 JPG artifact；用户要求发小红书、发布 GitHub 项目推文或直接发布图文时使用。
---

# xhs-publish — 小红书全自动发布

驱动已登录的小红书创作者中心，自动完成「切图文 → 上传封面+多图 → 填标题/正文 → 加话题 → 点击发布 → 跟踪审核状态」全流程。封装为 Hermes 工具（`xhs_publish`）与本脚本，不改动 Hermes 主智能体。

## Codex artifact 接口

优先读取上游 `github-promo-post` 生成的 `artifacts/metadata.json`：

- `title`：平台标题，必须 ≤20 字；
- `body`：不含话题行、真实 URL 或站外引流；
- `topics`：5 个不带 `#` 的话题；
- `images`：6 个绝对路径，顺序固定为封面到 CTA；
- `version_state`：记录版本是正式 Release、更新线还是准备中。

发布前不得自行补造标题、正文、话题或图片；缺字段时返回缺失清单。

## 自动化发布流程（Codex）

1. 读取上游 `artifacts/metadata.json`，运行 `github-promo-post/scripts/validate_artifacts.py <artifacts>`；不通过就停止。
2. 用户明确要求发布后，单命令执行 `publish --bootstrap-edge --restart-edge`。它会关闭所有 Edge 窗口、**用默认已登录 profile** 启动 Edge 143 的 CDP；绝不创建 `--user-data-dir` 临时 profile。
3. `--restart-edge` 只用于 CDP 未就绪或需重建时。它会关闭用户 Edge，必须在用户已明确授权发布且已知晓影响时使用。
4. 脚本完成输入校验、登录检查、六图上传、正文/话题填充、发布和 URL 成功判定；随后按标题查询审核状态。只返回平台实际状态或真实错误。
5. 若 `version_state` 不是正式 Release，保留「更新线/准备中」措辞，不改成「已发布」。

优先使用原生 `xhs_publish` 工具；工具不可用时才调用本 skill 内的 `scripts/xhs_publish.py`。禁止使用 `--force` 绕过敏感词或平台校验。

## When to Use

- 用户说「发一篇小红书」「把这篇笔记发出去」「发布 XX 电影笔记」
- 需要给小红书笔记配多张图（封面 + 电影海报/剧照）
- 需要查询某篇笔记的审核状态（审核中/已发布/未通过）

## 前置条件（一次性）

1. **浏览器调试端口**：Edge 143+ 没有 chrome://inspect 开关，用启动参数：
   ```powershell
   $flag = "--remote-allow-origins=*"
   & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "--remote-debugging-port=9222" "--remote-allow-origins=*"
   ```
   若代理报「未连上」，先启动浏览器再调用工具；代理会自动重连。
2. **CDP 代理**：`Z:\Natsumer\.codex\skills\web-access\scripts\cdp-proxy.mjs` 需在 3456 端口运行。
   - Edge 143 兼容补丁：代理 `discoverChromePort()` 的 fallback 分支已改为从 `/json/version` 取真实 wsPath（裸 `/devtools/browser` 会 404）。web-access 更新可能覆盖此补丁，遇到 404 时重新打补丁。
3. **登录态**：浏览器已登录 `creator.xiaohongshu.com`（登录由用户手动完成，不要代输密码）。
4. **风险提示**（每次自动化前向用户展示）：
   > 部分站点对浏览器自动化操作检测严格，存在账号封禁风险。已内置防护措施但无法完全避免。

## 使用方法

### 方式 A：Hermes 工具（推荐）

`xhs_publish` 工具由 `plugins/xhs-publish` 插件注册到 hermes-cli toolset。
它属于非核心插件工具，默认被 Tool Search 渐进披露机制延迟加载：主 schema 里只有
`tool_search`/`tool_describe`/`tool_call` 三个桥接工具，当用户要求「发小红书」时先
`tool_search` 搜索到 `xhs_publish`，再用 `tool_call` 调用它（与 spotify/MCP 工具一致）。

调用示例：

```json
{"action": "publish", "title": "...", "body": "...", "cover": "C:/.../cover.png",
 "images": ["C:/.../poster1.jpg"], "topics": ["赫尔佐格", "中国电影资料馆"]}
```

- `action`：`publish`（全自动发布）/ `update`（编辑已发布笔记，需 `note_id`，改标题/正文/话题后重新发布）/ `draft`（只填充不发布）/ `status`（查状态，配 `note_title` 或 `note_id`）/ `login` / `tabs`
- `body` 不要包含话题行（`#xxx #yyy`），话题统一用 `topics` 传入，脚本会自动剥离正文尾部纯话题行。
- 标题硬限制 **≤20 字（含标点）**，超出会被平台拦截（toast「标题最多输入20字哦~」）。

### 方式 B：直接命令行（标准 artifact）

```powershell
$a = 'C:/.../artifacts'
python C:/.../github-promo-post/scripts/validate_artifacts.py $a
python scripts\xhs_publish.py publish --bootstrap-edge --restart-edge `
  --title-file "$a/title.txt" --body-file "$a/body.txt" `
  --cover "$a/images/xhs-01-cover.jpg" `
  --image "$a/images/xhs-02-pain.jpg" --image "$a/images/xhs-03-fast.jpg" `
  --image "$a/images/xhs-04-fix.jpg" --image "$a/images/xhs-05-convert.jpg" --image "$a/images/xhs-06-cta.jpg" `
  --topic "GitHub" --topic "开源项目" --topic "程序员" --topic "效率工具" --topic "Markdown"
python scripts\xhs_publish.py status --note-title "标题"
```

`bootstrap` 可独立诊断：`python scripts\xhs_publish.py bootstrap`；若端口未就绪，且用户已授权关闭 Edge，执行 `bootstrap --restart-edge`。CDP 代理保持在 `3456`，代理若在 Edge 重启前已运行会自动重连。

常用参数：`--title-file/--body-file`（长文本用文件避免转义）、`--no-publish`（草稿模式）、`--dry-run`（只校验）、`--force`（放行敏感词，不建议）、`status --note-title "标题"`。

编辑已发布笔记（改文案后重发，审核会重新走一遍）：

```powershell
python scripts\xhs_publish.py update --note-id 6a74b839000000003303782b `
  --title "新标题（≤20字）" --body-file body_v2.txt `
  --topic "赫尔佐格" --topic "中国电影资料馆"
```

- update 会打开 `/publish/update?id=<noteId>`，清空旧正文 → 写新标题/正文 → 重新添加话题 → 点击发布。
- **仅配图模式**：`update` 也可只追加图片不改文案——不给 `--title/--body`，只给 `--note-id` + 一个或多个 `--image`，脚本保留原标题/正文/话题，只上传图片后点发布（审核会重新走一遍）。
- 成功后页面跳转（发布页跳 `published=true`，编辑页跳 `editSuccess` 或笔记管理页），脚本据此判定；发布被拦截（如标题超长）会读取校验 toast 并快速报错。

### 方式 C：剧照搜索→下载→配图（`xhs_enrich_stills` 工具）

Hermes 工具 `xhs_enrich_stills`（同插件注册，toolset=hermes-cli）：从 TMDB 按社区评分下载高清剧照（原图，最高 4K），可选直接追加到已发布笔记。

```json
{"tmdb_id": 6404, "count": 6, "min_width": 1280,
 "out_dir": "T:/.../stills", "note_id": "6a7513720000000033008657"}
```

- `slug` 内置映射：`kaspar_hauser`(11710) / `stroszek`(11698) / `woyzeck`(10319) / `nosferatu`(6404)；或直接给 `tmdb_id`。注意沃伊采克 1979 版是 **10319**（1368217 不是赫尔佐格版）。
- 选图逻辑：TMDB backdrops 页 `?image_sort=rating.desc`（社区评分最高在前）→ 按 `--min-width` 过滤 → 取前 `--count` 张 original 原图。
- 给 `note_id` 后自动走 `update` 的仅配图模式（不改文案）。`no_publish: true` 可停在发布前人工核对。
- 剧照版权归原出品方/发行方，公开笔记建议注明「剧照版权归出品方」；无版权风险的封面仍用自制的 `covers/cover_*.png`。

## 内容红线（发布前必查）

**站外引流是硬红线，除字面词外，隐含的「另一平台」表述同样违规。** 平台判定「推广第三方平台」包括：

1. 引导他人前往其他平台搜索/浏览（`公众号`、`微信`、`加我V`、`闲鱼`、`抖音`、`B站` 等字面词）；
2. 通过种草/科普/教程/测评方式为其他平台宣传（例如「深度长文放公众号」「完整版在别处」这类暗示另一平台的对比表述——哪怕没写平台名，也会被判文本违规）；
3. 福利红包/专属优惠诱导跳转、推荐其他平台付费内容。

- 公开正文/标题**禁止**出现：`公众号`、`微信`、`闲鱼`、`咸鱼`、`转卖`、`出票`、`转让`、`售票`、`二维码`、`淘口令`、`淘宝` 等。脚本默认拦截，命中会报错并列出词。
- **隐含表述也禁止**：不要写「这几部我会在别处写长文」「完整版在另一平台」；想表达内容规划，改成站内承诺（如「这几部我会在放映前一部一部细讲」）。
- 实测：正文含「公众号」→ 审核失败「笔记存在推广第三方平台的内容」。**修掉后必须重新走发布流程**（`update --note-id` 编辑页改文案 → 再次点发布），仅改前端展示不生效。
- 转票/承接信息只走私信与闲鱼（见 `ops/private_dm.md`），绝不进正文、标题、封面、评论区置顶。

## 内容准备建议（电影推广场景）

- 封面：`output/herzog_campaign/covers/cover_*.png`（3:4 文字大字报，非剧照，无版权风险）。
- 配图：`output/herzog_campaign/stills/` 已含官方海报（`*_poster.jpg`，Wikipedia REST 下载）与高清剧照（`*_still_*.jpg`，TMDB 原图，2026-08-07 按社区评分+分辨率筛选下载，已配到四篇笔记）；新片可用 `xhs_enrich_stills` 工具现抓。
- 每篇发布前跑 `dbs-content` 五维诊断 + 标题用 `dbs-xhs-title` 公式候选。

### 高浏览笔记风格模板（实测要点）

**标题**：前 8 字定生死；≤20 字含标点。三种高点击型：数字型（地点/数字/影展，如「8月北京最值得蹲的影展：赫尔佐格全回顾」，公式 #26）、痛点/反常识型（如「17年没见过太阳的人，戳穿了『正常』」，公式 #24+#1）、好奇缺口型（如「看完这部，你会怀疑『正常』这回事」，公式 #12）。用 `dbs-xhs-title` 出 5-8 个候选并标注公式编号，再定稿。

**首图**：大字报文字 ≤15 字，信息流停留 0.5-1 秒；电影类常用拼贴多图/实景剧照风。

**正文结构**：开头一句话点明价值 → 分点阐述（`1️⃣2️⃣3️⃣` 短行 + 换行，替代加粗）→ 结尾总结 + 提问引导互动（评论区聊什么）。结构化才有收藏率；结尾提问直接给「评论区聊聊」话题。

**人味 > 正确**：避免 AI 腔（空洞排比、连续祈使句「请你记住」「真相是」）；句子长短错落，允许口语化；数据/引语要具体（年份、片名、导演原话）。

## Common Pitfalls

0. **Edge 后台预加载实例抢占 profile → 调试端口静默失效（2026-08-14 实证）**：Windows 上 Edge 常驻 `--no-startup-window` 后台预加载实例，会抢占默认 profile 锁；此时再启动 `msedge.exe --remote-debugging-port=9222` 参数会被转交给现有实例且**被忽略**，9222 无响应、发布脚本报「请求失败 /targets: WinError 10061 目标计算机积极拒绝」。修复：先 `taskkill -F -IM msedge.exe` 杀光全部 Edge（含预加载），再用默认 profile 启动调试实例（登录态在默认 profile 里，保留）。排查顺序：`curl 127.0.0.1:9222/json/version` → `curl 127.0.0.1:3456/` → `xhs_publish.py login`。
1. **发布按钮是 closed shadow DOM**：`xhs-publish-btn` 内部内容查询不到，普通点击无效。正确触发：
   `document.querySelector("xhs-publish-btn").dispatchEvent(new CustomEvent("publish", {bubbles:true, composed:true}))`
2. **切换图文后 `.creator-tab` 会从 DOM 移除**：判断是否图文模式要查图片 input（`input[type=file]` accept 含 `.jpg`），不能只看 tab。
3. **多图上传**：第一张用 `input[type=file].upload-input`；后续图该 input 隐藏，改用 `input[type=file][accept*=".jpg"]`（DOM 里有 2 个隐藏副本，取第一个）。用 `div.status`（`n/18`）校验张数。
4. **标题**：必须用 `HTMLInputElement.prototype.value` 的原生 setter + `input`/`change` 事件，直接赋值 Vue 不认。
5. **正文**：`.tiptap.ProseMirror` contenteditable，用 `document.execCommand("insertText")`，`\n` 表示换段。
6. **话题**：正文输入 `#话题名` 会弹 `#creator-editor-topic-container` 浮层，点第一个 `.item`（精确匹配项在首位）即插入 `<a class="tiptap-topic">`。
7. **话题重复**：xhs_note.md 正文尾部自带一行 `#话题` 纯文本，脚本已自动剥离；不要手工再拼一遍。
8. **审核状态**：笔记管理页（`/new/note-manager`）卡片不直接显示状态，用「已发布/审核中/未通过」筛选 tab 判断笔记归属；未通过时点「查看修改建议」读 `.audit-modal` 原因。
9. **登录跳转**：若发布页跳到 `login/passport`，工具会报「未登录」，让用户手动登录后重试。
10. **Node/代理环境**：`check-deps.mjs` 需 Node 22+；`cdp-proxy.mjs` 用 `node scripts/cdp-proxy.mjs` 启动。
11. **标题 ≤20 字**：超长时发布被拦截并弹「标题最多输入20字哦~」。更新笔记时先写标题再检查字数。
12. **编辑已发布笔记**：正文编辑器要先清空再写入（`JS_CLEAR_BODY`），否则新正文会追加到旧正文后面；旧话题会随清空一起删除，需重新 `--topic` 添加。
13. **发布成功判定**：发布页成功后 URL 带 `published=true` 或跳走；编辑页成功后跳 `editSuccess` 或笔记管理页。`JS_PUBLISH_STATE` 同时检测校验失败 toast（标题超长/不能为空）快速报错，避免空等。

## Verification Checklist

- [ ] `python xhs_publish.py login` → `{"loggedIn": true}`
- [ ] `draft` 模式预览：标题正确、`div.status` 张数 = 封面+配图数、`a.tiptap-topic` 数量 = topics 数、正文无话题行
- [ ] 发布后 `status --note-title "<标题>"` → `审核中`（或 `已发布`）
- [ ] 改已发布笔记：`update --note-id <noteId> --title "≤20字" --body-file ...` → 页面跳 `editSuccess` → `status` 复查
- [ ] 未通过时读取 `.audit-modal` 原因，`update` 修改正文后重发
- [ ] 公开内容无敏感词（`公众号/微信/闲鱼/转卖/出票/转让`）
- [ ] 发布后按 `ops/private_dm.md` 补置顶评论与私信承接

