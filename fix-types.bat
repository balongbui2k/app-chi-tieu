@echo off
echo ========================================
echo FIX STYPES & PUSH
echo ========================================
echo.

cd /d d:\app-chi-tieu

echo [1/3] Adding files...
git add expense_manager.py
echo.

echo [2/3] Committing...
git commit -m "Fix Invalid comparison error by forcing string types"
echo.

echo [3/3] Pushing to GitHub...
git push
echo.

echo ========================================
echo DONE!
echo ========================================
pause
