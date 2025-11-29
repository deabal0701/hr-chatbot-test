@echo off
chcp 65001 >nul
echo ========================================
echo HR Chatbot Server 시작
echo ========================================

cd /d %~dp0

REM 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

if exist ".venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
)

echo.
echo uvicorn 서버 시작: http://localhost:8000
echo Swagger UI: http://localhost:8000/docs
echo ReDoc: http://localhost:8000/redoc
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
