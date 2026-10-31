@echo off
title Chronicle - iPad Server
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_ipad-open.ps1"
echo.
echo   Server stopped.
pause
