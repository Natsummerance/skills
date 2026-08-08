---
name: wechat-desktop-automation
description: Use when operating the WeChat auto-reply bot watch_eruting.
---

# WeChat 桌面客户端自动化（自动回复机器人运维）

## 何时使用
- 维护/调试微信自动回复机器人（`watch_eruting.py` 双副本）
- **⚠ 铁律：动手调试前必须先加载本技能**——本技能已沉淀完整链路（真实鼠标+键盘+SetClipboardData）与全部已知坑。2026-08-05 曾因未加载技能重新摸索数小时（截图灰、PostMessage、cua-driver 点击……全是被本技能记录过的死路），被用户点名「你看看你之前沉淀的skill」。先看本技能再动手。
- 症状：微信重启后 bot 不回复、cron 静默、消息发不出去、找不到窗口
- 需要改发送链路、窗口识别、LLM 参数、重试逻辑
- 本技能管运维/技术侧；回复人格与风格样本在 `eruting-reply-style`（user-owned）

## 关键文件（双副本必须同步）
- `T:\programming\project\Hermes\wechat_bot\watch_eruting.py` — 源文件（Codex 常改这里）
- `T:\programming\project\Hermes\scripts\watch_eruting.py` — cron 实际运行副本
- **铁律：每次改完源文件必须 `cp wechat_bot/watch_eruting.py scripts/watch_eruting.py`**（Codex 只改 wechat_bot/ 导致 cron 跑旧代码——踩过的坑）
- cron job_id=8961639cc834（every 1m、no_agent）；暂停用 `cronjob pause 8961639cc834`；日志在 `cron/output/8961639cc834/`

## 1. 窗口发现：禁止硬编码 pid/hwnd（微信重启必失效）
微信重启 → pid/hwnd 全变 → 硬编码窗口全废 → snapshot 空 → cron 静默跳过 → 用户以为"没有自动回复"。
- EnumWindows 遍历标题 == "微信" 的顶层窗口（**可能有多个**：真主窗口 + 通知弹窗）
- **主窗口 UIA 特征**：含 label=="搜索" 的 Edit + 一个宽度 >300 的 Edit（聊天输入框）
- 通知弹窗（如只含「忽略全部」按钮）会干扰——按"面积最大可见"选窗口会选错到弹窗
- 顺序：先查可见窗口（快）；找不到再 ShowWindow(SW_RESTORE=9) 恢复隐藏的逐个查；最后面积退路
- **no_agent cron 静默 = 无输出 = 无告警**；脚本找不到窗口必须 `print("[WARN] ...")` 而非静默 return，否则故障不可见

## 2. 坐标体系：UIA frame 是「虚拟画布坐标」，不是截图坐标（2026-08-05 实测纠正）
- **微信 4.0 的 UIA frame 是内部虚拟画布坐标，不能直接当截图/视口坐标用**。实测：截图只有 1567×888（逻辑），但聊天输入框 frame 却是 (1053,1505,2130,95)——宽 2130 超过截图宽，y=1505 超出截图高；聊天消息 ListItem 的 y 甚至是负数（-1290 起）。**frame 与截图像素之间没有 1:1 映射**，直接拿 frame 坐标点击必歪。
- 旧结论「输入框本地坐标固定 (456,794)」只在窗口恰好为特定尺寸/布局时成立；窗口重启、滚动位置变化、尺寸变化后全部失效。正确姿势 = 每次运行实时推导布局（get_wechat_layout），不要记固定坐标。
- **验证画面优先用 cua-driver 官方截图**：`get_window_state` 响应里的 `screenshot_png_b64`（base64 PNG，逻辑像素）。**不要用 PrintWindow/GetWindowDC 自截**——微信是 GPU 渲染，PrintWindow 返回陈旧帧（两次截图 diff=0 是假象，实际窗口已变化）。之前多轮「滚动没生效」判断全是 PrintWindow 骗的。
- **⚠ 三种截图源可能互相矛盾（2026-08-05 实测）**：同一时刻 cua-driver 官方截图 = 深灰(168)、BitBlt 屏幕 DC = 浅灰(245)、PrintWindow = 旧帧。GPU 渲染窗口没有哪个截图源保证真实。**判活第一性原理 = 交互反馈**：键盘输入（Ctrl+F 搜索、粘贴、Enter）后截图 diff 明显变化 ⇒ 微信活着且键盘路径通；此时画面灰可能是截图 API 拿不到 GPU 表面，别把「灰色」当故障结论。实在要确认真实画面，发 BitBlt 截图给用户看。
- **图像分析不依赖视觉模型**：解码 b64 → PIL → 扫微信绿发送按钮（#07C160，G>110 且 G>R+40 且 G>B+40）定位输入区；分区平均色判断界面状态（正常聊天区=白底；灰色 139 或大片纯黑 = 页面不对/内容区没铺满）。微信绿按钮在右下角出现 = 输入框可见。
- DPI 换算：GetWindowRect 返回**物理**像素，截图是**逻辑**像素，ratio = 截图/物理（110% 缩放下实测 0.909）。真实鼠标事件（mouse_event/SetCursorPos）用物理坐标：物理 = 逻辑 / ratio + 窗口物理原点。
- 窗口 rect 高度易变（用户拖动/微信自调），每次运行重新 GetWindowRect，别缓存。

