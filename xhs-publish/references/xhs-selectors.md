# xhs-publish 小红书创作者中心 DOM 选择器参考（2026-08 实测）

> 实测环境：Edge 143 + creator.xiaohongshu.com（2026-08-07）。站点改版后按此清单排查。

## 发布页 `https://creator.xiaohongshu.com/publish/publish?source=official`

| 元素 | 选择器 | 说明 |
|---|---|---|
| 模式 tab | `.creator-tab` | 上传视频/上传图文/写长文/发播客；active 有 `active` class |
| 隐藏副本 tab | `.creator-tab` + style `left: -9999px` | 有 2 个「上传图文」，需排除 off-screen 副本 |
| 视频上传框 | `input[type=file].upload-input`（accept `.mp4,.mov,...`） | 视频模式 |
| 图片上传框 | `input[type=file].upload-input`（accept `.jpg,.jpeg,.png,.webp`） | 图文模式初始 |
| 隐藏图片 input | `input[type=file][accept*=".jpg"]` | 传完第一张后出现 2 个隐藏副本，取第一个 |
| 图片计数 | `div.status` 文本 `n/18` | 校验已上传张数 |
| 标题 | `input[placeholder="填写标题会有更多赞哦"]` | 需原生 setter + input/change 事件 |
| 正文编辑器 | `.tiptap.ProseMirror`（contenteditable） | `execCommand("insertText")`，`\n` 换段 |
| 话题按钮 | `.contentBtn.topic-btn` | 兜底：点击插入 `#` |
| 话题浮层 | `#creator-editor-topic-container .item` | 输入 `#话题` 后弹出，首项为精确匹配 |
| 话题成品 | `a.tiptap-topic`（文本 `#xxx[话题]#`） | 插入成功的标志 |
| 发布按钮 | `xhs-publish-btn` | **closed shadow DOM**，内容不可见；触发：`dispatchEvent(new CustomEvent("publish", {bubbles:true, composed:true}))` |
| 发布成功 | URL 含 `published=true` 或离开 `/publish/publish` | 轮询判断 |

## 笔记管理页 `https://creator.xiaohongshu.com/new/note-manager?source=official`

| 元素 | 选择器 | 说明 |
|---|---|---|
| 状态筛选 tab | `.tab-item`（文本：全部 n / 已发布 / 审核中 / 未通过） | 点筛选后列表刷新 |
| 笔记卡片 | `.note-card` | `data-impression` 内含 `noteId`（正则 `noteId\\":\\"([0-9a-f]+)`） |
| 笔记标题 | `.note-card__title` | 文本精确匹配 |
| 修改建议弹窗 | `.audit-modal` | 未通过时点「查看修改建议」后出现，内含原因 |

## 常见失效点（站点改版先查这里）

1. 发布页 URL 变了 → 检查 `/publish/publish` 与 `source=official` 参数。
2. 图文模式判断：优先看图片 input 是否存在，别依赖 `.creator-tab`（切图后会被移除）。
3. 发布按钮 shadow DOM：若 `querySelector("xhs-publish-btn")` 返回 null，检查自定义元素名是否改版。
4. 审核状态：卡片无显式状态文字，靠筛选 tab 判断；若改版可改用 tab URL 参数（如 `?status=auditing`）。
