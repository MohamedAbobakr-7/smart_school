@echo off
echo Starting FastAPI Face Recognition Service...
echo.

cd face_recognition_service

if not exist main.py (
    echo Error: main.py not found in face_recognition_service directory
    pause
    exit /b 1
)

echo Starting service on http://localhost:8001...
echo Press Ctrl+C to stop the service
echo.

python main.py

pause