## 2b. 滚动：聚焦消息区后键盘滚动有效（2026-08-05 当日晚间纠正——早前「滚动全失败」结论作废）
早前用截图 diff 判定「cua-driver scroll / mouse_event 滚轮 / SendMessage WM_MOUSEWHEEL / keybd_event PageDown 全部无效」——**截图 diff 对 GPU 渲染窗口不可信，该结论作废**。
纠正后的实测：**真实鼠标点击消息区聚焦后，`keybd_event` End + PgDn×N 能滚动聊天区**（UIA 树消息 y 范围变化、新消息出现）。滚动前必须先把焦点放进消息区（真实鼠标点击消息区中部，物理坐标）。
- 判滚动生效看 **UIA 树**（消息 ListItem 的 y 最值/返回集合变化），别看截图 diff。
- UIA ListItem 的 y 是画布绝对坐标，滚动不改变单条 y；生效标志是返回集合与最值变化。

**会话列表滚动（2026-08-05 晚间实测）**：
- **滚轮（mouse_event WHEEL）对会话列表无效；keybd_event PgUp/PgDn 有效**（先真实鼠标点击会话列表中部聚焦，再按 PgUp/PgDn 翻页；PgDn 下滚、PgUp 回顶）。
- 置顶会话 label 带「已置顶」后缀（如 `'二如亭主人已置顶'`），ListItem 带 `selected: True` 标记当前选中会话——**聊天区内容跟随 selected 会话**。
- **⚠ 发送前必须确认 selected 会话 = 目标**：微信可能停在别的会话（用户操作过/窗口被 MoveWindow 后布局重排），此时点输入框会把消息发到错误会话或输入框不存在。诊断第一步 = 查 `[e for e in els if e.get('selected')]` 的 label。滚动会话列表本身也会改 selected 并切换聊天区（PgDn 一次就可能选中置顶区第一个）。

## 2c. 输入方法可靠性分级（2026-08-05 当日晚间大幅纠正——早前分级作废）
微信 4.0 对不同输入事件响应完全不同。**重新验证后，真实鼠标才是主通路**（早前「鼠标无效」= 窗口底边超出屏幕 + 截图 diff 假象双重误判）：
1. ✅ **真实鼠标有效**（`SetCursorPos` + `mouse_event` LEFTDOWN/UP）：点击消息区聚焦后键盘滚动生效（UIA 证实）；点击窗口底部输入框 + 剪贴板粘贴 + Enter **成功发出消息**（UIA 树读回确认，okok 出现在消息列表）。**前提：目标点在屏幕内**——窗口底边（GetWindowRect bottom）超出屏幕高时输入框物理点在屏幕外点不到；先 `MoveWindow` 缩小窗口让底边 < 屏幕高-20。
2. ✅ **keybd_event 键盘有效**：Ctrl+F 聚焦搜索、粘贴、Enter 发送、End/PgDn（焦点在消息区时）滚动全部有效。**输入文本可靠通道**。
3. ❌ **PostMessage 点击无 UIA 证据**：投递 `WM_LBUTTONDOWN/UP`（客户区坐标 lparam）后搜索框未聚焦（无「清空」按钮）、点击会话项未切换聊天（UIA 树仍旧会话）。早前「diff 178815 生效」是截图 diff 假象。**PostMessage 对微信自绘控件不可靠，不再当主通路**。
4. ❌ **cua-driver `click element_index`**：**0.17 起裸 element_index 被直接拒绝**（要求 element_token 或 snapshot_id）；即使传 element_token，accessibility 路径点自绘控件返回 unverifiable、无实际效果。

