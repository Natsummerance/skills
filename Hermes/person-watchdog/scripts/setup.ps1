# PersonWatchdog 安装脚本：创建独立 venv、安装依赖、下载 YOLO11m + YuNet 人脸模型
param(
    [string]$Model = "yolo11m.onnx",
    [switch]$SkipVenv,
    [switch]$SkipModel,
    [switch]$SkipFaceModel
)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$ModelsDir = Join-Path $Root "models"
$ModelPath = Join-Path $ModelsDir $Model
$FaceModelName = "face_detection_yunet_2023mar.onnx"
$FaceModelPath = Join-Path $ModelsDir $FaceModelName

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# 1. 创建虚拟环境并安装依赖
if ($SkipVenv) {
    Write-Step "跳过 venv 创建/依赖安装"
} else {
    if (-not (Test-Path $VenvPython)) {
        Write-Step "创建虚拟环境 .venv ..."
        $py = Get-Command python -ErrorAction SilentlyContinue
        if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
        if (-not $py) { throw "未找到 python，请先安装 Python 3.10+ 并加入 PATH" }
        & $py.Source -m venv (Join-Path $Root ".venv")
        if ($LASTEXITCODE -ne 0) { throw "venv 创建失败" }
    }
    Write-Step "安装依赖（onnxruntime / opencv / numpy）..."
    & $VenvPython -m pip install --disable-pip-version-check -q -r (Join-Path $Root "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "依赖安装失败" }
}

# 2. 下载模型（支持 -Model 指定 yolov8n/s/m.onnx 或 yolo11n/s/m.onnx）
if ($SkipModel) {
    Write-Step "跳过模型下载"
} elseif (Test-Path $ModelPath) {
    $mb = [math]::Round((Get-Item $ModelPath).Length / 1MB, 1)
    Write-Step "模型已存在: $ModelPath ($mb MB)"
} else {
    Write-Step "下载模型 $Model（约 77MB）..."
    New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null
    $urls = @(
        "https://github.com/ultralytics/assets/releases/download/v8.4.0/$Model"
    )
    $ok = $false
    foreach ($u in $urls) {
        try {
            Invoke-WebRequest -Uri $u -OutFile $ModelPath -UseBasicParsing -TimeoutSec 900
            $ok = $true
            break
        } catch {
            Write-Warning "Invoke-WebRequest 下载失败: $u -> $($_.Exception.Message)"
        }
        # 备用：curl.exe
        try {
            & curl.exe -L -s -o $ModelPath --connect-timeout 20 --max-time 900 $u
            if ((Test-Path $ModelPath) -and (Get-Item $ModelPath).Length -gt 1000000) {
                $ok = $true
                break
            }
        } catch {
            Write-Warning "curl 下载失败: $($_.Exception.Message)"
        }
    }
    if (-not $ok) { throw "模型下载失败，请检查网络后重试" }
}

# 3. 下载 YuNet 人脸模型（约 232KB；raw.githubusercontent 对 LFS 文件只返回指针，故优先用 HuggingFace）
if ($SkipFaceModel) {
    Write-Step "跳过人脸模型下载"
} elseif (Test-Path $FaceModelPath) {
    $fmb = [math]::Round((Get-Item $FaceModelPath).Length / 1KB, 1)
    Write-Step "人脸模型已存在: $FaceModelPath ($fmb KB)"
} else {
    Write-Step "下载人脸模型 $FaceModelName ..."
    New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null
    $faceUrls = @(
        "https://huggingface.co/opencv/face_detection_yunet/resolve/main/$FaceModelName",
        "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/$FaceModelName"
    )
    $faceOk = $false
    foreach ($fu in $faceUrls) {
        try {
            & curl.exe -L -s -o $FaceModelPath --connect-timeout 20 --max-time 300 $fu
            if ((Test-Path $FaceModelPath) -and (Get-Item $FaceModelPath).Length -gt 100000) {
                $faceOk = $true
                Write-Step "人脸模型下载完成: $((Get-Item $FaceModelPath).Length) bytes"
                break
            }
        } catch {
            Write-Warning "人脸模型下载失败: $fu -> $($_.Exception.Message)"
        }
    }
    if (-not $faceOk) { throw "人脸模型下载失败，请检查网络后重试" }
}

# 4. 验证模型可加载
Write-Step "验证模型可加载 ..."
& $VenvPython -c "import onnxruntime as ort; s = ort.InferenceSession(r'$ModelPath', providers=['CPUExecutionProvider']); print('OK 模型可加载:', s.get_inputs()[0].name, '->', s.get_outputs()[0].name)"
if ($LASTEXITCODE -ne 0) { throw "模型验证失败" }
if (Test-Path $FaceModelPath) {
    & $VenvPython -c "import cv2; d = cv2.FaceDetectorYN.create(r'$FaceModelPath', '', (320,320), 0.6, 0.3, 5000); print('OK 人脸模型可加载')"
    if ($LASTEXITCODE -ne 0) { throw "人脸模型验证失败" }
}

Write-Step "安装完成！"
Write-Host ""
Write-Host "  测试通知:      .venv\Scripts\python.exe watchdog.py --test-send"
Write-Host "  列出摄像头:    .venv\Scripts\python.exe watchdog.py --list-cameras"
Write-Host "  开始检测:      .venv\Scripts\python.exe watchdog.py"
Write-Host "  开机自启:      .\install-task.ps1"