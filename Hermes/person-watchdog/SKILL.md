---
name: person-watchdog
description: 摄像头人形监控守护（PersonWatchdog）的部署、运维与排障技能。用于在 Windows 上用前置摄像头持续检测"有人经过电脑前"，通过 Hermes 的 hermes send 向飞书私聊发送文字提醒 + 清晰人脸抓拍 + 停留时长；支持开机自启（计划任务 + supervisor 守护）、省电优化（运动门控、ONNX 限线程）、自动学习强化（误报区域抑制、自适应置信度阈值），并沉淀相机监控类项目的整套实测调试方法论（进程消失、CPU 飙高、ONNX 线程、画面亮度诊断、计划任务 LastRun=1999 等）。触发场景：用户说"帮我装个摄像头监控""检测有人经过电脑前发飞书""开机自启不生效""watchdog 没动静/卡顿/弹窗/CPU 高""摄像头监控排查"。依赖 Hermes（hermes send）与飞书，脚本为可复用模板（占位符配置）。
---

# PersonWatchdog：摄像头人形监控守护

## 何时使用
- 用户要"检测有人经过电脑前并通知"，或已有 PersonWatchdog 需要部署/排障/优化。
- 症状类请求：没收到提醒、开机不自启、cmd 弹窗、电脑卡顿、CPU/内存高、照片模糊或只剩侧影、想记录停留时长、想让它越用越准。

## 快速部署（Windows，一次完成）
1. 把 `scripts/` 复制到目标目录（例如 `C:\...\person-watchdog\`），复制 `scripts\config.example.json` 为 `config.json`，填写两个占位符：
   - `{{HERMES_SEND}}`：hermes.exe 完整路径（留空则用 PATH 中的 hermes）。
   - `{{FEISHU_TARGET}}`：飞书目标，如 `feishu:oc_xxxx`。
2. 运行 `.\setup.ps1`：创建独立 `.venv`、安装依赖（onnxruntime / opencv-python-headless / numpy / pygrabber）、下载 YOLO11m + YuNet 人脸模型并验证可加载。
3. 验证链路：`.venv\Scripts\python.exe watchdog.py --test-send "测试消息"`，飞书应收到文字+抓拍。
4. 确认摄像头：`.venv\Scripts\python.exe watchdog.py --list-cameras`；若前置摄像头不是 index 0，改 `config.json` 的 `camera_index`（或开 `auto_select_camera`）。
5. 前台试跑：`.venv\Scripts\python.exe watchdog.py`；确认有人出现→发"⚠️ 有人出现在电脑前"、离开→发"👋 人已离开，停留 X 分 Y 秒"。
6. 开机自启：管理员运行 `.\install-task.ps1`（注销用 `-Uninstall`）。

## CLI 速查
- `watchdog.py`：前台运行检测循环。
- `--list-cameras`：枚举摄像头 index/亮度/分辨率。
- `--test-send "消息"`：同步发一条测试通知（验证飞书链路）。
- `--config <path>`：指定配置文件（默认 `config.json`）。
- `--reset-learning`：清空学习数据（误报区域/自适应阈值）。
- `--version`：版本号。

## 工作机制（理解后再调参）
- 状态机：仅"无人→有人"跳变时发出现消息；人在场不重复；人连续消失 ≥5 秒（`exit_confirm_secs`）才发离开消息并重新布防；开机前 15 秒（`grace_secs`）不检测。
- 清晰抓拍：连续 3 帧确认有人后进入 6 秒采集窗口，按 `人脸占比 × 人脸置信度 × 清晰度(Laplacian 方差)` 打分，窗口结束发送最高分帧；无人脸（背对/戴口罩）退回"最大人体框+最清晰"帧。
- 省电：空闲只做 160 宽灰度帧差运动门控（不跑 YOLO，500ms 轮询）；有运动才检测；布防后每 5 秒定期扫描静止的人；ONNX 限 4 线程（`onnx_threads: 4`），布防后 CPU 从约 200% 降到约 10%。
- 自动学习（纯本地）：见 `references/learning-mechanism.md`。

## 排障方法论（先看这里）
- 总原则：**先判活，再猜原因**——进程在不在、CPU 多少、画面亮不亮、计划任务有没有真正跑，最后才怀疑模型。
- 九条实测结论与诊断命令：见 `references/debugging-log.md`（含计划任务 `LastRun=1999`、supervisor 守护、ONNX 线程、brightness 诊断等）。
- 运维手册/常见故障表：见 `references/ops-playbook.md`。

## 验收清单
- [ ] `setup.ps1` 成功且模型可加载（无报错）。
- [ ] `--test-send` 飞书收到文字+图片。
- [ ] `--list-cameras` 列出本机摄像头。
- [ ] 空房间 1 分钟无任何通知。
- [ ] 走过摄像头：1–2 秒内收到"出现"消息+清晰人脸照；再次走过收到第二条；持续站在镜头前不重复发送。
- [ ] 离开后收到"停留时长"消息。
- [ ] `install-task.ps1` 后任务出现在计划任务；`-Uninstall` 后消失。
- [ ] 拔插摄像头程序自动重试不退出。
- [ ] 空闲时 CPU 占用明显下降、无 cmd 弹窗。

## 定制与降级
- 模型：`config.json` 改 `model: yolov8n.onnx` / `yolov8s.onnx` / `yolo11s.onnx` 可降级提速（`setup.ps1 -Model <名>` 下载）。
- 精度：`input_size: 416` 提速；`conf_threshold` 0.25–0.55（自适应学习会自动在此区间调整）；`onnx_threads` 按 CPU 核数调整。
- 通知：`appear_template` / `leave_template` / `message_template` 可改文案；`notify_on_leave: false` 关闭离开消息。