**发送链路（真实鼠标 + 键盘，替代原 click→type→enter）**：
1. `MoveWindow` 确保窗口底边在屏幕内（用缩小逻辑；放大逻辑会把窗口推到屏幕外）
2. 真实鼠标点击消息区聚焦 → keybd_event End + PgDn 滚到底
3. 真实鼠标点击输入框（窗口底部 x≈0.55W、y≈H-55；UIA 宽 Edit 在树时用它换算物理坐标）
4. ctypes SetClipboardData 设剪贴板（中文）→ Ctrl+V → Enter
5. 读回验证用 UIA 树（见 §2d），失败打 [SEND-ERR] 不写 reply_hash

**⚠ 测试安全铁律（违反过 3 次，每次用户都看到测试消息/乱码）**：发送测试消息永远发「文件传输助手」，绝不发真实联系人（二如亭主人）。但会话切换本身不可靠（PostMessage/UIA 点击都不稳）——**切不过去就放弃本次测试，不要对真实联系人发测试消息**（曾误发「okok」「测试」到真实联系人，用户看到乱码/测试消息；2026-08-05 晚间又误发 5 条「测试」到二如亭主人）。**即使成功切到目标会话，也不要先发测试内容验证——直接发真实回复（走 LLM 生成），或用 UIA 读回验证而非发送**。真要验证发送链路，先切「文件传输助手」（置顶区第二位，PgUp 回顶后可见）。

**UIA 树不暴露搜索结果**：搜索后元素树只有搜索框 + 「清空」按钮，结果列表是自绘的不在 UIA 树里；Enter 行为不稳定。别指望 UIA 定位搜索结果。

## 2d. cua-driver 0.17 API + 剪贴板中文 + 输入框定位（2026-08-05 当日晚间实测）
- **0.17 拒绝裸 element_index**：`click`/`type_text`/`press_key` 传 `element_index` 直接报错（提示用 element_token 或 snapshot_id+element_index）。**升级 cua-driver 后第一件事检查调用参数**——老代码全部静默降级到无效路径，表现为「发送链路全挂」。
- **clip.exe 管道中文乱码**：MSYS/bash 下 `clip.exe` 写 UTF-16LE 中文损坏（微信里变「Km諎裇」乱码；英文 okok 正常）。可靠路径 = ctypes `SetClipboardData(CF_UNICODETEXT=13)`。
- **ctypes 64 位句柄截断坑**：GlobalAlloc/GlobalLock/SetClipboardData 返回 HANDLE，必须设 `restype=c_void_p` + `argtypes=[c_void_p]`，否则句柄截断成 32 位 → GlobalLock 返回 NULL → memmove 访问违规崩溃。
- **输入框自绘不进 UIA 树——但聊天页打开时它其实在树里**（2026-08-05 晚间纠正）：宽 Edit **label = 会话名**（如 `'二如亭主人'`，frame 约 (735,747,1269×95)），不是空 label。之前「找不到输入框」是因为**当前不在目标会话/不在聊天页**，不是输入框不在树。定位优先级：UIA 宽 Edit（label 非「搜索」、w>300）→ frame 换算物理坐标 → 失败再降级窗口底部 (0.55W, H-55)。
- **输入框物理 y 计算**：物理 y = 窗口 top + frame_y/ratio。实测 frame y=747、ratio 0.909 → 物理 y=885（顶）中心 937——**输入框渲染区（物理 ~885-989）超出 GetWindowRect 报的窗口底边 913**（微信自绘界面比 rect 深），这就是「okok 成功点击 y=937 竟在底边外」之谜。**点击输入框的 y 扫描范围 = 窗口底部 H-105 到 H-10**（不只 H-55 一点；本会话 9 候选 y=833-873 失败正是都在输入框顶 885 之上）。
- **UIA 树是可靠读回信号**：消息内容实时（新消息立即出现），但 max_elements 截断 + 返回范围随滚动/状态漂移，判断「最新」要多取样容忍缺失；窗口句柄会反复失效（GetWindowRect 返回 0），每次先 find_wechat_window() 重新定位（该函数返回 bool，调用后读 w.PID/w.WID）。
- 窗口 rect 高度/宽度频繁变动（用户拖动、微信自调、MoveWindow 后微信可能反向调整：1724×850 → 2586×1315 → 1373×929 都见过），每次操作前重新 GetWindowRect；MoveWindow 缩小后 1.5s 内可能被微信改回，必要时缩小后立即操作。

