@echo off
echo ========================================
echo PUSH CODE LEN GITHUB
echo ========================================
echo.

cd /d d:\app-chi-tieu

echo [1/5] Kiem tra trang thai git...
git status
echo.

echo [2/5] Them tat ca files...
git add .
echo.

echo [3/5] Commit code...
git commit -m "Update config for Render deployment"
echo.

echo [4/5] Luu y: Ban can tao repository tren GitHub truoc!
echo Truy cap: https://github.com/new
echo Ten repository: app-chi-tieu
echo Chon: Private
echo.
pause

echo [5/5] Nhap username GitHub cua ban:
set /p GITHUB_USER="Username: "

echo.
echo Dang them remote va push...
git remote add origin https://github.com/%GITHUB_USER%/app-chi-tieu.git
git branch -M main
git push -u origin main

echo.
echo ========================================
echo HOAN THANH!
echo ========================================
echo.
echo Buoc tiep theo:
echo 1. Truy cap: https://render.com
echo 2. Dang nhap bang GitHub
echo 3. New Web Service
echo 4. Chon repository: app-chi-tieu
echo 5. Them Environment Variables:
echo    - TELEGRAM_BOT_TOKEN = 8153679316:AAHug9W18qFkPCKG83nqj9YwCaYVJzgsHQU
echo    - AUTHORIZED_USER_IDS = 2115787819
echo 6. Deploy!
echo.
pause
