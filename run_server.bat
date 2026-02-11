@echo off
chcp 65001 >nul
echo ========================================
echo   MUREUM Backend Server 시작
echo ========================================

cd /d %~dp0

REM Conda 가상환경 활성화
echo Conda 환경 활성화 중 (penv3.13-nlq)...
call conda activate penv3.13-nlq

echo.
echo uvicorn 서버 시작: http://localhost:19090
echo Swagger UI: http://localhost:19090/docs
echo ReDoc: http://localhost:19090/redoc
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

uvicorn app.main:app --host 0.0.0.0 --port 19090 --reload

pause