## 2e. ChatWnd 独立聊天窗口（用户把会话单独点出来，2026-08-05 晚间实测）
用户可在微信 4.0 把某个会话单独拖成独立窗口（「单独聊天窗口」）——**这是比主窗口更干净的目标**（无会话列表/导航栏，输入框就在窗口底部）。检测与操作：
- **检测**：EnumWindows 找 pid 匹配 + `GetClassName == 'ChatWnd'` + `GetWindowText == 会话名`（如 '二如亭主人'）。类名 ChatWnd 是独立聊天窗的签名，主窗口类是 WeChatMainWndForPC。
- **ChatWnd 的 UIA 树读不到**（get_window_state 返回 0 元素；uiautomation 库也只能读到标题栏按钮 置顶/最小化/最大化/关闭，消息/输入框不暴露）——**读取必须截图 + OCR**（见 §2f）
- **SetForegroundWindow 会被 Windows 前台锁拦截**（前台不变，返回别的手柄）。解锁：模拟 Alt 键（keybd_event 0x12 down/up）后再 SetForegroundWindow，或**真实鼠标点击窗口标题栏**（窗口顶部中央物理坐标）强制激活——实测点击标题栏激活有效，之后前台 = ChatWnd。
- **操作流程**：MoveWindow 缩小（底边 < 屏幕高-20）→ 点标题栏激活 → 点输入框（0.55W、H-60 物理）→ SetClipboardData + Ctrl+V → Enter。
- 用户主动把会话点成独立窗口 = 强烈信号：主窗口里该会话已不在，cron 的 find_wechat_window 若只认主窗口会找不到目标——窗口发现逻辑需同时支持 ChatWnd。

## 2f. ChatWnd 完整链路：Win32 操作 + OCR 读发（2026-08-05 晚实测闭环，用户确认消息真实发出）
ChatWnd 内容无 UIA 暴露，但 **BitBlt 截图有效**（主窗口 GPU 合成常全灰，ChatWnd 截图 1893 色正常）→ **RapidOCR 读消息**，发送走纯 Win32。已固化进 watch_eruting.py（MODE=chatwnd）：
- **依赖**：`uv pip install rapidocr-onnxruntime`（自带模型离线可用，~3s/张）；uiautomation（诊断用）
- **读取 = BitBlt 截图 + OCR 归属**：气泡中心 x > 窗口宽×0.5 = 夏天（自己/右侧），否则二如亭主人；过滤标题栏（y<70 且 x<0.4W）、发送(S)/口/×/最小化等 UI 文本、时间戳 `\d{1,2}:\d{2}`
- **OCR 会丢空格**（「没咋 去洗吧」→「没咋去洗吧」）——**发送验证必须去空白比较**（re.sub `\s+`），否则误报 [SEND-ERR]
- **发送 = 点输入框(0.55W, H-60) → SetClipboardData → Ctrl+V → Enter**；每段重新聚焦；验证 = 等 1.5s → OCR 读右侧最后一条自己消息去空白匹配
- **激活 = Alt 键技巧 + SetForegroundWindow + 点击标题栏**（单独 SetForegroundWindow 被前台锁拦截）
- **滚动 = 点击消息区(0.5W, 0.45H) 聚焦 + End/PgDn**
- **find_wechat_window 优先级：ChatWnd（标题含「二如亭」）> 主窗口**；无 ChatWnd 时回退主窗口 UIA 模式
- **坑**：窗口底边必须 < 屏幕高-20（否则输入框在屏幕外点不到）；窗口尺寸/位置用户随时会动（每个操作前重新 GetWindowRect）；OCR 对同一消息两次读法可能不同（长句抖动，去空白+部分匹配容忍）
- **速度优化（2026-08-05 晚）**：① `_activate_chatwnd` 前台已是 hwnd 直接跳过（cron 连续轮次省 1.4s×2）；② `_mouse_click` sleep 0.25/0.1/0.6→0.2/0.06/0.4；③ 滚动 PgDn 8→5 次 + sleep 1.2→0.7；④ 发送 sleep 0.6/0.4/0.8/1.5→0.4/0.3/0.5/1.0。实测：find 0s / ensure 0s（前台命中）/ scroll 2.5s / OCR 二次 1.6s
- **OCR 预热坑**：RapidOCR 构造仅 ~1s，但**首次调用 `ocr(img)` 预热 12.6s**（onnxruntime session 创建）——cron 每轮新进程都要付一次；之后每次推理 1.6s。后台 cron 可接受，勿因首轮慢误判故障

