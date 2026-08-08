# 实战样例：赫尔佐格回顾展 12 篇（2026-08-07）

用户需求：每隔 1 小时发一篇小红书笔记，围绕赫尔佐格 + 4 部电影，内容互不重复，12 篇后暂停。

## 资产落位（本机可复用骨架）

- `scripts/xhs_campaign_content.json` — 12 槽位内容矩阵
- `scripts/xhs_campaign_publish.py` — 状态机发布脚本（直接可复用改槽位）
- `scripts/xhs_campaign_state.json` — 运行状态（index/results/retries，脚本自维护）
- `scripts/gen_xhs_covers.py` — PIL 封面生成（12 张 3:4 大字报）
- `output/herzog_campaign/covers/slotNN.png` + `output/herzog_campaign/stills/<slug>/<slug>_still_N.jpg`

## 内容设计要点

- 12 篇切面互不重复：篇1 总览导览 → 每部电影 2 篇（故事篇/思想或版本篇）→ 篇10 Kinski 篇 → 篇11 Bruno S. 篇 → 篇12 三大母题收尾。
- 事实准确：Bruno S. 演《卡斯帕尔·豪泽尔之谜》+《史楚锡流浪记》；Kinski 演《沃伊采克》+《诺斯费拉图》；两人合作 5 部电影（阿吉尔/诺斯费拉图/沃伊采克/陆上行舟/柯帛尼克船长）；毕希纳 23 岁去世。
- 争议细节软化：「赫尔佐格威胁开枪留人」写成「传说…多年后他自己都说不清」。
- 台词不引原文，转述大意（「关于雪崩一样的念头」），防记错被指摘。

## 验证与上线顺序

1. dry-run 循环 12/12 通过（标题 11-19 字、无敏感词、封面+剧照全部在位）。
2. 前台跑 `scripts/xhs_campaign_publish.py` → 第一篇真实发布成功（stdout `"published": true`，3 图上传、3 话题 popup 方式成功）。
3. 建 cron：`every 60m` / `no_agent=true` / `script=xhs_campaign_publish.py` / `deliver='origin'`；返回 `next_run_at = 创建+60min`，节奏对齐「每小时一篇」。
4. 之后 cron 每小时跑脚本；第 12 篇发完脚本静默，任务结束。

## 发布契约（xhs_publish.py，发布脚本判定依据）

- 成功：exit 0 + stdout `{"published": true, ...}`
- 失败：RuntimeError → stderr `{"error": ...}`
- `--dry-run`：校验标题字数/敏感词/图片存在性，不碰浏览器（12 篇约 4 秒）
- `--cover` 必填（首图）；`--image` 可多次；`--topic` 可多次
- body 换行保留（insertText 语义）；`--topic` 传入时自动剥离正文尾部话题行

## cron no_agent 投递语义（本方案依赖）

- 空 stdout → 静默不投递（发完 12 篇后的「暂停」效果）
- 非空 stdout → 原样投递给用户（每篇成功/失败摘要）
- 非零退出 → 错误告警（脚本正常路径恒 exit 0）
