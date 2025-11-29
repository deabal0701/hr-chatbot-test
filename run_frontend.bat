@echo off
echo ========================================
echo   HR Chatbot Frontend Dev Server
echo ========================================
echo.
echo Starting Vue.js dev server on http://localhost:3000
echo API Server: http://localhost:8000
echo.
cd /d "%~dp0frontend"
npm run dev