## 2g. 窗口异常防护：最小化/覆盖/用户在操作（2026-08-05 深夜 SEND-ERR 根因）
20:09 轮 SEND-ERR（验证读到「夏天：你发啥呢」≠「好 关了」）排查出的三类窗口状态异常，全都要在发送前挡住：
- **最小化窗口 = 经典坐标 (-32000,-32000)**：Windows 最小化窗口 GetWindowRect 返回 (-32000,-32000,...)。**发送前必查 `r.left < -1000` 或 `H < 200` → 直接失败**——此时点输入框会点到屏幕左上角/错误窗口。诊断：EnumWindows 列出该 hwnd 的 rect，看到 -32000 即最小化。
- **被覆盖窗口的 OCR 读到覆盖层内容**：BitBlt 截屏读的是**屏幕合成结果**——ChatWnd 被其他窗口（浏览器/网页）盖住时，OCR 读到的全是覆盖层文字（实测读到「淘气兔/我的订单/我的邀请」机场网页）。**OCR 结果出现非聊天内容（网页文字/菜单/按钮文案）时 = 窗口被覆盖或已关，本轮放弃**，不是消息异常。
- **用户活跃操作 = 让路**：窗口 rect 变化、被移动/最小化/覆盖，说明用户正在电脑前（很可能同时在微信上聊）。bot 本轮放弃、暂停 cron、通知用户确认，**绝不自动恢复重试**。
- **通知用户（no_agent cron 投递机制）**：no_agent 模式 stdout **非空即投递到 origin**（origin 记录在 cron/jobs.json，投递目标 = 创建时会话，如 weixin chat_id o9cq807...）。通知要醒目：成功 `🔔 已自动回复二如亭主人\n她说：「...」\n我回了：「...」`；失败 `⚠️ 自动回复失败（原因）\n...\n已标记为已处理，不会重发同一批`。**用户要求「回复后要通知我一声」= 每个非静默轮都要清晰通知**，别让通知看起来像系统日志。

## 3. 发送链路（click → type → enter → 读回验证）
> **2026-08-05 当日晚间：本节描述的 element_index 链路已过时**——cua-driver 0.17 拒绝裸 element_index，且 UIA 点自绘控件无效。当前有效链路见 §2c（真实鼠标 + 键盘 + SetClipboardData）。本节保留作为失败模式参考。
- click 输入框：element_index（UIA Invoke）background 优先，error/delivery_failed → 像素 foreground；**微信自绘控件 click element_index 常返回 effect=None 且无 error——静默无操作，effect 不为 confirmed 一律不信**（2026-08-05 实测：click 输入框后 frame 不变、输入框无焦点）
- type_text：element_index（UIA SetValue）background 优先；**effect=="unverifiable" 必须降级 foreground**——自绘 Edit 的 SetValue 静默无效（声称成功但没输入，这是「okok 发出去却显示成功」的根因之一）
- press_key return：同上
- 发送后：sleep 1.2s → scroll_to_bottom → snapshot → 过滤系统消息（is_noise：时间戳/通话/撤回/图片占位）→ 比对最后一条自己发的真实消息，不匹配打 `[SEND-ERR]` 并**不写 reply_hash**

