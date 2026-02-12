@echo off
echo ========================================
echo PUSH WEBHOOK FIX
echo ========================================
echo.

cd /d d:\app-chi-tieu

echo [1/3] Adding files (main.py, config.py)...
git add main.py config.py
echo.

echo [2/3] Committing...
git commit -m "Switch to Webhook to fix Render Port Timeout"
echo.

echo [3/3] Pushing to GitHub...
git push
echo.

echo ========================================
echo DONE!
echo ========================================
echo Render will redeploy automatically.
echo.
echo IMPORTANT: In Render Dashboard, ensure WEB_APP_URL is set correctly:
echo    WEB_APP_URL = https://app-chi-tieu.onrender.com
echo.
pause
