# 2026-08-05 当日晚间：cua-driver 0.17 + 真实鼠标主通路（推翻早前 PostMessage 突破论）

本记录修正 `2026-08-05-postmessage-click-breakthrough.md`：当晚用 UIA 树重新验证后，
「PostMessage 点击 = 突破」「真实鼠标无效」「滚动全失败」三个结论全部作废。

## 验证过的可靠信号（按可信度排序）
1. **UIA 树（get_window_state elements）** — 消息内容实时（新消息立即出现在树里）、
   会话切换/滚动有痕迹。但 max_elements 截断 + 返回范围随状态漂移，判断「最新」要多取样。
2. **keybd_event 键盘** — Ctrl+F 聚焦搜索（UIA 出现「清空」按钮证实）、粘贴、Enter、
   焦点在消息区时 End/PgDn 滚动，全部有效。
3. **真实鼠标（SetCursorPos + mouse_event LEFTDOWN/UP）** — 点击消息区聚焦后滚动生效
   （UIA y 范围 46→1061）；点击窗口底部输入框 + 粘贴 + Enter 成功发出消息（UIA 读回 okok）。
4. ❌ 截图 diff（cua-driver 官方 / BitBlt / PrintWindow）— GPU 窗口三个源互相矛盾，
   diff 数值不可当真。判活/判变化一律以 UIA 树为准。

## 为什么早前「鼠标无效」：两个叠加误判
- **窗口底边超出屏幕**：窗口物理 rect (279,63,1724×977) → bottom=1040 > 屏幕高 960，
  输入框物理点在屏幕外，SetCursorPos 点不到（鼠标事件发出去了但落在屏幕外/别处）。
  修复：`MoveWindow` 缩小窗口高 → 底边 < 屏幕高-20。之后鼠标点击全部有效。
- **验证手段错**：早前用截图 diff=0 判「鼠标无效」，但截图对 GPU 窗口本来就不可信。

## cua-driver 0.17 API 变更（发送链路全挂的根因之一）
- 裸 `element_index` 参数被直接拒绝：报错要求 `element_token`（如 "s000004ba:19"）
  或 `snapshot_id` + `element_index`。
- 老 send_text 的 `click/type_text/press_key element_index=...` 全部 refused →
  静默降级到无效 foreground 路径 → [SEND-ERR]。
- 即使传 element_token：accessibility 路径点自绘控件返回 unverifiable、无实际效果
  （点会话列表「文件传输助手」聊天区没切换）。
- 教训：升级 cua-driver 后第一件事检查调用参数；UIA 点不动自绘控件。

## 剪贴板中文乱码（用户看到「你怎么发了个乱码」）
- `clip.exe` 管道在 MSYS/bash 下写 UTF-16LE 中文会损坏（微信里显示「Km諎裇」）；
  英文 okok 正常（ASCII 不受影响）。
- 修复：ctypes `SetClipboardData(CF_UNICODETEXT=13)`。
- **ctypes 64 位句柄截断坑**：GlobalAlloc/GlobalLock/SetClipboardData 返回 HANDLE，
  必须 `restype=c_void_p` + `argtypes=[c_void_p]`（含 GlobalAlloc 的
  `argtypes=[c_uint, c_size_t]`、GlobalUnlock），否则句柄截断成 32 位 →
  GlobalLock 返回 NULL → memmove 访问违规崩溃 / OverflowError。
- 验证剪贴板：ctypes GetClipboardData 读回可能因剪贴板占用/延迟渲染失败；
  用 `powershell Get-Clipboard -Raw` 做交叉验证，但经 MSYS 管道显示中文会乱
  （显示问题，非数据问题）。

## 输入框定位
- 微信 4.0 聊天输入框（宽 Edit）**经常不在 UIA 树**（只有「搜索」Edit）——
  `get_wechat_layout` 返回 None，老代码直接放弃。
- 降级：输入框固定窗口底部 → 物理坐标 (left + 0.55W, top + H-55)。
- 未决怪点：okok 成功那次点击 y=937，低于 GetWindowRect 报的窗口底边 913——
  输入框实际渲染区可能比 rect 报告更深（DPI/客户区偏移）。窗口状态变动后
  输入框坐标不稳定（9 个候选位置全失败、UIA 树一度无消息），本会话未完全解决。
- 窗口句柄会反复失效（GetWindowRect 返回 0）：每次诊断先 find_wechat_window()
  （返回 bool，之后读 w.PID/w.WID），别缓存句柄。

## 一次性成功的 okok 发送配方（作为参考，非稳定流程）
1. MoveWindow 缩小窗口 (279,63,1724×850) → 底边 913 < 960
2. 真实鼠标点击消息区 (1709,503) 聚焦 → keybd_event End + PgDn×10 滚到底
3. 真实鼠标点击 (1489,937)（输入框区域）→ SetClipboardData('okok') → Ctrl+V → Enter
4. UIA 树读回：okok 出现在消息列表 y=794 ✓
后续同配方（「测试」「测试中文」）失败——输入框坐标/窗口状态漂移，待下轮解决。
