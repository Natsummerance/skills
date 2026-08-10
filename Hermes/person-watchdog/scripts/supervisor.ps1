# PersonWatchdog 守护脚本：watchdog 退出/崩溃后自动重启。
# 停止方式：创建 supervisor.stop 标记文件，或运行 install-task.ps1 -Uninstall。
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$StopFile = Join-Path $Root "supervisor.stop"
$VenvPythonw = Join-Path $Root ".venv\Scripts\pythonw.exe"
$Script = Join-Path $Root "watchdog.py"

# 单 supervisor 互斥：已有一个 supervisor 在守护时，本实例直接退出，
# 避免两个 supervisor 反复拉起 watchdog 互相踢（配合 watchdog 退出码 3 的长退避）。
$svCreated = $false
$svMutex = $null
try {
    $svMutex = [System.Threading.Mutex]::new($false, "PersonWatchdogSupervisorMutex", [ref]$svCreated)
} catch {
    Write-Host "supervisor 互斥创建失败（继续运行）: $($_.Exception.Message)"
}
if ($svMutex -and -not $svCreated) {
    Write-Host "已有 PersonWatchdog supervisor 在运行，本实例退出"
    exit 0
}

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
if ($svMutex) { try { $svMutex.Dispose() } catch { } }
