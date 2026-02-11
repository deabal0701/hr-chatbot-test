@echo off
chcp 65001 >nul
echo ========================================
echo   MUREUM Frontend Dev Server
echo ========================================
echo.
echo Starting Vue.js dev server on http://localhost:19080
echo API Server: http://localhost:19090
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo ========================================
echo.
cd /d "%~dp0frontend"
npm run dev
