# ChatBI API 启动脚本（Windows/PowerShell）
# 用法: 从 chatbi-application\ 根目录运行: .\scripts\start_api.ps1

# 切换到项目根目录
Set-Location "$PSScriptRoot\.."

Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        ChatBI API 启动脚本                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan

# 1. 检查 Python
Write-Host "[1/5] 检查 Python..." -ForegroundColor Yellow
python --version 2>$null || {
    Write-Host "❌ 未安装 Python" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python 已安装" -ForegroundColor Green

# 2. 检查虚拟环境
Write-Host "[2/5] 检查虚拟环境..." -ForegroundColor Yellow
if (Test-Path "venv") {
    & venv\Scripts\Activate.ps1
    Write-Host "✓ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "⚠ 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
    & venv\Scripts\Activate.ps1
    Write-Host "✓ 虚拟环境已创建" -ForegroundColor Green
}

# 3. 安装依赖
Write-Host "[3/5] 安装依赖..." -ForegroundColor Yellow
pip install -q -r requirements-api.txt
Write-Host "✓ 依赖已安装" -ForegroundColor Green

# 4. 检查环境变量
Write-Host "[4/5] 检查环境变量..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "⚠ .env 已创建，请编辑并设置 DEEPSEEK_API_KEY" -ForegroundColor Yellow
}
Write-Host "✓ 环境变量已加载" -ForegroundColor Green

# 5. 启动 API
Write-Host "[5/5] 启动 API 服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host "ChatBI API 运行中：http://localhost:8000" -ForegroundColor Green
Write-Host "API 文档：http://localhost:8000/docs" -ForegroundColor Green
Write-Host "按 CTRL+C 停止服务" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

uvicorn api:app --host 0.0.0.0 --port 8000 --reload
