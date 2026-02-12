@echo off
echo ========================================
echo RESTORE TEXT-ONLY BOT
echo ========================================
echo.

cd /d d:\app-chi-tieu

echo [1/3] Cleaning up...
git rm main.py templates/index.html static/style.css static/script.js
git add .
echo.

echo [2/3] Committing...
git commit -m "Revert to Text-Only Bot (Simple Polling)"
echo.

echo [3/3] Pushing to GitHub...
git push
echo.

echo ========================================
echo DONE!
echo ========================================
echo Render will redeploy automatically.
echo Bot is now running in Simple Polling mode.
echo.
pause
