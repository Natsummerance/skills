# 调试日志：相机监控类项目排障方法论（实测沉淀）

> 来自 PersonWatchdog v2 真实排障记录。核心思想：**先判活，再猜原因**。怀疑模型之前，先确认进程在跑、CPU 正常、画面有人、计划任务真的启动过。

## 总原则（诊断顺序）
1. **进程是否在跑**：`Get-Process pythonw,python | Select Id,ProcessName,CPU,WorkingSet,StartTime`。进程没了 → 一切功能都不存在，先解决守护。
2. **CPU/内存是否异常**：`Get-Process pythonw | Select Id,CPU,WorkingSet`。持续高 CPU 说明检测循环在空转（见结论 3/4）。
3. **计划任务是否真正启动**：`Get-ScheduledTask -TaskName PersonWatchdog | Select State; (Get-ScheduledTaskInfo -TaskName PersonWatchdog).LastRunTime, LastTaskResult`。**注册成功 ≠ 运行成功**（见结论 1）。
4. **画面里到底有没有人**：`watchdog.py --list-cameras` 看亮度；截帧看 `frame_brightness`（见结论 6）。人不在镜头内时，再准的模型也输出 0 人。
5. **最后才怀疑模型/阈值**：`conf_threshold`、`input_size`、人脸置信度等。

## 实测结论（每条都是踩过的坑）

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

## 七、离开消息丢失 → 退出时发送队列未排空（daemon 线程被杀死）
- 现象：飞书只收到"出现"照片，没收到"👋 人已离开，停留 X 分 Y 秒"。
- 实测时序：`事件[离开]` 入队后 79ms 进程退出（`达到测试时长...退出`），后台发送线程是 `daemon=True`，进程退出时被直接杀死，队列里的离开消息丢失。
- 根因：`Sender.close()` 只投递哨兵 `None`，**不等待 worker 排空队列**。
- 修复：`close(timeout)` = 投哨兵 + `thread.join(timeout)`；`run()` 收尾调用 `sender.close(60)`，干净退出（duration/Ctrl+C/异常）时已入队消息必然发完；join 超时记 warning 日志。
- 验证：单测 `test_sender_close_drains_queued_messages`（不调 flush 直接 close，断言两条消息都发出）。
- 纪律：任何"发送队列 + daemon 线程"架构都必须保证退出路径排空，否则最后一条消息大概率丢。

## 八、计划任务 LastTaskResult=0xC000013A 与 supervisor 被终止
- 现象：任务确实运行过（LastRunTime 正常），但 LastTaskResult=0xC000013A（STATUS_CONTROL_C_EXIT），watchdog 与 supervisor 双双消失。
- 结论：0xC000013A = 进程被 Ctrl+C 类信号终止；supervisor 挂了就没有守护，watchdog 退出后无人重启。**注册任务后要定期看 LastTaskResult，不是看 State**。

## 九、双实例/僵尸进程排查
- watchdog 单实例：命名互斥量 `PersonWatchdogMutex`，第二个实例退出码 3；supervisor 对退出码 3 采用 60 秒长退避，避免与手动实例互踢。
- 系统里"同一个程序两个进程"≠ watchdog 双实例：实测发现 Hermes gateway 与 n8n server.py 各有两个进程（同一脚本、不同解释器），多为开机启动脚本重复拉起；清理前先确认哪个是权威实例（看父进程、端口绑定），不要盲杀正在使用的服务。
- **"pythonw 两个进程" ≠ 双实例**：`.venv\Scripts\pythonw.exe` 是 venv 重定向器，它会再拉起真实解释器（如 uv 的 pythonw.exe），表现为"两个 pythonw"——其实是同一个 watchdog 实例（父=启动器，子=解释器）。判断是否双实例要看互斥：再启一个实例应被拒绝并退出码 3，而不是数 pythonw 个数。

