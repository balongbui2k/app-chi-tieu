@echo off
echo ========================================
echo PUSH FIX RUNTIME ERROR
echo ========================================
echo.

cd /d d:\app-chi-tieu

echo [1/3] Them file bot.py...
git add bot.py
echo.

echo [2/3] Commit...
git commit -m "Fix RuntimeError by using application.job_queue"
echo.

echo [3/3] Push len GitHub...
git push
echo.

echo ========================================
echo HOAN THANH!
echo ========================================
echo.
echo Render se tu dong deploy lai ngay lap tuc.
echo.
pause
