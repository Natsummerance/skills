# 运维手册：部署 / 配置 / 自启 / 常见故障

## 目录结构
```
person-watchdog/
├── watchdog.py            # 主程序（检测 + 通知）
├── config.json            # 配置（由 config.example.json 复制而来）
├── setup.ps1              # 一键安装：venv + 依赖 + 模型下载
├── supervisor.ps1         # 守护：watchdog 退出自动重启
├── install-task.ps1       # 开机自启注册/注销（需管理员）
├── requirements.txt
├── test_watchdog.py       # 单元测试（48 例）
├── models/                # yolo11m.onnx + face_detection_yunet_2023mar.onnx
├── .venv/                 # 独立虚拟环境
├── logs/watchdog.log      # 运行日志（滚动 3×1MB）
├── snapshots/             # 抓拍临时目录
└── learning_data.json     # 自动学习数据（运行时生成）
```

## 安装
```powershell
cd <目标目录>
.\setup.ps1                 # 建 .venv、装依赖、下载模型并验证
```

## 配置（config.json 关键项）
| 键 | 默认 | 说明 |
|---|---|---|
| `hermes_send` | `{{HERMES_SEND}}` | hermes.exe 路径；留空则用 PATH 中的 hermes |
| `target` | `{{FEISHU_TARGET}}` | 飞书目标，如 `feishu:oc_xxxx` |
| `camera_index` / `auto_select_camera` | 0 / true | 摄像头选择；`camera_name_exclude` 排除 OBS/Virtual/OMEN |
| `model` / `input_size` / `conf_threshold` | yolo11m.onnx / 640 / 0.35 | 检测模型与参数（可降级 yolov8n/s） |
| `onnx_threads` | 4 | ONNX 推理线程数（省 CPU 关键项） |
| `human_confirm_frames` | 3 | 连续 N 帧确认有人才触发 |
| `capture_window_secs` | 6 | 抓拍采集窗口（取最高分帧） |
| `exit_confirm_secs` | 5 | 人连续消失 N 秒才算离开 |
| `grace_secs` | 15 | 开机宽限期（不检测） |
| `motion_gate_width` / `motion_threshold` | 160 / 18.0 | 运动门控省电 |
| `notify_on_leave` / `send_snapshot` | true / true | 离开消息与抓拍开关 |
| `keep_snapshots` | false | 发送成功后删除本地抓拍 |

## 运行
```powershell
.venv\Scripts\python.exe watchdog.py --list-cameras
.venv\Scripts\python.exe watchdog.py --test-send "测试"
.venv\Scripts\python.exe watchdog.py
```

## 开机自启
```powershell
# 管理员 PowerShell
.\install-task.ps1            # 注册 PersonWatchdog（登录时经 supervisor 启动，隐藏窗口）
.\install-task.ps1 -Uninstall # 注销并停止
```
验证：`Get-ScheduledTask -TaskName PersonWatchdog | Select State`，并检查 `LastRunTime/LastTaskResult`（见 debugging-log.md 结论 1）。

## 常见故障速查
| 症状 | 检查 | 处置 |
|---|---|---|
| 从未收到通知 | `logs\watchdog.log` 尾部；`--test-send` | 先修链路，再查检测 |
| 注册了自启但不生效 | `LastRunTime=1999` / `LastTaskResult=267011` | 任务没真正跑过；检查执行体路径，`Start-ScheduledTask` 验证 |
| 一段时间后没动静 | 进程是否还在 | 用 supervisor 守护；查日志 |
| cmd 弹窗 | 发送是否带 `CREATE_NO_WINDOW` | 用本 skill 的模板版本 |
| CPU/内存高 | `Get-Process pythonw` | `onnx_threads: 4` + 运动门控 + 冷却参数 |
| 照片只有侧影/模糊 | 抓拍时机 | 检查采集窗口与最佳帧打分参数 |
| 坐在电脑前不提醒 | `--list-cameras` 亮度；镜头朝向 | 确认人在画面内；排除虚拟摄像头；手动指定 index |
| 摄像头被占用/拔掉 | 日志报错 | 程序自动每 5 秒重试，不退出 |

## 日志
- `logs\watchdog.log`：运行、检测、发送、学习事件均记录。
- 发送失败：本地保留抓拍并记日志，重试一次后放弃（避免重复轰炸）。
