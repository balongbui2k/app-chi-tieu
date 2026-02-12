# Expense categories and their keywords for automatic classification

CATEGORIES = {
    "Ăn uống": ["cơm", "phở", "bún", "mì", "cafe", "nước", "snack", "trà sữa", "ăn", "sáng", "trưa", "tối", "nhậu", "tiệc"],
    "Xăng xe": ["xăng", "dầu", "gửi xe", "rửa xe", "sửa xe", "thay nhớt", "grab", "taxi", "bus", "xe"],
    "Mua sắm": ["quần áo", "giày", "dép", "mỹ phẩm", "siêu thị", "shopee", "lazada", "tiki", "đồ gia dụng", "mua"],
    "Giải trí": ["phim", "game", "netflix", "du lịch", "vé", "hát", "karaoke"],
    "Giáo dục": ["học phí", "sách", "vở", "khóa học", "bút"],
    "Sức khỏe": ["thuốc", "khám", "bệnh viện", "gym", "yoga"],
    "Nhà cửa": ["tiền điện", "tiền nước", "internet", "vệ sinh", "thuê nhà", "rác"],
    "Khác": []  # Default category if no keywords match
}

DEFAULT_CATEGORY = "Khác"

def classify_expense(description):
    """Classify expense based on description using keywords."""
    description = description.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in description for keyword in keywords):
            return category
    return DEFAULT_CATEGORY
