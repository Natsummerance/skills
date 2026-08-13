---
name: codex-bridge
description: 飞书/微信遥控本机 Codex 的桥接技能。当用户消息以 "@codex"（后面不加冒号，可以是空格或不加任何符号）开头时，必须使用本技能：把 @codex 之后的内容交给本机 Codex 桌面会话执行（注入到用户正在使用的 Codex 窗口），并把 Codex 的输出原样作为回复。"/switch" 用于切换目标 Codex 会话窗口。适用于用户明确想用 Codex（而不是 Hermes 自身）来处理任务的情况。
metadata:
  short-description: 转发 @codex 消息到本机 Codex 会话窗口
---

# Codex Bridge

当收到以 `@codex` 开头（无冒号）的消息时：

1. 提取 `@codex` 之后的内容，去掉首尾空白（允许 `@codex：` 旧格式兼容）。如果为空，回复使用说明。
2. 用终端工具执行（内容作为参数，注意转义双引号）：

   ```powershell
   python "HERMES_HOME\scripts\codex_bridge.py" "<内容>"
   ```

   若内容包含换行或引号，改用 stdin 方式：

   ```powershell
   "<内容>" | python "HERMES_HOME\scripts\codex_bridge.py"
   ```

3. **默认 fire-and-forget（2026-08-05 起）**：脚本只负责把任务注入 Codex 会话并确认发送成功，**不等待执行、绝不超时终止**。脚本返回「✅ 已发送给 Codex → 会话…」即成功，把该确认**原样**作为回复发送即可；Codex 执行结果由用户自己的监听（codex_watch）汇报。
4. 想同步等待执行结果时用 `@codex --wait <内容>`（无限等待，不超时终止）；脚本输出以「（」开头 = 启动失败/异常——如实转告用户。

## 切换 Codex 会话窗口

- `@codex /switch` 或 `@codex /switch --list`：列出最近的 Codex 会话（ID + 标题）。
- `@codex /switch <会话ID或标题片段>`：切换到目标会话。匹配到多个时脚本会列出候选，让用户补充更精确的关键词。
- 切换后，之后的 `@codex <内容>` 会注入到新会话窗口。

## 注意

- 每条 `@codex` 消息都会消耗 Codex 的模型 token（当前会话上下文较大，可能几十万到上百万 token），比直接问 Hermes 慢且贵，除非用户明确要 Codex 处理，否则不要主动建议使用。
- 不要在其他情况下使用本技能。

## 已知坑：桥接创建的会话不出现在桌面侧边栏

- 现象：通过 `codex exec resume` 注入/新建的会话，Codex 桌面端侧边栏不显示。
- 根因（2026-08-04 实测）：会话来源标记为 `source="exec"`，桌面端 `thread/list` 默认过滤（`sourceKinds=[]`）只返回"交互式来源"（vscode 等），`exec` 被排除。
- 修复：把 `C:\Users\<user>\.codex\state_5.sqlite` 中该会话 `source` 字段从 `exec` 改为 `vscode`（改前先备份：复制为 `.bak-<日期>`），然后重启 Codex 桌面应用（或收起/展开侧边栏、切走再切回）。已验证：桌面端运行中不会回写该字段。
- 复发风险：应用升级/状态库全量扫描可能从 rollout 元数据重新推导回 `exec`，届时同样方法再改（或同步改 rollout 的 session_meta）。
- 相关文件：会话文件在 `Z:\<user>\.codex\sessions\2026\<月>\<日>\rollout-<时间戳>-<session_id>.jsonl`（**2026-08-05 Codex 更新后数据目录迁到 Z 盘**；C 盘 `C:\Users\<user>\.codex` 只剩 08-04 前旧会话）。codex_bridge.py 与 codex_watch.py 的 `SESSIONS_ROOT` 都已指向 Z 盘。若 Codex 再更新导致目录变化：先 `@codex /switch --list` 验证能否看到新会话，否则同步修改两个脚本的 SESSIONS_ROOT。
- 排查此类问题消耗大，建议先 `@codex /switch` 到小会话再处理。
