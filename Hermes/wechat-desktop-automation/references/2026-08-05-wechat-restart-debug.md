# 2026-08-05 微信重启静默故障排查记录

## 症状
用户：「你现在怎么没有自动回复了」。cron 每分钟在跑但输出全部 silent（no_agent 空 stdout）。
手动跑 `python scripts/watch_eruting.py` 也无输出。cron 日志目录 `T:\programming\project\Hermes\cron\output\8961639cc834\`。

## 根因链（三层）
1. **微信重启**：WeChat.exe pid 32684→30764，主窗口 hwnd 23199872→20253098，窗口位置 (597,204)→(398,136)、尺寸 1365×960→910×640。脚本硬编码 PID/WID → get_window_state 拿不到元素 → snapshot 空 → 静默跳过（no_agent cron 空 stdout 无告警）。
2. 附加干扰：pid 30764 有**多个**顶层"微信"窗口——20253098 真主窗口（搜索 Edit + 输入框 Edit + ~44 ListItem）、2427850 通知弹窗（只有「忽略全部」按钮）。按"面积最大可见"选窗口会选到弹窗。
3. 坐标失效：窗口物理 910×640 时，cua-driver 截图仅 ~1045×735（DPI 1.148 逻辑像素），而输入框 UIA frame 逻辑坐标 (1053,998) → 本地 (596,842) 超出截图 → 像素点击/输入全部点到空白 → 发送静默失败。

## 排查工具
- 枚举窗口：python ctypes EnumWindows + GetWindowThreadProcessId + GetWindowTextW（标题=="微信"），GetWindowRect 拿尺寸/位置
- cua-driver：`C:\Users\Natsumer\AppData\Local\Programs\Cua\cua-driver\bin\cua-driver.exe call get_window_state {"pid":<pid>,"window_id":<hwnd>}`
- 窗口可见性：IsWindowVisible；恢复：ShowWindow(hwnd, 9) SW_RESTORE

## 关键实测数据
| 项 | 值 |
|---|---|
| 旧 pid/hwnd（重启前） | 32684 / 23199872，窗口 (597,204,1365×960) |
| 新 pid/hwnd（重启后） | 30764 / 20253098（主）、2427850（通知弹窗） |
| 输入框 UIA frame | (1053, 998, 909×95)，逻辑坐标，与截图同坐标系 |
| 输入框本地逻辑坐标 | (456, 794)（窗口物理 1365×960 @ (597,204) 时有效） |
| 物理 910×640 → 截图 | ~1045×735（ratio≈1.148）→ 输入框在截图外 |
| 物理 1365×960 → 截图 | 1568×1102（ratio≈1.148）→ 输入框在截图内 |
| MoveWindow | 手动调用生效（GetWindowRect 确认 1365×960）；脚本内偶发不生效 → 需确认循环 |

## 错误签名
- `[SEND-ERR] 验证失败: 视口内没有找到自己发的消息` → 消息根本没进输入框/没发出
- `[SEND-ERR] 验证失败: 最后一条自己消息「…」≠ 回复「…」` → 发了别的/没发成（注意过滤系统消息如「视频通话 通话时长 00:06」）
- cron 输出全 silent + 手动跑无输出 → 先查窗口发现（pid/hwnd 是否还活着）

## 修复落地（watch_eruting.py）
1. `find_wechat_window()`：EnumWindows 收集所有"微信"窗口 → `_is_main_window()` 用 UIA 特征（搜索 Edit + 宽 Edit）识别 → 可见优先、隐藏 ShowWindow 后再查、面积退路
2. `ensure_window()`：ShowWindow(SW_RESTORE) → MoveWindow(597,204,1365,960) 确认循环（≤3 次，GetWindowRect 校验，fallback SetWindowPos SWP_SHOWWINDOW）→ SetForegroundWindow；实测耗时 ~8.9s
3. `send_text`：type_text/press_key element_index background 优先，`effect in ("delivery_failed","unverifiable")` → foreground 像素降级
4. `main()`：ensure_window 失败 `print("[WARN] 找不到微信主窗口，跳过本轮")` 并 return——no_agent cron 必须有可见告警
5. 发送失败不写 reply_hash（成功才写），cron 下轮自动重试

## 同日另一 bug 记录（DeepSeek 推理 token 吃光预算）
19:44 事件：她连发 5 条，回复"okok"且未发出。根因① max_tokens=500 被推理吃光（completion 494 / reasoning 487 → 正文 7 token → 空 → 静默 None → 降级本地规则）；根因② 发送失败仍写 reply_hash + 旧检测 `effect != "delivery_failed"` 太松（cua-driver 出错时无 effect 字段被误判成功）。修法见 SKILL.md §3/§4。
