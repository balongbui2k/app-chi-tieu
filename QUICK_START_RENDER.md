# 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER - NHANH NHẤT

## Bước 1: Push Code Lên GitHub

### Cách 1: Dùng Script Tự Động (Khuyên dùng)
1. Double-click file **`push-to-github.bat`**
2. Làm theo hướng dẫn trên màn hình
3. Nhập username GitHub của bạn khi được hỏi

### Cách 2: Chạy Thủ Công
Mở Command Prompt và chạy:

```bash
cd /d d:\app-chi-tieu

# Tạo repo trên GitHub trước: https://github.com/new
# Tên: app-chi-tieu, Private

git add .
git commit -m "Update config for Render deployment"
git remote add origin https://github.com/YOUR_USERNAME/app-chi-tieu.git
git branch -M main
git push -u origin main
```

---

## Bước 2: Deploy Trên Render

1. Truy cập: **https://render.com**
2. Click **"Sign up with GitHub"** (hoặc Login nếu đã có tài khoản)
3. Click **"New +"** → **"Web Service"**
4. Tìm và chọn repository **`app-chi-tieu`**
5. Click **"Connect"**

### Cấu hình:
- **Name**: `expense-bot` (hoặc tên bất kỳ)
- **Region**: Singapore (nếu có) hoặc Oregon
- **Branch**: `main`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py`
- **Instance Type**: **Free**

### Environment Variables (QUAN TRỌNG!):
Click **"Add Environment Variable"**, thêm 2 biến:

1. **Key**: `TELEGRAM_BOT_TOKEN`  
   **Value**: `8153679316:AAHug9W18qFkPCKG83nqj9YwCaYVJzgsHQU`

2. **Key**: `AUTHORIZED_USER_IDS`  
   **Value**: `2115787819`

### Deploy:
Click **"Create Web Service"** → Đợi 2-3 phút

---

## Bước 3: Kiểm Tra

1. Trong trang Service, xem tab **"Logs"**
2. Nếu thấy `Bot is running...` → **Thành công!** ✅
3. Mở Telegram, gửi `/start` cho bot

---

## ⚠️ Lưu Ý Quan Trọng

### Bot sẽ "ngủ" sau 15 phút
Render free tier tắt bot sau 15 phút không hoạt động.

**Giải pháp:** Dùng cron-job.org để ping bot mỗi 10 phút:
1. Đăng ký: https://cron-job.org
2. Tạo job mới:
   - URL: `https://expense-bot.onrender.com` (thay bằng URL của bạn)
   - Schedule: Every 10 minutes
3. Save

### Dữ liệu sẽ mất khi redeploy
Render không lưu file persistent miễn phí.

**Giải pháp:** Dùng `/export` thường xuyên để tải Excel về máy.

---

## 🎉 Xong!

Bot của bạn giờ chạy trên Render miễn phí!

Mọi thắc mắc, xem log tại tab **"Logs"** trên Render.
