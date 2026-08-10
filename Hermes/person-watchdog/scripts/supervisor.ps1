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
    Wait-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if (Test-Path $StopFile) { break }
    $failCount++
    $delay = if ($failCount -ge 3) { 30 } else { 5 }
    Start-Sleep -Seconds $delay
}
Remove-Item $StopFile -ErrorAction SilentlyContinue
