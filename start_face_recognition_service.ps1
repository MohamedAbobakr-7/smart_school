# Start FastAPI Face Recognition Service
Write-Host "Starting FastAPI Face Recognition Service..." -ForegroundColor Cyan
Write-Host ""

# Change to service directory
Set-Location face_recognition_service

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if main.py exists
if (-not (Test-Path "main.py")) {
    Write-Host "Error: main.py not found in face_recognition_service directory" -ForegroundColor Red
    exit 1
}

# Start the service
Write-Host ""
Write-Host "Starting service on http://localhost:8001..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
Write-Host ""

python main.py




