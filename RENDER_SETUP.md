# Hướng Dẫn Deploy Bot Lên Render.com - ĐơN Giản Nhất!

## 🚀 Render.com - Deploy Trong 5 Phút!

- ✅ **MIỄN PHÍ** - 750 giờ/tháng (đủ chạy cả tháng)
- ✅ **Cực kỳ đơn giản** - Không cần SSH, không cần terminal
- ✅ **Không cần thẻ tín dụng**
- ✅ **Tự động deploy** khi push code lên GitHub
- ⚠️ Bot sẽ "ngủ" sau 15 phút không hoạt động (có cách fix)

---

## Phần 1: Chuẩn Bị Code Trên GitHub

### Bước 1: Tạo GitHub Repository
1. Truy cập: https://github.com/new
2. **Repository name**: `expense-bot`
3. Chọn **Private** (để bảo mật token)
4. Click **"Create repository"**

### Bước 2: Push Code Lên GitHub
Mở Command Prompt trong thư mục `d:\app-chi-tieu`:

```bash
# Khởi tạo git (nếu chưa có)
git init

# Thêm tất cả files
git add .

# Commit
git commit -m "Initial commit"

# Thêm remote (thay YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/expense-bot.git

# Push
git branch -M main
git push -u origin main
```

**Lưu ý:** File `.gitignore` đã có sẵn để tránh upload nhầm dữ liệu.

---

## Phần 2: Deploy Lên Render.com

### Bước 3: Đăng Ký Render.com
1. Truy cập: https://render.com/
2. Click **"Get Started"** hoặc **"Sign Up"**
3. Chọn **"Sign up with GitHub"**
4. Đăng nhập GitHub và cho phép Render truy cập

### Bước 4: Tạo Web Service
1. Sau khi đăng nhập, click **"New +"** (góc trên bên phải)
2. Chọn **"Web Service"**
3. Click **"Connect a repository"**
4. Tìm và chọn repository `expense-bot`
5. Click **"Connect"**

### Bước 5: Cấu Hình Service

**Name**: `expense-bot` (hoặc tên bất kỳ)

**Region**: Singapore (nếu có) hoặc Oregon

**Branch**: `main`

**Runtime**: **Python 3**

**Build Command**:
```bash
pip install -r requirements.txt
```

**Start Command**:
```bash
python bot.py
```

**Instance Type**: **Free** ← Chọn cái này!

### Bước 6: Thêm Environment Variables (Tùy chọn)
Nếu bạn muốn giữ token bảo mật hơn:

1. Scroll xuống **"Environment Variables"**
2. Click **"Add Environment Variable"**
3. Thêm:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: Token của bạn
4. Thêm:
   - Key: `AUTHORIZED_USER_IDS`
   - Value: `2115787819`

**Sau đó sửa `config.py`:**
```python
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
AUTHORIZED_USER_IDS = [int(os.getenv("AUTHORIZED_USER_IDS", "2115787819"))]
```

### Bước 7: Deploy!
1. Click **"Create Web Service"** ở cuối trang
2. Render sẽ tự động:
   - Clone code từ GitHub
   - Cài dependencies
   - Chạy bot
3. Đợi 2-3 phút để deploy hoàn tất

### Bước 8: Kiểm Tra
1. Trong trang Service, xem **"Logs"**
2. Nếu thấy `Bot is running...` → **Thành công!** ✅
3. Mở Telegram, gửi `/start` cho bot

---

## Phần 3: Giải Quyết Vấn Đề "Ngủ"

Render free tier sẽ tắt bot sau 15 phút không có request HTTP. Để bot luôn chạy:

### Giải pháp 1: Thêm Health Check Endpoint (Khuyên dùng)

**Sửa `bot.py`**, thêm vào cuối file (trước `if __name__ == '__main__':`):

```python
from flask import Flask
import threading

# Tạo Flask app cho health check
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Chạy Flask trong thread riêng
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
```

**Cập nhật `requirements.txt`**, thêm dòng:
```
flask
```

**Sau đó push code:**
```bash
git add .
git commit -m "Add health check endpoint"
git push
```

Render sẽ tự động deploy lại!

### Giải pháp 2: Dùng Cron Job Miễn Phí

1. Truy cập: https://cron-job.org/
2. Đăng ký tài khoản miễn phí
3. Tạo cron job mới:
   - **Title**: Ping Expense Bot
   - **URL**: `https://expense-bot.onrender.com/health`
   - **Schedule**: Every 10 minutes
4. Save

Bot sẽ được "đánh thức" mỗi 10 phút!

---

## Phần 4: Quản Lý Bot

### Xem Logs
1. Vào trang Service trên Render
2. Click tab **"Logs"**
3. Xem log realtime

### Khởi Động Lại Bot
1. Click **"Manual Deploy"** → **"Deploy latest commit"**
2. Hoặc push code mới lên GitHub (tự động deploy)

### Cập Nhật Code
```bash
# Sửa code trên máy local
# Sau đó:
git add .
git commit -m "Update features"
git push
```

Render tự động deploy trong 2-3 phút!

### Xem Dữ Liệu
Render không lưu file persistent, nên dữ liệu Excel sẽ **MẤT** khi redeploy!

**Giải pháp:**
- Dùng `/export` để tải file Excel về thường xuyên
- Hoặc dùng Google Drive/Dropbox để lưu (cần code thêm)

---

## Phần 5: Nâng Cấp (Tùy chọn)

### Dùng Persistent Disk (Trả phí)
Nếu muốn lưu dữ liệu vĩnh viễn:
1. Trong Service settings → **"Disks"**
2. Add disk: `/home/ubuntu/expense-bot/data`
3. Chi phí: ~$1/tháng cho 1GB

---

## 🎉 Hoàn Thành!

Bot của bạn giờ chạy trên Render.com với:
- ✅ **$0** - Miễn phí
- ✅ Deploy tự động khi push code
- ✅ Không cần SSH, không cần terminal
- ⚠️ Cần health check để tránh "ngủ"

---

## So Sánh Render vs Oracle Cloud

| Tính năng | Render.com | Oracle Cloud |
|-----------|------------|--------------|
| **Chi phí** | $0 | $0 |
| **Độ đơn giản** | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Cấu hình** | 512MB RAM | 24GB RAM |
| **Persistent data** | ❌ (trừ khi trả $1/tháng) | ✅ |
| **Region** | USA/EU | Singapore |
| **Setup time** | 5 phút | 30 phút |

**Kết luận:** 
- **Render** = Đơn giản, nhanh, nhưng yếu hơn
- **Oracle** = Mạnh hơn nhiều, nhưng phức tạp hơn

Nếu bạn chỉ cần bot đơn giản → **Render**
Nếu muốn cấu hình mạnh + lưu dữ liệu → **Oracle**
