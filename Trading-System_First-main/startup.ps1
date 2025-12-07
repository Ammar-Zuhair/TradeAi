# Startup Script for MetaTrader5 Trading System
# This script initializes the environment and starts the trading system

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MT5 Trading System Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file from .env.example" -ForegroundColor Yellow
    Write-Host "Copy .env.example to .env and fill in your MT5 credentials" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ .env file found" -ForegroundColor Green

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
        Write-Host "  Loaded: $name" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "System Information" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Python Version: $(python --version)" -ForegroundColor White
Write-Host "Working Directory: $(Get-Location)" -ForegroundColor White
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host ""

# Check required files
$requiredFiles = @(
    "Run_System.py",
    "getDataAndVoting.py",
    "getNews.py",
    "models",
    "scalers"
)

Write-Host "Checking required files..." -ForegroundColor Cyan
$allFilesExist = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (MISSING)" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host ""
    Write-Host "ERROR: Some required files are missing!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Trading System..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start the trading system
try {
    python Run_System.py
} catch {
    Write-Host ""
    Write-Host "ERROR: Trading system crashed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
