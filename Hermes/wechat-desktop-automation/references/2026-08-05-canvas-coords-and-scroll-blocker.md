# 2026-08-05：虚拟画布坐标 + 合成滚动全失败 + 引用回复挂起

## 背景
用户反馈「硬编码写太死，一重启就不能用了」→ 彻底动态化 watch_eruting.py（PID/WID/窗口尺寸/输入框坐标/滚动锚点全部运行时推导）。过程中发现微信 4.0 的 UIA 坐标系与旧认知不符，并撞上滚动硬阻塞。

## 硬编码清理（已完成并同步双副本）
- `PID, WID = 0, 0` + `find_wechat_window()`：EnumWindows 标题「微信」→ UIA 特征识别主窗口（label=="搜索" Edit + 宽 >300 的 Edit），排除通知弹窗；先查可见窗口，隐藏的最后 ShowWindow(9) 恢复再查。
- `get_wechat_layout()`：从 get_window_state 元素 frame + GetWindowRect + 截图尺寸实时推导输入框/滚动锚点本地坐标与所需最小窗口逻辑尺寸。
- 删除了 WIN_X/WIN_Y/WIN_W/WIN_H (597,204/1365×960)、输入框 (456,794)、滚动锚点 (1507,619) 全部硬编码。
- grep 验证：`grep -nE "597|1365|456|794|1507|619|23199872|32684"` → 无残留。

## 关键实测数据（本窗口状态）
- 窗口物理 rect：398,136,1724,977（**每次运行都在变**，用户拖动/微信自调；曾见 597,204,1365,960 与 398,136,2025,1156）。
- cua-driver 官方截图：1567×888（逻辑像素）→ ratio = 1567/1724 = 0.909（≈110% DPI 缩放，逻辑 = 物理 × 0.909）。
- 聊天输入框 UIA frame：**(1053, 1505, 2130, 95)**，label「二如亭主人」（对方名字即输入框 label）。
- 聊天消息 ListItem frame：x=1053, w=2130, **y 从 -1290 起**（负值 = 画布在视口上方，窗口滚动位置停在聊天记录顶部）。
- 会话列表 ListItem：x=678, w=374, y=297+（正 y，在视口内）。
- 结论：**frame 是虚拟画布坐标**（画布宽 2130 > 截图宽 1567；输入框 y=1505 > 截图高 888），frame ↔ 截图像素无 1:1 映射。同一棵树里会话列表 frame 像视口坐标、聊天区 frame 是画布坐标，不能混用。

## 验证通道：官方截图，不是 PrintWindow
- `get_window_state` 响应含 `screenshot_png_b64`（base64 PNG，逻辑像素 1567×888）+ `screenshot_width/height` + `tree_markdown`。
- **PrintWindow/GetWindowDC 自截图对微信返回陈旧帧**：连续两次抓取 diff=0 是假象（窗口实际已变化/滚动）。多轮「滚动没生效」误判的根因。此后一切视觉验证必须解码官方 b64。
- 大 b64 会撑爆 stdout → 朴素 `subprocess.run` + `stdout.find("{")` + `json.loads` 的 call() 助手解析失败返回 `{"raw": ...}`。直接调 cua-driver 却正常——说明是管道/输出截断问题。要么处理大输出，要么诊断时直接命令行调用。

## 图像分析（无视觉模型时的界面状态判断）
- 微信绿发送按钮 #07C160：扫描 G>110 且 G>R+40 且 G>B+40；右下角 (x>60%W, y>70%H) 出现绿色簇 = 输入框可见；无 = 输入框在视口外。
- 分区平均色：正常聊天区 = 白底（>230）；右侧 (139,139,139) 灰 + 底部 850-888 纯黑 + 黑色占比 35.7% = 界面异常/内容未铺满。
- 绿色像素在左上 (16..94, 90..742) 是左侧导航图标，不是发送按钮。

## 合成滚动全失败（官方截图 diff=0 验证）
| 方法 | 结果 |
|---|---|
| cua-driver `scroll` foreground page-down ×6 | diff=0 |
| `mouse_event(0x0800, 0,0,-120,0)` ×15（光标在消息区 3 个位置） | diff=0 |
| `SendMessageW(hwnd, WM_MOUSEWHEEL, -120<<16, 0)` ×10 | diff=0 |
| `SendMessageW(hwnd, WM_KEYDOWN/UP, VK_NEXT)` ×10 | diff=0 |
| 物理点击消息区 + keybd_event PageDown ×10 | diff=0 |
| `click element_index=123`（输入框 UIA Invoke） | effect=None, frame 不变 |

→ 微信 4.0 忽略一切合成滚动与 UIA 点击。若窗口滚动位置停在记录顶部，输入框在画布 1505 处不可达。**未解决**；猜测微信只响应原生硬件滚轮消息流，需真实输入模拟层验证。

## 引用回复（quote-reply）需求 —— 挂起
用户要求：右键某条消息 → 左键点「回复」→ 输入 → 发送。约束：
- cua-driver `click` 只有左键（describe 确认，无右键参数）。
- 右键需 ctypes：`SendMessage(hwnd, WM_RBUTTONDOWN/UP)` 或 `SendInput`。
- 弹层菜单「回复」可试 UIA 枚举（role MenuItem）。
- 消息定位受虚拟画布坐标问题影响（§2）。
- 未实现，下次接续。
