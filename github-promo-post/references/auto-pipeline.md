# 自动推送链路操作手册（auto-pipeline）

> 四库（readMD/doAI/skills/agents）GitHub 更新 → 小红书推文自动发布。
> 目标：**下次直接半自动化执行，不重试**。所有命令可直接复制。

## 0. 两阶段流水线（2026-08-14 19:00 定案，用户要求「不要提前写好」）

```
写作 cron c67f4a093b92（:20/:50 触发 = 推送前 10 分钟, agent 模式, 加载 github-promo-post）
  ├─ python scripts/github_updates.py       检测四库新 commit → 入队
  ├─ 无更新 → 只回复「无更新」，结束
  ├─ 有更新 → python scripts/xhs_github_publish.py --dry-run  生成模板正文+封面（内置像素校验）
  ├─ LLM 精细重写正文（T3 更新公告 / T4 单条安利，覆盖同一 .txt）
  ├─ vision_analyze 复核封面（只复核不改图，布局脚本已内置修复）
  └─ 写 scripts/xhs_github_ready.json：{id,repo,title,body_path,cover_path,topics,created_at}
       → 回复「✅ 已写好《标题》，10 分钟后自动推送」

发布 cron 3972814137ba（:00/:30 触发, no_agent 零 token, script=publish_ready.py）
  ├─ 无 ready → 静默（空 stdout，cron 不投递）
  ├─ 有 ready → xhs_publish.py publish（--title/--body-file/--cover/--topic）
  ├─ 成功 → 删 ready + 队列条目移 done → stdout「✅ 已发布《标题》」投递
  └─ 失败 → retries+1；≥3 次删 ready 告警；<3 次保留下周期重试（静默）
```

- 用户硬要求：**内容不提前写好**——每次推送前 10 分钟现场检测+现场写+校验，到点推。
- 旧单阶段 cron 94f34ec49e39（检测→模板→即发）已 **pause**（防双发），保留代码不用。
- 写作 cron 是 agent 模式（LLM 写文），发布 cron 是 no_agent（零 token）。

---

## 1. 架构总览（零 token 设计）

```
cron 94f34ec49e39（每 30 分钟, no_agent 模式, 零 token）
  └─ python scripts/xhs_github_cycle.py
       ├─ ① github_updates.py     检测：GitHub API 拉四库 commits，对比 state.json last_sha
       │                           新增 → 写入 queue.json pending（skills/agents 按新增文件路径识别条目名）
       │                           首跑只记基线不入队（防历史误发）
       └─ ② xhs_github_publish.py 发布：取 pending 一篇 → T3/T4 模板推文+封面（范式校验）→ xhs_publish 发布
                                   无更新/队列空 → 静默（无任何输出）
```

设计原则：cron 用 `no_agent=true`（纯脚本，不烧 LLM token）；定时任务只用 T3（大项目更新公告）/T4（单条目安利）模板；人工/触发语场景才用全 6 类型精细创作。

## 2. 文件清单与职责

| 文件 | 职责 |
|---|---|
| `scripts/github_updates.py` | 四库检测：GET /repos/Natsummerance/{repo}/commits，对比 `scripts/xhs_github_state.json` 的 last_sha；新 commit 入队 `scripts/xhs_github_queue.json` |
| `scripts/xhs_github_publish.py` | 队列状态机 + T3/T4 模板推文生成 + 封面生成（Edge headless 截图+裁剪）+ validate_poster 校验钩子 + 调 xhs_publish 发布 |
| `scripts/xhs_github_cycle.py` | cron 入口 wrapper：检测→入队→发布一篇 |
| `scripts/xhs_github_state.json` | 四库 last_sha 基线（首跑自动建立） |
| `scripts/xhs_github_queue.json` | `{"pending":[...], "done":[...]}`，条目 `{id, repo, kind: project|item, items:[条目名], commits:[...], retries, status}` |
| `output/github_promo/auto/<repo>/` | 封面 png + html 输出 |

依赖：xhs-publish 技能的 `xhs_publish.py`（发布器，支持 `--body-file`）；validate_poster.py（范式校验）。

## 3. 运行方式（命令照抄）

```bash
cd T:/programming/project/Hermes

# 手动检测（只检测入队，不发布）——触发语第一步
python scripts/github_updates.py

# 手动发布一篇（--dry-run 只生成不发布，封面+推文进 auto/ 目录）
python scripts/xhs_github_publish.py --dry-run
python scripts/xhs_github_publish.py          # 真实发布

# 完整周期（cron 同款）
python scripts/xhs_github_cycle.py            # 队列空/无更新 → 静默，EXIT 0

# 手动入队测试条目（格式）
python -c "
import json
q = json.load(open('scripts/xhs_github_queue.json', encoding='utf-8'))
q['pending'].append({'id':'test-1','repo':'readMD','kind':'project','items':[],'commits':[{'message':'测试更新点','date':'2026-08-14T00:00:00Z'}],'retries':0,'status':'pending'})
open('scripts/xhs_github_queue.json','w',encoding='utf-8').write(json.dumps(q, ensure_ascii=False, indent=2))
"
```

## 4. 队列状态机

