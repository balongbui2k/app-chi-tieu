@echo off
echo ========================================
echo STRING-BASED DATE FIX (GUARANTEED)
echo ========================================
echo.

cd /d d:\app-chi-tieu

echo [1/3] Adding files...
git add bot.py expense_manager.py
echo.

echo [2/3] Committing...
git commit -m "Switch to string-based date matching for absolute reliability"
echo.

echo [3/3] Pushing to GitHub...
git push
echo.

echo ========================================
echo DONE!
echo ========================================
echo.
echo QUAN TRONG:
echo Bau gio HAY MO FILE GOOGLE SHEET, xoa sach du lieu di nhe.
echo De bot bat dau ghi ngay theo kieu moi: 2026-02-12
echo.
pause
