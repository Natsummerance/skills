# PostMessage 点击 / 键盘路径突破 —— 2026-08-05 完整实测记录

背景：微信重启后窗口显示异常（聊天区灰、输入框视口外），此前一切真实鼠标/合成滚动全失败。
本会话找到**可靠输入通道**，并确认「鼠标事件被吞」是独立于滚动问题的第二个大坑。

## 输入事件实测分级（全部以像素 diff 判定，diff 小≈139 为噪声、大≈17 万为真变化）

| 通道 | 操作 | diff 结果 | 结论 |
|---|---|---|---|
| cua-driver `click element_index=16` | 点击会话「二如亭主人」 | 0 | ❌ 自绘控件静默无效 |
| `SetCursorPos + mouse_event` | 点击会话 (848,289) / (848,395) | 0 / 139 | ❌ 真实鼠标无效 |
| `SetCursorPos + mouse_event` 滚轮 | 4 个位置滚轮 | 全 0 | ❌ 真实滚轮无效 |
| `SendMessage WM_MOUSEWHEEL / PageDown` | 直投窗口 | 全 0 | ❌ |
| `keybd_event` Ctrl+F + 粘贴 + Enter | 搜索 | 178817 / 179846 | ✅ 键盘有效 |
| **`PostMessageW WM_LBUTTONDOWN/UP`** | 点击会话「文件传输助手」客户区 (569,332) | **178815** | ✅ **有效，本会话突破** |

判定细节：diff≈139 是噪声（可能光标/抗锯齿抖动）；真正生效的 diff 都是 ~17 万量级（大量像素变化）。

## PostMessage 点击配方
```python
lparam = (cy << 16) | (cx & 0xFFFF)          # 客户区物理坐标（非屏幕坐标！）
user32.PostMessageW(hwnd, 0x0201, 0x0001, lparam)  # WM_LBUTTONDOWN, MK_LBUTTON
time.sleep(0.1)
user32.PostMessageW(hwnd, 0x0202, 0, lparam)        # WM_LBUTTONUP
```
- 坐标 = 客户区物理像素：`frame逻辑坐标 / ratio`，其中 ratio = cua截图逻辑宽 / GetWindowRect 物理宽（实测 0.909）
- 绕过命中测试 → 不受 overlay 影响 → 对自绘控件有效

## Cua.AgentCursorOverlay 嫌疑
- 枚举顶层窗口发现 `Cua.AgentCursorOverlay` class，pid=cua-driver，全屏 (0,0,1707x960) 可见
- `GetWindowFromPoint` 在点击点查询**返回微信**（overlay 不在命中链）→ 但真实鼠标仍无效
- 尝试 `EnableWindow(hwnd, False)` + `ShowWindow(hwnd, 0)` 仍无效 → 最终不纠结原因，**放弃真实鼠标，一律 PostMessage**

## 三种截图源互相矛盾（判活靠交互 diff）
| 来源 | 实测画面 | 结论 |
|---|---|---|
| cua-driver `screenshot_png_b64` | 深灰 (168) | GPU 表面可能拿不到 |
| BitBlt 屏幕 DC（GetDC(0)+BitBlt+GetDIBits） | 浅灰 (245) 全均匀 | 与 cua 不一致 |
| PrintWindow | 旧帧（diff=0 假象） | 陈旧 |

**判活第一性原理**：键盘操作后 diff 明显变化 = 微信活着 + 键盘路径通。画面灰≠故障结论，可能只是截图 API 拿不到渲染帧。需要给用户看真实画面时用 BitBlt 截图（`cache/wx_screen_bitblt.png` 曾发给用户确认）。

## 其他可复用事实
- 窗口 rect 一个会话内变 4 次：1724x977 → 2586x1466 → 1057x739 → 1724x977 —— 永远实时 GetWindowRect
- cua-driver `get_window_state` 失败时返回 `{"pid": N}`（无 elements/截图键）——调用方要判空
- UIA 树不暴露搜索结果显示（只有搜索框+「清空」按钮）——搜索操作无法用 UIA 验证
- 测试发送必须走「文件传输助手」，绝不发真实联系人
- cron 发送失败签名：`[SEND-ERR] 验证失败: 最后一条自己消息「X」≠ 回复「Y」` = 发送没落地、reply_hash 未更新、下轮自动重试
