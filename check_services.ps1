# Quick service status checker
Write-Host "`n=== Service Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Check Django
try {
    $django = Invoke-WebRequest -Uri "http://localhost:8000/api/" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Django Backend: RUNNING (http://localhost:8000)" -ForegroundColor Green
} catch {
    Write-Host "✗ Django Backend: NOT RUNNING" -ForegroundColor Red
    Write-Host "  Start with: python manage.py runserver" -ForegroundColor Yellow
}

# Check FastAPI
try {
    $fastapi = Invoke-WebRequest -Uri "http://localhost:8001/" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ FastAPI Service: RUNNING (http://localhost:8001)" -ForegroundColor Green
} catch {
    Write-Host "✗ FastAPI Service: NOT RUNNING" -ForegroundColor Red
    Write-Host "  Start with: cd face_recognition_service && python main.py" -ForegroundColor Yellow
}

Write-Host ""




