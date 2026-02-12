@echo off
echo ========================================
echo PUSH MINI APP UPDATE
echo ========================================
echo.

cd /d d:\app-chi-tieu

echo [1/3] Adding files (main.py, static/, templates/)...
git add .
echo.

echo [2/3] Committing...
git commit -m "Convert to Telegram Mini App with FastAPI"
echo.

echo [3/3] Pushing to GitHub...
git push
echo.

echo ========================================
echo DONE!
echo ========================================
echo Render will redeploy automatically.
echo.
echo IMPORTANT: In Render Dashboard:
echo 1. Add Environment Variable:
echo    WEB_APP_URL = https://expense-bot.onrender.com (or your actual URL)
echo 2. Check Logs to ensure FastAPI starts correctly.
echo.
pause
