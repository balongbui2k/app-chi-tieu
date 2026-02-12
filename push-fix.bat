@echo off
echo ========================================
echo PUSH CODE UPDATE LEN GITHUB
echo ========================================
echo.

cd /d d:\app-chi-tieu

echo [1/3] Them file requirements.txt...
git add requirements.txt
echo.

echo [2/3] Commit...
git commit -m "Add missing requirements.txt"
echo.

echo [3/3] Push len GitHub...
git push
echo.

echo ========================================
echo HOAN THANH!
echo ========================================
echo.
echo Render se tu dong deploy lai trong 1-2 phut.
echo Kiem tra log tren Render de xem tien trinh!
echo.
pause
