# Telegram Expense Tracking Bot

Bot Telegram giúp bạn quản lý chi tiêu cá nhân một cách nhanh chóng và lưu trữ dữ liệu tập trung vào file Excel local.

## Tính năng chính

- **Ghi nhận nhanh**: Nhập `100k cơm` để lưu 100,000đ vào danh mục Ăn uống.
- **Tự động phân loại**: Nhận diện danh mục dựa trên từ khóa (xăng, cafe, shopee, ...).
- **Thống kê & Biểu đồ**: Xem chi tiêu theo ngày, tuần, tháng và biểu đồ hình quạt.
- **Quản lý dữ liệu**: Lưu trữ an toàn trong các file Excel offline (theo năm/tháng).
- **Báo cáo hàng tháng**: Tự động gửi báo cáo tổng kết vào ngày 5 hàng tháng.
- **Bảo mật**: Chỉ cho phép các User ID được cấu hình truy cập.

## Hướng dẫn cài đặt

1. **Yêu cầu**: Python 3.8+
2. **Cài đặt thư viện**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Cấu hình**:
   Mở file `config.py` và cập nhật:
   - `TELEGRAM_BOT_TOKEN`: Token lấy từ @BotFather.
   - `AUTHORIZED_USER_IDS`: Danh sách ID Telegram của bạn (và người thân nếu cần).
4. **Chạy Bot**:
   ```bash
   python bot.py
   ```

## Các lệnh điều khiển

- `/start` & `/help`: Hướng dẫn sử dụng.
- `/view` hoặc `/today`: Chi tiêu hôm nay.
- `/week`: Chi tiêu tuần này.
- `/month`: Tổng hợp chi tiêu tháng này.
- `/stats`: Biểu đồ chi tiêu tháng này.
- `/recent`: Xem 10 giao dịch gần nhất.
- `/search <từ khóa>`: Tìm kiếm giao dịch.
- `/edit <id> <tiền> <mô tả>`: Sửa giao dịch đã nhập.
- `/delete <id>`: Xóa giao dịch.
- `/export`: Tải file Excel của tháng hiện tại.

## Cấu trúc thư mục

```
app-chi-tieu/
├── bot.py                # Logic điều khiển bot
├── expense_manager.py    # Thao tác với Excel
├── categories.py         # Quy tắc phân loại
├── config.py             # Cấu hình bot & bảo mật
├── requirements.txt      # Thư viện cần thiết
├── data/                 # Thư mục lưu trữ Excel
└── README.md             # Tài liệu này
```

## Chú ý
Dữ liệu được lưu local trong thư mục `data/`. Hãy đảm bảo bạn sao lưu thư mục này thường xuyên.

## Deploy 24/7 trên VPS/Cloud

Để bot chạy liên tục 24/7, bạn cần deploy lên:
- **Google Cloud** (Free tier - miễn phí vĩnh viễn)
- **AWS EC2** (Free tier 12 tháng)
- **DigitalOcean** ($4/tháng)
- **Raspberry Pi** (mua 1 lần, dùng mãi mãi)

📖 **Xem hướng dẫn chi tiết:** [DEPLOY.md](DEPLOY.md)

### Quick Deploy (Linux VPS)
```bash
# Upload code lên VPS, sau đó chạy:
bash deploy.sh
```
