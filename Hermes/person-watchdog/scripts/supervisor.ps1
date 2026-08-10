# PersonWatchdog 守护脚本：watchdog 退出/崩溃后自动重启。
# 停止方式：创建 supervisor.stop 标记文件，或运行 install-task.ps1 -Uninstall。
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$StopFile = Join-Path $Root "supervisor.stop"
$VenvPythonw = Join-Path $Root ".venv\Scripts\pythonw.exe"
$Script = Join-Path $Root "watchdog.py"

$failCount = 0
while (-not (Test-Path $StopFile)) {
    if (-not (Test-Path $VenvPythonw)) {
        Start-Sleep -Seconds 30
        continue
    }
    $proc = Start-Process -FilePath $VenvPythonw -ArgumentList "`"$Script`"" -WorkingDirectory $Root -WindowStyle Hidden -PassThru
    # 等待退出（venv 启动器会在真实解释器结束后退出）
    try { $proc.WaitForExit() } catch { }
    if (Test-Path $StopFile) { break }
    $failCount++
    $code = 0
    try { $code = $proc.ExitCode } catch { }
    # 退出码 3 = 已有另一个 PersonWatchdog 实例在运行（手动/其它 supervisor），
    # 此时不需要急着重启，延长退避避免两个实例互相踢。
    if ($code -eq 3) {
        $delay = 60
    } elseif ($failCount -ge 3) {
        $delay = 30
    } else {
        $delay = 5
    }
    Start-Sleep -Seconds $delay
}
Remove-Item $StopFile -ErrorAction SilentlyContinue
