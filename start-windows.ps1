[CmdletBinding()]
param(
    [string]$Query = "",
    [ValidateRange(0, 3600)]
    [int]$LoginWaitSeconds = 0,
    [string]$OutputDir = "",
    [switch]$CheckOnly,
    [switch]$NoPause
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[boss-hr-start] $Message"
}

function Write-Failure {
    param([string]$Message)
    Write-Host "[boss-hr-start] ERROR: $Message" -ForegroundColor Red
}

function Finish-Script {
    param([int]$ExitCode)
    if (-not $NoPause) {
        Write-Host ""
        Read-Host "按 Enter 键关闭此窗口"
    }
    Pop-Location
    exit $ExitCode
}

Push-Location $PSScriptRoot

# 避免外部 Python 配置污染本项目，并统一中文输出编码。
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$ProjectOutputDir = Join-Path $PSScriptRoot "boss-hr-output"
if ($OutputDir) {
    $env:BOSS_HR_OUTPUT_DIR = [System.IO.Path]::GetFullPath($OutputDir)
} elseif (-not $env:BOSS_HR_OUTPUT_DIR) {
    $env:BOSS_HR_OUTPUT_DIR = $ProjectOutputDir
}
if (-not $CheckOnly -and -not (Test-Path -LiteralPath $env:BOSS_HR_OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $env:BOSS_HR_OUTPUT_DIR -Force | Out-Null
}

$PythonExe = $null
$PythonPrefix = @()
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $venvPython) {
    $PythonExe = $venvPython
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonExe = (Get-Command py).Source
    $PythonPrefix = @("-3")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = (Get-Command python).Source
} else {
    Write-Failure "未找到 Python 3。请先安装 Python 3.10+，再运行 install-windows.bat。"
    Finish-Script 1
}

function Invoke-BossHr {
    param([string[]]$Arguments)
    $lines = @(& $PythonExe @PythonPrefix "-X" "utf8" "-m" "boss_hr" @Arguments)
    $exitCode = $LASTEXITCODE
    foreach ($line in $lines) {
        Write-Host $line
    }
    return @{
        ExitCode = $exitCode
        Output = $lines
    }
}

Write-Step "项目目录：$PSScriptRoot"
Write-Step "Python：$PythonExe"
Write-Step "输出目录：$env:BOSS_HR_OUTPUT_DIR"

& $PythonExe @PythonPrefix "-c" "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Failure "需要 Python 3.10 或更高版本。"
    Finish-Script 1
}

& $PythonExe @PythonPrefix "-c" "import boss_hr, patchright"
if ($LASTEXITCODE -ne 0) {
    Write-Failure "项目或 patchright 尚未安装。请先运行 install-windows.bat。"
    Finish-Script 1
}

Write-Step "检查本地运行环境……"
$localCheck = Invoke-BossHr -Arguments @("doctor", "--skip-browser")
if ($localCheck.ExitCode -ne 0) {
    Write-Failure "本地环境检查失败。"
    Finish-Script $localCheck.ExitCode
}

if ($CheckOnly) {
    Write-Step "检查完成；未启动浏览器，也未连接 BOSS。"
    Finish-Script 0
}

if ($Query) {
    Write-Step "启动岗位任务：$Query"
    $startResult = Invoke-BossHr -Arguments @(
        "start", $Query,
        "--login-wait-seconds", [string]$LoginWaitSeconds
    )

    $payload = $null
    $jsonLine = @($startResult.Output | Where-Object { $_ -and $_.Trim().StartsWith("{") } | Select-Object -Last 1)
    if ($jsonLine.Count -gt 0) {
        try {
            $payload = $jsonLine[0] | ConvertFrom-Json
        } catch {
            Write-Warning "无法解析 CLI 返回的 JSON；请根据上方原始输出处理。"
        }
    }

    $status = ""
    if ($null -ne $payload -and $payload.PSObject.Properties.Name -contains "status") {
        $status = [string]$payload.status
    }

    if ($status -eq "waiting_user_login") {
        Write-Host ""
        Write-Step "专用 Edge 已打开。请完成 BOSS 招聘者登录，再用同一 Query 重跑本脚本。"
    } elseif ($status -eq "waiting_user_confirmation") {
        Write-Host ""
        Write-Step "已创建筛选任务，并停在人工确认门。"
        Write-Host "  run_id: $($payload.run_id)"
        Write-Host "  job_name: $($payload.job_name)"
        Write-Host "  encrypt_job_id: $($payload.encrypt_job_id)"
        Write-Host "请先在 BOSS 推荐牛人页面调整筛选条件，再按操作说明执行 confirm。"
    } elseif ($startResult.ExitCode -ne 0) {
        Write-Failure "岗位任务启动失败。"
    }

    Write-Host "本脚本不会自动执行 confirm、fetch、score、report 或 greet。"
    Finish-Script $startResult.ExitCode
}

# 未指定岗位时，只准备专用 Edge 和登录页，不创建筛选 run。
& $PythonExe @PythonPrefix "-c" "from boss_hr.adapters.browser_preflight import check_cdp_port_listening; raise SystemExit(0 if check_cdp_port_listening() else 1)"
$cdpReady = ($LASTEXITCODE -eq 0)

if (-not $cdpReady) {
    Write-Step "未检测到 9222 端口，正在启动专用 Edge……"
    $launchResult = Invoke-BossHr -Arguments @("doctor", "--launch-edge")
    # 未登录时 doctor 可能返回非零；只要随后能打开页面，就允许用户登录。
} else {
    Write-Step "检测到已运行的专用 Edge，直接复用。"
}

$openCode = "from boss_hr.adapters.browser_environment import _open_login_page; ok, err = _open_login_page(); print('BOSS_PAGE_OPENED' if ok else 'BOSS_PAGE_OPEN_FAILED: ' + str(err)); raise SystemExit(0 if ok else 1)"
& $PythonExe @PythonPrefix "-X" "utf8" "-c" $openCode
if ($LASTEXITCODE -ne 0) {
    Write-Failure "未能打开 BOSS 招聘者页面。请运行 python -X utf8 -m boss_hr doctor 查看诊断。"
    Finish-Script 1
}

Write-Host ""
Write-Step "专用 Edge 已就绪，登录状态保存在 %LOCALAPPDATA%\boss-hr-edge-profile。"
Write-Host "登录后可运行："
Write-Host '  .\start-windows.ps1 -Query "AI应用工程师"'
Write-Host "本次未创建筛选任务、未读取简历、未发送招呼。"
Finish-Script 0
