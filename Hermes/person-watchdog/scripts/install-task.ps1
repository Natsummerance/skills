# PersonWatchdog 计划任务：注册 / 注销登录时自动运行（经 supervisor.ps1 守护，崩溃自动重启）
param([switch]$Uninstall)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$TaskName = "PersonWatchdog"
$Pythonw = Join-Path $Root ".venv\Scripts\pythonw.exe"
$Script = Join-Path $Root "watchdog.py"
$Supervisor = Join-Path $Root "supervisor.ps1"
$StopFile = Join-Path $Root "supervisor.stop"

# 注册计划任务需要管理员权限，自动请求提权
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    if ($Uninstall) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Remove-Item $StopFile -ErrorAction SilentlyContinue
        Write-Host "已注销计划任务 $TaskName"
        exit 0
    }
    Write-Host "注册计划任务需要管理员权限，正在请求提权（请在弹出的 UAC 对话框中选择“是”）..."
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"")
    try {
        Start-Process -FilePath "powershell.exe" -ArgumentList $argList -Verb RunAs -Wait
        exit 0
    } catch {
        Write-Host ""
        Write-Host "提权失败或被取消。请手动以管理员身份运行："
        Write-Host "  右键开始菜单 -> Windows PowerShell(管理员)，然后执行："
        Write-Host "  cd $Root"
        Write-Host "  .\install-task.ps1"
        exit 1
    }
}

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Remove-Item $StopFile -ErrorAction SilentlyContinue
    Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -like '*person-watchdog*watchdog.py*' } | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Write-Host "已注销计划任务 $TaskName 并停止 watchdog"
    exit 0
}

if (-not (Test-Path $Pythonw)) { Write-Error "未找到 $Pythonw，请先运行 setup.ps1"; exit 1 }
if (-not (Test-Path $Script)) { Write-Error "未找到 $Script"; exit 1 }
if (-not (Test-Path $Supervisor)) { Write-Error "未找到 $Supervisor"; exit 1 }
Remove-Item $StopFile -ErrorAction SilentlyContinue

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Supervisor`"" -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "PersonWatchdog：检测摄像头前经过的人并发送飞书通知（supervisor 守护）" -Force | Out-Null
Write-Host "已注册计划任务 $TaskName（登录时自动启动，supervisor 守护，隐藏窗口）"
Write-Host "如需注销： .\install-task.ps1 -Uninstall"