## 十、PowerShell 脚本 UTF-8 无 BOM → PS 5.1 按 ANSI 误读，中文注释吃行/引号
- 现象：supervisor.ps1 秒退，stderr 报 `字符串缺少终止符` / `缺少 }`，但文件内容看着完全正常。
- 根因：Windows PowerShell 5.1 对**无 BOM** 的 .ps1 按 ANSI(GBK) 解析；UTF-8 中文注释的尾字节（如 `。` 的 0x82）会被当作 GBK 双字节前导，**吞掉后面的 `\r`/`\n` 或引号**，导致注释与下一行合并、字符串未终止。LF 行尾比 CRLF 更容易中招（吞 `\n` 直接并行）。
- 修复：.ps1 一律存 **UTF-8 with BOM**（`utf-8-sig`）+ CRLF；改完用 `[System.Management.Automation.Language.Parser]::ParseFile` 在真实 powershell.exe 里验证 0 错误。

## 十一、摄像头对着桌面而不是走道 → 永远零事件（"人走过没提醒"的常见真凶）
- 现象：watchdog 正常运行、摄像头亮度正常（~123）、无任何报错，但 2 小时+ 零事件；`--debug` 显示每帧 `motion=False det=0`、亮度纹丝不动。
- 诊断：抓帧做全类 YOLO——画面是"水瓶/椅子/手提包"等桌面物品、无人无脸 → 摄像头朝向问题，不是模型/链路问题。
- 根因：笔记本屏幕后仰时内置摄像头对准桌面（键盘/水瓶），人员走动的区域完全不在画面内；"人经过"根本没进入镜头。
- 修复（物理）：调整屏幕/摄像头角度让走道入镜；用 `--test-send` 把当前画面发到飞书确认朝向。
- 软件侧：watchdog 启动时会做"启动画面自检"，若首帧检测 0 人则打 WARNING 提示朝向；排查时用 `--debug` 看每帧 motion/det。

## 十一、守护进程"静默消失"：日志一片空白 ≠ 没检测到人，先确认进程还活着
- 现象：用户反馈"有人走过好几次却一条提醒都没有"，但 watchdog 日志一片空白。
- 排查顺序：(1) 进程在不在（`Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'"`）；(2) 若进程没了 → 从最后一条日志到"现在"之间**没有任何监控**，人走过当然不提醒——先查为什么没人拉起来；(3) 若进程在 → 看心跳/`--debug` 逐帧决策。
- 实测：某次 watchdog+supervisor 在 10:43–13:05 双双静默消失（无退出日志，疑似被手动结束），期间有人多次经过 → 零提醒。**不是检测坏了，是根本没在跑。**
- 修复：watchdog 加**心跳日志**（默认每 60 秒一条 `心跳 state=... bright=...`，`heartbeat_secs` 可配）——静默期可观测；supervisor 写 `logs\supervisor.log`（启动/退出码/重启间隔/停止），崩溃重启有据可查。
- 验证链路顺序：先 `--test-send`（相机+hermes+飞书全通）→ 再 `--debug --duration N` 观察逐帧 motion/det → 最后真人走动做端到端。链路任一环断都有明确日志，别停留在"没提醒"的表象。

## 十二、停留时长被高估：把"离场确认等待"算进了停留时间
- 现象：用户反馈"我只停留了 5 秒，却显示 17 秒"。
- 根因：旧版 `_leave_event` 用 `离开通知发出时刻 - 出现时刻` 计算时长；离开通知要在人消失 5 秒（`exit_confirm_secs`）**之后**才发出，等于把离场确认等待也算进了"停留"。
- 实测案例：13:27:17 检出 → 13:27:24 发出现（6 秒采集窗口结束）→ 13:27:29.8 最后在场 → 13:27:34.8 发离开、显示 16.6 秒；其中约 5 秒是离场确认等待，其余是走进画面到通知的时间。
- 修复（v2.3.0）：跟踪"最后在场时刻"（`_last_present`），时长 = `最后在场 - 出现时刻`（不含离场确认）；离开日志追加 `出现 <时间> → 离开 <时间>`。若用户希望"从出现通知发出后才开始计时"，可把起始点改为 `capture_until`（采集窗口结束时刻）。
- 排查要点：先看日志"事件[离开]"行与心跳/`--debug`，确认是计时口径问题还是真的长时间在场；不要只凭用户感觉下结论。
