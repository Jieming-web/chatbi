# ChatBI API launch script (Windows/PowerShell)
# Usage: run from the chatbi-application\ repo root: .\scripts\start_api.ps1

# Switch to the project root
Set-Location "$PSScriptRoot\.."

Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         ChatBI API Launch Script          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan

# 1. Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
python --version 2>$null || {
    Write-Host "Python is not installed." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python is installed" -ForegroundColor Green

# 2. Check the virtual environment
Write-Host "[2/5] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    & venv\Scripts\Activate.ps1
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    & venv\Scripts\Activate.ps1
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# 3. Install dependencies
Write-Host "[3/5] Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements-api.txt
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# 4. Check environment variables
Write-Host "[4/5] Checking environment variables..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env was created. Please edit it and set DEEPSEEK_API_KEY." -ForegroundColor Yellow
}
Write-Host "✓ Environment variables loaded" -ForegroundColor Green

# 5. Start the API
Write-Host "[5/5] Starting the API service..." -ForegroundColor Yellow
Write-Host ""
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host "ChatBI API is running at: http://localhost:8000" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Press CTRL+C to stop the service" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

uvicorn api:app --host 0.0.0.0 --port 8000 --reload