- 条目生命周期：`pending` → 发布成功 → `done`（从 pending 移走，追加进 done）；发布失败 retries+1，≥3 次移出 pending 并告警
- **dry-run 不移除队列**（只生成不消费）——测试多个场景时手动 pop：`q['pending'].pop(0)`
- 测试完必须清队列（`q['pending']=[]; q['done']=[]`）+ 删 auto/ 下测试产物，防污染正式发布
- 触发语/人工场景：检测 → 精细创作（poster-types.md 全类型）→ 发布后**手动清 state 或确认已入队消费**

## 5. T3/T4 模板推文结构

- **T3 更新公告**（大项目有更新）：标题「XX 更新了」+ 概要段（不了解项目的人能看懂）+ 本次更新点（≤4 条 commit）+ 老/新用户分流话术
- **T4 单条安利**（skills/agents 新条目）：标题「新技能上线：<条目名>」+ 一句话定位 + 亮点 2-3 条 + 「怎么用」CTA
- 话题标签 4 个：#GitHub #开源 #程序员 + 项目相关（#效率工具/#AI编程/#多Agent）
- 正文红线同 Step 6（禁引流词、≤1000 字）；封面 CTA 用「GitHub 搜 Natsummerance/<repo>」

## 6. 封面生成硬规则（血泪教训，全部在脚本内置）

| # | 规则 | 原因 |
|---|---|---|
| 1 | **Edge headless 必须 `--force-device-scale-factor=1`** | Windows 125% DPI 缩放：CSS 视口被缩到 864px 裁切 1080px body——**所有** absolute/flex 漂移的根因；修复后布局全部回归正常 |
| 2 | 截图 `--screenshot=路径` **等号语法** + `file:///` URL | 空格语法/裸路径会静默失败或截空白 |
| 3 | `--window-size=1080,1544` → PIL 裁剪回 1080×1440 | Edge UI 占 104px，视口=window-size-104；raw 图含 UI 会稀释像素级校验 |
| 4 | 所有 flex 子项 `flex-shrink:0` | uptitle 曾被压缩到 5px |
| 5 | foot `position:absolute;bottom:60px` | 恒定贴底，不参与 space-between 均分 |
| 6 | 空白带 = 行盒空白 + margin + space-between 段距 三者累加 | 校验器逐行扫非背景像素；space-between 会把这些累加成 >120px 空白带 FAIL |
| 7 | 内容不足 → **放大 li 字号吃满空间**（58→72→88→104 按条数升档），不是靠 flex 拉伸 | 单条 li 时 space-between 均分每段 157px>120px 阈值 |
| 8 | 单条 li 时加「怎么用」CTA 区块 + date 38px 放大 | 内容填充，吸收剩余空间 |
| 9 | 4 个话题 chips 固定区块（每图 +~120px 内容） | 填充 + 小红书风格 |
| 10 | line-height 收紧 1.1-1.4；rule 与 sub 之间 margin 48/40 | 行盒空白是空白带主要来源；72/64 会让 sub↔rule 间隙 153px |
| 11 | **纯 flow + Python 动态间隙方案已被证伪**（渲染 90px vs 计算 8px 错位） | DPI 修复后回归 flex + space-between，勿回退 |

## 7. 验证协议（发布前必走）

1. **先脚本后视觉**：validate_poster.py 像素校验（尺寸 1080×1440 / 四边无白边 / coverage ≥5% / **blank_band ≤120px** / bottom_gap ≤90px / top ≤220px / 不出血）→ 全 PASS 才进视觉
2. **视觉五问**（vision_analyze 逐张）：重叠？空白？底部完整？白边/截断？主要排版问题？
3. 空白带 FAIL 时修复闭环：脚本输出最大空白带 y 区间 → 定位对应区块 → 放大字号/padding 或加内容行 → 重建 → 复跑脚本 → 视觉确认
4. 四场景回归清单：单条 commit（T3）/ 多条 commit（T3）/ 短条目名（T4）/ 长条目名换行（T4，如 fullstack-engineer）

## 8. 下次半自动化操作清单（直接照做）

**触发语「帮我把GitHub更新发小红书」：**
1. `python scripts/github_updates.py` → 看是否入队
2. 无新 → 回复「没有新更新」
3. 有新 → 读 queue.json 拿条目 + 素材卡 references/projects.md → 按 poster-types.md 选型精细创作推文（非模板）
4. 生成封面（build_v3.py 同款链路：HTML→Edge 截图→PIL 裁剪→validate_poster）→ 视觉五问
5. `xhs_publish --body-file` 发布 → 汇报

**布局/样式改动：**
1. 只改 xhs_github_publish.py 的 CSS/HTML 段 + 高度估算
2. 手动入队测试条目 → `--dry-run` 生成 → validate_poster → vision_analyze
3. 四场景回归 → 清队列 → 完成

## 9. 已踩坑时间线（2026-08-14 复盘）

padding 96→80→70→60 无效（raw 1048×1336 resize 稀释改动）→ 视口实为 1080×1336 → window-size 1544 方案 → 布局仍漂移 → 纯 flow 计算间隙仍错位（90 vs 8px）→ **定位 DPI 根因** → 回归 flex + absolute foot + flex-shrink:0 → 单条 li 空白带 157px → 字号升档 + howto CTA + date 放大 → chips 区块 → 全场景通过。
