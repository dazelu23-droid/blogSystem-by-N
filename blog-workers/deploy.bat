@echo off
cd /d "%~dp0"
echo.
echo  Iron and Motion - Cloudflare Deploy
echo  ===================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"
echo.
pause
