---
name: codex-bridge-debugging
description: "Use when codex bridge/watch 扫不到新会话时，按 Z 盘优先阶梯排查。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [codex, debugging, bridge, watch, sessions, z-drive]
    related_skills: [codex-bridge, codex-session-analysis]
---

# Codex Bridge / Watch 会话监控排查

## 何时使用
- `@codex` 新开对话完成后 **没有** 飞书提醒（watch 盲区）
- `@codex /switch --list` 看不到最近会话（bridge 盲区）
- 会话目录疑似迁移（Codex 更新后）、SESSIONS_ROOT 指向错误
- watch 首次扫描就报错 / state 对不上

## 架构认知（必须先懂）
- **codex_bridge.py**：发送端。`SESSIONS_ROOT` 指向 Codex 会话目录，用于 `/switch` 会话选择和上下文注入。
- **codex_watch.py**：监听端。定时扫描 `SESSIONS_ROOT` 下的 rollout JSONL，新会话完成 → 飞书提醒；`state/codex_notified.json` 记录已通知会话（key = **完整 UUID**，调试别用 8 位前缀查，会误判「未记录」）。

## 排查阶梯（按顺序，命中即停）
1. **先查 Z 盘（第一原则）**：`ls Z:/Natsumer/.codex/sessions/2026/<月>/<日>/` 找最新 rollout-*.jsonl。
   - Codex **2026-08-05 更新后数据目录整体迁移**：`C:\Users\<user>\.codex` → `Z:\Natsumer\.codex\`（sessions、config.toml、auth.json、skills 全在那）。
   - 这是历史最高频根因：脚本还在读 C 盘旧目录，新会话全在 Z 盘。
2. **验证 bridge 可见性**：`@codex /switch --list` 或直接 `python codex_bridge.py` 内部 scan。列表里有新会话 → 不是 bridge 问题。
3. **手动跑 watch 扫描**：`python codex_watch.py`（dry 模式），确认能扫到并打印新会话数。
4. **查 state**：`state/codex_notified.json`，确认新会话 UUID 是否已记录（幂等不重发机制）。

## 排查过的死路（别再走）
| 路径 | 结论 |
|---|---|
| `C:\Users\<user>\.codex\sessions\` | 只剩 08-04 前旧会话（迁移前） |
| `C:\Users\<user>\.codex\state_5.sqlite` | 同旧，停更 |
| `AppData\Local\Packages\OpenAI.Codex_*\` | Store 版根目录，**仅浏览器缓存**，无会话数据 |
| `.codex\logs_2.sqlite`（94MB） | 只有 `logs` 表，无会话数据 |
| `.codex\process_manager\chat_processes.json` | 仅进程/会话线索，非数据源 |
| 运行中的 codex.exe（Store app-server，Electron 壳） | 进程形态 ≠ 数据存储位置 |

## 修复模板
- bridge：`SESSIONS_ROOT = r"Z:\Natsumer\.codex\sessions"`（硬编码 + 迁移注释）
- watch：Z 盘优先、C 盘回退、保留 `CODEX_SESSIONS_ROOT` 环境变量覆盖
- 修完必须实测：扫描数、新会话提醒触发（exit=0=发送成功）、幂等不重发

## 验证清单
- [ ] watch 扫到的会话数 ≥ 最近实际会话数（含当天新开的）
- [ ] 最新 rollout 时间戳 = 最近一次会话时间
- [ ] `/switch` 列表能看到新会话
- [ ] state 中最新会话 UUID 已入档
- [ ] 飞书/微信提醒正常触发且不重复

## 教训
- **排查数据迁移先问/查 Z 盘**——本机 Codex 08-05 起数据在 Z 盘，脚本全要指向 `Z:\Natsumer\.codex\sessions`。
- state 的 key 是完整 UUID，调试用 8 位前缀查询会得到「未记录」的假象。
- Codex 更新常伴随目录迁移；「桥接脚本扫不到新会话」先假设是路径问题，再怀疑格式。
