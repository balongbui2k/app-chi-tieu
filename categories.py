import re

# Chia rõ ràng thành 2 nhóm chính: THU và CHI
INCOME_CATEGORIES = {
    "Thu nhập": ["lương", "thưởng", "thu nhập", "tiền về", "lãi", "đòi nợ", "trả nợ", "quà", "biếu", "tặng", "thu", "nhận"]
}

EXPENSE_CATEGORIES = {
    "Ăn uống": ["cơm", "phở", "bún", "mì", "cafe", "nước", "snack", "trà sữa", "ăn", "sáng", "trưa", "tối", "nhậu", "tiệc"],
    "Xăng xe": ["xăng", "dầu", "gửi xe", "rửa xe", "sửa xe", "thay nhớt", "grab", "taxi", "bus", "xe"],
    "Mua sắm": ["quần áo", "giày", "dép", "mỹ phẩm", "siêu thị", "shopee", "lazada", "tiki", "đồ gia dụng", "mua"],
    "Giải trí": ["phim", "game", "netflix", "du lịch", "vé", "hát", "karaoke"],
    "Giáo dục": ["học phí", "sách", "vở", "khóa học", "bút"],
    "Sức khỏe": ["thuốc", "khám", "bệnh viện", "gym", "yoga"],
    "Nhà cửa": ["tiền điện", "tiền nước", "internet", "vệ sinh", "thuê nhà", "rác", "tiền dịch vụ"],
    "Khác": []
}

# Gộp chung lại để Bot search, nhưng ưu tiên THU trước CHI
CATEGORIES = {**INCOME_CATEGORIES, **EXPENSE_CATEGORIES}

DEFAULT_CATEGORY = "Khác"

def classify_expense(description):
    """Phân loại thông minh: Ưu tiên Thu nhập và kiểm tra từ chính xác."""
    desc_lower = description.lower()
    
    # Duyệt qua từng danh mục
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            # Sử dụng Regex để tìm từ nguyên vẹn (\b) 
            # Giúp tránh lỗi "xăng" bị hiểu nhầm thành "ăn"
            if re.search(rf'\b{re.escape(kw)}\b', desc_lower):
                return category
                
    return DEFAULT_CATEGORY
