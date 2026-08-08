---
name: scheduled-social-campaign
description: 定时批量发布社交内容时使用（每小时一篇、内容不重复、N篇后暂停）。
---

# Scheduled Social Campaign（零 token 批量定时发布）

用户要求「每隔 1 小时发布一篇笔记，内容互不重复，发 12 篇后暂停」这类任务的标准架构：
**一次性预生成全部内容（一次 LLM 成本）→ 状态机发布脚本（零 token）→ no_agent cron 定时驱动 → 发完自动静默。**

## 架构

```
scripts/<campaign>_content.json    # N 个内容槽位（一次性创作）
scripts/<campaign>_publish.py      # 状态机发布脚本（每次运行只处理一个槽位）
scripts/<campaign>_state.json      # 运行状态（脚本自维护）
cron (no_agent=true)               # 定时驱动脚本，stdout 投递给用户
```

## 步骤

1. **创作内容矩阵**：写 `<campaign>_content.json`，每个槽位：
   ```json
   {"id": 1, "title": "标题(≤20字含标点)", "body": "正文\n支持换行",
    "topics": ["话题1","话题2"], "cover": "relative/path.png",
    "images": ["relative/path.jpg"], "cover_text": "封面大字", "cover_sub": "封面小字"}
   ```
   每篇取不同切面保证「内容不重复」；标题 ≤20 字（小红书硬限制，中文标点算 1 字）。
   事实性内容（年份/演员/作品）必须准确；拿不准的台词/传闻用转述或「传说」软化，不引原文。

2. **全量 dry-run 校验**（发布前必做，不操作浏览器）：循环调用发布脚本 `publish --dry-run`，
   检查标题字数/敏感词/图片存在。12 篇约 4 秒，全部通过才上线。

3. **写状态机发布脚本**（骨架参考 scripts/xhs_campaign_publish.py）：
   - 读 state：`{"index": N, "results": [...], "retries": {...}}`
   - `index >= total` → **print 空串 + exit 0**（no_agent cron 空 stdout = 静默不投递）
   - 成功判定：子进程 exit 0 且 stdout 含 `"published": true`（xhs_publish.py 契约）
   - 失败：retries[idx]+1，连续 3 次失败才跳过并告警；否则留待下个 tick 重试
   - 每篇成功/跳过都追加 results 并持久化 state.json（状态文件是唯一真相，cron 补跑不会重复发）

4. **本地生成封面（零版权风险）**：PIL 3:4 大字报（1080x1440），Windows 字体
   `C:/Windows/Fonts/msyhbd.ttc`（粗体）+ `msyh.ttc`（常规）；深色底 + 米白大字 + 金色小字；
   中文按字符数折行（每行 ≤7 字）。参考 scripts/gen_xhs_covers.py。

5. **配图（可选）**：xhs-publish 技能 scripts/enrich_stills.py 可从 TMDB 抓高清剧照
   （`--slug <slug> --count 4 --min-width 1280 --out-dir <dir>`，无需 API key，网页抓取）。

6. **建 no_agent cron**：`schedule='every 1h'`，`no_agent=true`，`script=<campaign>_publish.py`，`deliver='origin'`。

7. **先手动发第一篇验证全链路**（cron 创建**前**跑一次脚本），确认 `published: true` 后建 cron。

## Pitfalls

- **cron `every 1h` 语义**：next_run = 创建时刻 + 60min（不是立即）。第一篇手动发、再建 cron，节奏正好对齐。
- **建 cron 后不要手动 run**：会立即多发一篇（间隔 0 小时）。
- **no_agent cron 投递语义**：空 stdout = 静默；非空 stdout = 原样投递；非零退出 = 错误告警。发完的「暂停」= 脚本静默输出，cron 保持空转零成本。
- **成功判定必须解析 stdout JSON**：`"published": true`（失败时脚本 raise RuntimeError 到 stderr）。
- **正文换行**：subprocess 以 list 传参，body 里的 `\n` 保留为换段（insertText 语义）。
- **调度脚本与 cron 同 tick 竞态**：第一篇手动触发必须在建 cron 之前完成，否则同一小时可能发两篇。

## 参考
- references/herzog-campaign-example.md — 赫尔佐格回顾展 12 篇实战（槽位设计、脚本逻辑、cron 参数、发布契约）