## 4. LLM 参数：DeepSeek 推理 token 陷阱
- `max_tokens` 是**推理+正文的总预算**：实测 completion_tokens=494 中 reasoning_tokens=487 → 正文只剩 7 token → 空回复 → 静默 None → 降级敷衍（被用户点名批评过）
- 修复组合：max_tokens=4000 + 空回复且推理 ≥90% 预算时自动翻倍（8000→16000）重试 + 超时 120s（推理长时更从容）
- 其他参数：model=deepseek-v4-flash、temperature=0.8；system = SOUL.md + 技能文本 + samples.md 拼接；API key 从 `$HERMES_HOME/.env` 读

## 4b. 待办需求：引用回复（quote-reply）
用户要求「右键某条消息 → 左键点『回复』→ 输入 → 发送」（回复具体消息）。**尚未实现（2026-08-05 挂起）**。关键约束：cua-driver `click` 只支持左键，右键需 ctypes 模拟（SendMessage WM_RBUTTONDOWN/UP 或 SendInput）；弹层菜单「回复」项可尝试 UIA 枚举 MenuItem；消息定位同样受虚拟画布坐标问题影响（见 §2）。

## 5. 行为守则（用户偏好）
- **发送失败防重发（2026-08-05 深夜修订——旧策略有重复发送风险）**：~~发送成功才写 `state["reply_hash"]`，失败保留旧 hash → cron 下一轮自动重试~~ **作废**。实测验证失败时 Enter 已按下、消息**可能已实际发出**，下轮重试同批会重复发送（她收到两条一样的）。新策略：**失败也写 reply_hash + `last_failed=True`**，同批不重发，**下一条新消息才触发**；成功时 `pop("last_failed")`。宁可漏发，不可乱发——验证失败多半是窗口被移动/最小化/覆盖（用户在电脑前操作），此时重发更危险（可能点进错误窗口）。
- **窗口异常放弃发送**：发送前检测 `GetWindowRect`——`rect.left < -1000`（最小化窗口经典坐标 -32000）或 `H < 200` → 直接失败，不点鼠标不粘贴（防止点到覆盖层/错误窗口）。
- **用户活跃操作信号 = 立即让路**：窗口被移动/最小化/覆盖（OCR 读到非聊天内容，如网页「淘气兔/我的订单」）、rect 与上次不同 → 用户正在电脑前操作，bot 放弃本轮并暂停 cron，把情况告诉用户确认（不要自动恢复、不要重试）。
- **OCR 名字前缀容错**：气泡可能带「夏天：」/「二如亭主人：」前缀（部分微信版本/场景）——验证比较前 `re.sub(r'^(夏天|二如亭主人)[:：]\s*', '', s)` 再去空白。
- 用户本人（夏天）已手动回复过 → collect_unreplied 返回 None → **不抢答**（正确行为，不是故障）
- 她提问必须正面回答，禁止万能敷衍（"okok" 降级被点名）；消息组判断在 SKILL Step 0 + user prompt 双实现

## references
- `references/2026-08-05-wechat-restart-debug.md` — 微信重启静默故障完整排查记录（窗口 id 时间线、坐标换算、错误签名、修复落地）
- `references/2026-08-05-canvas-coords-and-scroll-blocker.md` — 虚拟画布坐标证据、官方截图验证法、合成滚动全失败的实测记录、引用回复挂起状态
- `references/2026-08-05-postmessage-click-breakthrough.md` — **已被 2026-08-05 当日晚间实测推翻**（PostMessage 无 UIA 证据，diff 是截图假象）；保留作对照
- `references/2026-08-05-cuadriver17-real-mouse.md` — 当日晚间纠正记录：cua-driver 0.17 API、真实鼠标/键盘主通路、滚动聚焦法、clip.exe 中文坑、ctypes 句柄坑、输入框定位与未决问题
- `references/2026-08-05-chatwnd-independent-window.md` — ChatWnd 独立聊天窗口检测/激活/操作、会话列表 PgUp/PgDn 滚动、输入框 y=937 之谜解开（frame 换算 + 渲染区超 rect）、窗口尺寸漂移
- `references/2026-08-05-minimized-window-senderr.md` — 20:09 SEND-ERR 完整排查：最小化窗口经典坐标 (-32000,-32000)、覆盖层 OCR 污染（读到网页文字）、失败防重发修复、通知格式升级
- `scripts/wechat_probe.py` — 诊断探针：三种截图源对比 + PostMessage 点击 + 键盘辅助（改 watch_eruting.py 发送链路时的复用起点）
