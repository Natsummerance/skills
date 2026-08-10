# 调试日志：相机监控类项目排障方法论（实测沉淀）

> 来自 PersonWatchdog v2 真实排障记录。核心思想：**先判活，再猜原因**。怀疑模型之前，先确认进程在跑、CPU 正常、画面有人、计划任务真的启动过。

## 总原则（诊断顺序）
1. **进程是否在跑**：`Get-Process pythonw,python | Select Id,ProcessName,CPU,WorkingSet,StartTime`。进程没了 → 一切功能都不存在，先解决守护。
2. **CPU/内存是否异常**：`Get-Process pythonw | Select Id,CPU,WorkingSet`。持续高 CPU 说明检测循环在空转（见结论 3/4）。
3. **计划任务是否真正启动**：`Get-ScheduledTask -TaskName PersonWatchdog | Select State; (Get-ScheduledTaskInfo -TaskName PersonWatchdog).LastRunTime, LastTaskResult`。**注册成功 ≠ 运行成功**（见结论 1）。
4. **画面里到底有没有人**：`watchdog.py --list-cameras` 看亮度；截帧看 `frame_brightness`（见结论 6）。人不在镜头内时，再准的模型也输出 0 人。
5. **最后才怀疑模型/阈值**：`conf_threshold`、`input_size`、人脸置信度等。

## 六条实测结论（每条都是踩过的坑）

### 1. 计划任务 LastRun=1999 / LastTaskResult=267011 → 任务从未真正启动
- 现象：任务已注册（State=Ready），但 `LastRunTime=1999-12-30`、`LastTaskResult=267011`（0x41303 = 任务尚未运行）。
- 结论：注册成功不等于运行成功。验证必须看 `LastRunTime/LastTaskResult`，不是看任务列表里"存在"。
- 修复：确保触发器是 `AtLogOn`、执行体存在、用绝对路径；注册后手动 `Start-ScheduledTask -TaskName PersonWatchdog` 验证一次。

### 2. 守护进程会在长时间运行后消失 → 需要 supervisor + 计划任务双层
- 现象：23:14 后 watchdog 进程消失，无人重启，之后不再有任何通知。
- 结论：单层计划任务不够，必须在计划任务里挂 `supervisor.ps1`：循环 `Start-Process pythonw watchdog.py`，进程退出后自动重启（3 次内 5 秒、之后 30 秒退避），`supervisor.stop` 文件可优雅停止。
- 停机链路：`install-task.ps1 -Uninstall` 会注销任务、创建 stop 标记、强杀匹配 `*person-watchdog*watchdog.py*` 的 pythonw。

### 3. 有人活动时 IDLE 空转 YOLO → CPU 200%、内存 465MB
- 现象：房间有人活动（但不构成"人形确认"）时，检测循环一直在跑 YOLO，CPU 冲到 200%，内存 465MB。
- 根因：只在"完全无运动"时空闲，一旦有运动就持续全速检测，运动但不含人 → 空转。
- 修复：三层节流——(a) 空闲只做 160 宽灰度帧差运动门控（不跑 YOLO，500ms 轮询）；(b) "运动但没检到人"进入 `idle_empty_backoff_secs: 2.0` 冷却；(c) 人在场时检测降到 `present_interval_ms: 1000`（1 秒/次）。布防后每 5 秒（`idle_detect_secs`）定期扫描一次，静止的人也能被检出。

### 4. ONNX 默认全线程是隐形 CPU 杀手 → 限 4 线程省 11 倍
- 实测数据：默认全线程 `wall 177ms 但 cpu 2.86s/次`；`onnx_threads: 4` 后 `wall 323ms、cpu 0.26s/次`。
- 结论：单帧墙钟时间只慢一倍，但 CPU 时间省 11 倍——多核机器默认会烧满所有核。
- 修复：`config.json` 设 `onnx_threads: 4`（按核数调整）；YOLO 推理走 onnxruntime `SessionOptions.intra_op_num_threads`。

### 5. 布防后 CPU 从 206% → 10%
- 验证项：运动门控 + 冷却 + 人在场降频 + ONNX 限线程全部生效后，布防状态 CPU 约 10%，空闲状态更低。
- 验收标准：`Get-Process pythonw | Select CPU` 持续观察 60 秒，CPU 百分比应明显低于检测空转期。

### 6. 画面 brightness≈122 + YOLO 0 人 → 人不在镜头内，不是模型故障
- 现象：用户反馈"我一直坐在电脑前也没警告"。
- 诊断：`frame_brightness(frame) ≈ 122`（正常室内画面），YOLO 输出 0 人，模型测试（bus.jpg）正常检出。
- 结论：**画面里根本没有这个人**——最常见原因是镜头朝向不对（摄像头被 OBS/虚拟摄像头抢占，或前置摄像头选了 index 0 但实际是别的设备）。
- 修复：`--list-cameras` 看设备名与亮度；`config.json` 用 `camera_name_exclude: ["OBS","Virtual","OMEN"]` 排除虚拟/游戏本摄像头，或手动指定 `camera_index`；同时确认人确实在镜头画面内（可临时 `--test-send` 看抓拍）。

## 快速诊断命令清单（Windows PowerShell）
```powershell
# 进程与资源
Get-Process pythonw,python -ErrorAction SilentlyContinue | Select Id,ProcessName,CPU,WorkingSet,StartTime
# 计划任务真实运行状态
Get-ScheduledTask -TaskName PersonWatchdog | Select State
(Get-ScheduledTaskInfo -TaskName PersonWatchdog) | Select LastRunTime,LastTaskResult
# 日志尾部（错误/发送失败）
Get-Content logs\watchdog.log -Tail 40
# 摄像头枚举
.venv\Scripts\python.exe watchdog.py --list-cameras
# 飞书链路
.venv\Scripts\python.exe watchdog.py --test-send "链路测试"
```

## 发送与弹窗纪律
- `hermes send` 必须带 `CREATE_NO_WINDOW`（无 cmd 黑窗）；发送放入后台队列线程，不阻塞检测循环。
- 抓拍图发送成功后立即删除本地文件（`keep_snapshots: false`）；失败保留文件并记日志、重试一次。
- 照片出现"只剩侧影"的根因是发送时机太晚（人已走）——修复为采集窗口内按"人脸占比×置信度×清晰度"取最高分帧，而不是离开瞬间抓拍。
