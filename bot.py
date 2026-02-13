import logging
import asyncio
from datetime import datetime, timedelta, time, date
import re
import matplotlib.pyplot as plt
import io
import os
import pytz

# Config Vietnam Timezone
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import config
from expense_manager import ExpenseManager
from keep_alive import keep_alive  # Import keep_alive server

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

expense_mgr = ExpenseManager()

# Track processed updates to prevent duplicates
processed_updates = set()

# Cache for today's transactions to be independent of Google Sheets reading issues
# Logic: Simple, Telegram-only, resets daily
today_cache = {
    'date': None, # Format: YYYY-MM-DD
    'items': []   # List of dicts: {'amount': int, 'desc': str}
}

def authorized_only(func):
    """Decorator to check if the user is authorized."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in config.AUTHORIZED_USER_IDS:
            await update.message.reply_text("⛔ Bạn không có quyền sử dụng bot này.")
            return
        return await func(update, context)
    return wrapper

@authorized_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    help_text = (
        "👋 Chào mừng bạn đến với Bot Quản Lý Chi Tiêu!\n\n"
        "Cơ chế nhập liệu:\n"
        "Gửi tin nhắn như: `100k cơm` hoặc `50 xăng`\n"
        "Ghi cho người khác: `100k cơm @vợ` hoặc `50k xăng @con`\n\n"
        "Các lệnh hỗ trợ:\n"
        "/today - Xem chi tiêu hôm nay\n"
        "/week - Xem chi tiêu tuần này\n"
        "/month - Xem chi tiêu tháng này\n"
        "/stats - Biểu đồ chi tiêu\n"
        "/recent - 10 giao dịch gần nhất\n"
        "/search <từ khóa> - Tìm kiếm\n"
        "/edit <id> <tiền> <mô tả> - Sửa\n"
        "/delete <id> - Xóa\n"
        "/person <tên> - Xem chi tiêu theo người\n"
        "/help - Xem lại hướng dẫn này"
    )
    # Remove Mini App button, restore default keyboard (none)
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())

@authorized_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await start(update, context)

@authorized_only
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the user message for expense recording."""
    if not update.message or not update.message.text:
        return

    # Check for duplicate updates
    if update.update_id in processed_updates:
        logger.info(f"Ignored duplicate update: {update.update_id}")
        return
    processed_updates.add(update.update_id)
    
    # Keep the set size manageable (keep last 500 IDs)
    if len(processed_updates) > 500:
        # Simple way to prune: convert to list, sort, keep newest
        sorted_ids = sorted(list(processed_updates))
        for old_id in sorted_ids[:-400]:
            processed_updates.remove(old_id)

    text = update.message.text.strip()
    
    # Regex: number + optional 'k'/'m' + description + optional @person + optional #date
    # Matches: "100k cơm", "50 xăng @vợ", "200 bỉm #hôm qua", "300 bỉm #12/02"
    match = re.match(r'^(\d+)(k|m|K|M)?\s+(.+?)(?:\s+@(\w+))?(?:\s+#([\d/]+|hôm qua|hom qua))?$', text)
    
    if not match:
        await update.message.reply_text("❓ Sai định dạng.\nVí dụ: `100k cơm`, `50 xăng @vợ`, `200 bỉm #hôm qua`, `300 bỉm #12/02`", parse_mode='Markdown')
        return
        
    amount_raw = match.group(1)
    suffix = match.group(2)
    description = match.group(3)
    person = match.group(4) if match.group(4) else "Bản thân"
    date_flag = match.group(5)

    # Process date adjustment
    record_date = datetime.now(vn_tz)
    if date_flag:
        date_flag = date_flag.lower()
        if date_flag in ["hôm qua", "hom qua"]:
            record_date -= timedelta(days=1)
        elif "/" in date_flag:
            try:
                # Expecting dd/mm (uses current year)
                day, month = map(int, date_flag.split("/"))
                record_date = record_date.replace(day=day, month=month)
            except:
                await update.message.reply_text("❌ Ngày không hợp lệ (định dạng dd/mm).")
                return

    amount = int(amount_raw)
    if suffix and suffix.lower() == 'k':
        amount *= 1000
    elif suffix and suffix.lower() == 'm':
        amount *= 1000000
        
    try:
        # Add expense with Vietnam time
        now_vn = datetime.now(vn_tz)
        today_str = now_vn.strftime("%Y-%m-%d")
        record_date_str = record_date.strftime("%Y-%m-%d")
        
        # Reset cache if day changed
        if today_cache['date'] != today_str:
            today_cache['date'] = today_str
            today_cache['items'] = []

        # Update Cache if it's actually for today
        display_balance = ""
        if record_date_str == today_str:
            # Store with sign for simple sum
            signed_amount = amount if record['Danh mục'] == "Thu nhập" else -amount
            today_cache['items'].append({'amount': signed_amount, 'desc': description, 'cat': record['Danh mục']})
            
            # Calculate daily stats
            today_income = sum(item['amount'] for item in today_cache['items'] if item['amount'] > 0)
            today_spent = abs(sum(item['amount'] for item in today_cache['items'] if item['amount'] < 0))
            daily_net = today_income - today_spent
            
            display_balance = (
                f"📊 **Hôm nay:**\n"
                f"➕ Thu: {today_income:,}\n"
                f"➖ Chi: {today_spent:,}\n"
                f"💰 Còn: {daily_net:,} {config.CURRENCY}\n"
            )

        response = (
            f"✅ **Đã ghi nhận!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Người: {record['Người']}\n"
            f"💰 Số tiền: {amount:,} {config.CURRENCY}\n"
            f"📂 Danh mục: {record['Danh mục']}\n"
            f"📝 Mô tả: {description}\n"
            f"📅 Ngày: {record['Ngày']}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{display_balance}"
            f"📅 ID: `{record['ID']}`"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error recording expense: {e}")
        await update.message.reply_text("❌ Có lỗi xảy ra khi lưu dữ liệu.")

@authorized_only
async def view_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View today's expenses using the internal cache."""
    now = datetime.now(vn_tz)
    today_str = now.strftime("%Y-%m-%d")
    
    # Ensure cache is for today
    if today_cache['date'] != today_str:
        # If cache is old or empty, we try to load from sheet ONCE or just show empty
        # But per user request "separate", we stick to cache
        today_cache['date'] = today_str
        today_cache['items'] = []

    items = today_cache['items']
    
    if not items:
        await update.message.reply_text(f"📅 Hôm nay ({now.strftime('%d/%m/%Y')}) bạn chưa chi tiêu gì.")
        return
        
    today_income = sum(item['amount'] for item in items if item['amount'] > 0)
    today_spent = abs(sum(item['amount'] for item in items if item['amount'] < 0))
    net = today_income - today_spent
    
    date_str = now.strftime("%d/%m/%Y")
    report = f"📅 **Tài chính hôm nay ({date_str}):**\n\n"
    for item in items:
        sign = "➕" if item['amount'] > 0 else "➖"
        report += f"{sign} {abs(item['amount']):,} đ - {item['desc']}\n"
    
    report += "━━━━━━━━━━━━━━━━━━━━\n"
    report += f"➕ Tổng Thu: {today_income:,} đ\n"
    report += f"➖ Tổng Chi: {today_spent:,} đ\n"
    report += f"💰 **Số dư: {net:,} {config.CURRENCY}**"
    await update.message.reply_text(report, parse_mode='Markdown')

@authorized_only
async def view_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View this week's expenses."""
    now = datetime.now(vn_tz)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = datetime(start_of_week.year, start_of_week.month, start_of_week.day)
    df = expense_mgr.get_expenses(start_date=start_of_week, end_date=now)
    
    # Calculate Income vs Spent
    income_df = df[df['Danh mục'] == "Thu nhập"]
    spent_df = df[df['Danh mục'] != "Thu nhập"]
    
    total_income = income_df['Số tiền'].sum()
    total_spent = spent_df['Số tiền'].sum()
    net = total_income - total_spent

    report = "📅 **Tài chính tuần này:**\n\n"
    for _, row in df.iterrows():
        sign = "➕" if row['Danh mục'] == "Thu nhập" else "➖"
        report += f"{sign} {row['Ngày']} - {row['Số tiền']:,} đ: {row['Mô tả']}\n"
    
    report += "━━━━━━━━━━━━━━━━━━━━\n"
    report += f"➕ Tổng Thu: {total_income:,} đ\n"
    report += f"➖ Tổng Chi: {total_spent:,} đ\n"
    report += f"💰 **Số dư: {net:,} {config.CURRENCY}**"
    await update.message.reply_text(report, parse_mode='Markdown')


@authorized_only
async def view_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View this month's summary."""
    summary = expense_mgr.get_monthly_summary()
    if not summary:
        await update.message.reply_text("📅 Tháng này chưa có dữ liệu chi tiêu.")
        return
        
    report = f"📊 **TÀI CHÍNH THÁNG {summary['month']}/{summary['year']}**\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    report += f"📈 **Thu nhập:** {summary['income']:,} {config.CURRENCY}\n"
    report += "📉 **Chi tiêu chi tiết:**\n"
    
    for cat, amt in summary['categories'].items():
        if cat == "Thu nhập": continue
        percent = (amt / summary['total_spent']) * 100 if summary['total_spent'] > 0 else 0
        report += f"• {cat}: {amt:,} {config.CURRENCY} ({percent:.1f}%)\n"
        
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += f"➖ Tổng chi: {summary['total_spent']:,} {config.CURRENCY}\n"
    report += f"💰 **Số dư tháng: {summary['net']:,} {config.CURRENCY}**"
    
    await update.message.reply_text(report, parse_mode='Markdown')

@authorized_only
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send a pie chart of monthly expenses."""
    summary = expense_mgr.get_monthly_summary()
    if not summary:
        await update.message.reply_text("📅 Không có dữ liệu để tạo biểu đồ.")
        return
        
    # Create pie chart
    labels = list(summary['categories'].keys())
    values = list(summary['categories'].values())
    
    plt.figure(figsize=(8, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title(f"Chi tiêu tháng {summary['month']}/{summary['year']}")
    
    # Save chart to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    await update.message.reply_photo(photo=buf, caption=f"📊 Biểu đồ chi tiêu tháng {summary['month']}/{summary['year']}")


@authorized_only
async def recent_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show last 10 transactions."""
    df = expense_mgr.get_expenses()
    if df.empty:
        await update.message.reply_text("📅 Chưa có dữ liệu chi tiêu.")
        return
        
    recent = df.tail(10)
    report = "🕒 **10 Giao dịch gần nhất:**\n\n"
    for _, row in recent.iloc[::-1].iterrows(): # Reverse to show newest first
        report += f"ID: `{row['ID']}` | {row['Số tiền']:,} đ | {row['Mô tả']}\n"
        
    await update.message.reply_text(report, parse_mode='Markdown')

@authorized_only
async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete an expense record by ID."""
    if not context.args:
        await update.message.reply_text("📎 Vui lòng nhập ID: `/delete <id>`", parse_mode='Markdown')
        return
    
    try:
        expense_id = int(context.args[0])
        if expense_mgr.delete_expense(expense_id):
            await update.message.reply_text(f"✅ Đã xóa giao dịch ID: `{expense_id}`", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Không tìm thấy giao dịch với ID này.")
    except ValueError:
        await update.message.reply_text("❌ ID không hợp lệ.")

@authorized_only
async def edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Edit an expense record: /edit <id> <amount> <description>"""
    if len(context.args) < 2:
        await update.message.reply_text("📎 HD: `/edit <id> <số tiền> <mô tả>`", parse_mode='Markdown')
        return
    
    try:
        expense_id = int(context.args[0])
        amount_str = context.args[1]
        
        # Handle k/m suffixes in edit
        amount = 0
        match = re.match(r'^(\d+)(k|m|K|M)?$', amount_str)
        if match:
            amount = int(match.group(1))
            suffix = match.group(2)
            if suffix and suffix.lower() == 'k': amount *= 1000
            elif suffix and suffix.lower() == 'm': amount *= 1000000
        else:
            amount = int(amount_str)

        description = " ".join(context.args[2:]) if len(context.args) > 2 else None
        
        if expense_mgr.edit_expense(expense_id, new_amount=amount, new_description=description):
            await update.message.reply_text(f"✅ Đã cập nhật giao dịch ID: `{expense_id}`", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Không tìm thấy giao dịch với ID này.")
    except ValueError:
        await update.message.reply_text("❌ Dữ liệu không hợp lệ.")

@authorized_only
async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for expenses by keyword."""
    if not context.args:
        await update.message.reply_text("🔍 Nhập từ khóa: `/search <từ khóa>`", parse_mode='Markdown')
        return
        
    keyword = " ".join(context.args).lower()
    df = expense_mgr.get_expenses()
    if df.empty:
        await update.message.reply_text("📅 Chưa có dữ liệu để tìm kiếm.")
        return
        
    results = df[df['Mô tả'].str.lower().str.contains(keyword) | df['Danh mục'].str.lower().str.contains(keyword)]
    
    if results.empty:
        await update.message.reply_text(f"❌ Không tìm thấy kết quả cho: `{keyword}`", parse_mode='Markdown')
        return
        
    report = f"🔍 **Kết quả tìm kiếm cho '{keyword}':**\n\n"
    for _, row in results.tail(15).iterrows(): # Show last 15 matches
        report += f"• {row['Ngày']} | ID: `{row['ID']}` | {row['Số tiền']:,} đ | {row['Mô tả']}\n"
        
    await update.message.reply_text(report, parse_mode='Markdown')

@authorized_only
async def view_by_person(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View expenses for a specific person this month."""
    if not context.args:
        await update.message.reply_text("👤 Nhập tên: `/person vợ` hoặc `/person con`", parse_mode='Markdown')
        return
        
    person = " ".join(context.args)
    summary = expense_mgr.get_monthly_summary(person=person)
    
    if not summary or summary['total'] == 0:
        await update.message.reply_text(f"📅 Tháng này chưa có chi tiêu của {person}.")
        return
        
    report = f"👤 **CHI TIÊU CỦA {person.upper()} - THÁNG {summary['month']}/{summary['year']}**\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for cat, amt in summary['categories'].items():
        percent = (amt / summary['total']) * 100
        report += f"• {cat}: {amt:,} {config.CURRENCY} ({percent:.1f}%)\n"
        
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += f"💰 **TỔNG: {summary['total']:,} {config.CURRENCY}**"
    
    await update.message.reply_text(report, parse_mode='Markdown')

@authorized_only
async def debug_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hidden command to diagnose sheet issues."""
    try:
        rows = expense_mgr._sheet.get_all_values()
        if not rows:
            await update.message.reply_text("Sheet trống rỗng.")
            return
            
        header = rows[0]
        sample = rows[1:3] if len(rows) > 1 else "Không có dữ liệu dòng 2+"
        
        msg = f"🔍 **Sheet Debug Info:**\n"
        msg += f"• Tổng số dòng: {len(rows)}\n"
        msg += f"• Headers: `{header}`\n"
        msg += f"• Sample data: `{sample}`\n"
        msg += f"• VN Time: `{datetime.now(vn_tz).strftime('%Y-%m-%d %H:%M:%S')}`\n"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Lỗi debug: {e}")

async def send_monthly_report(context: ContextTypes.DEFAULT_TYPE):
    """Scheduled task to send monthly report."""
    now = datetime.now()
    if now.day != config.REPORT_DAY:
        return

    for user_id in config.AUTHORIZED_USER_IDS:
        try:
            last_month_date = now.replace(day=1) - timedelta(days=1)
            summary = expense_mgr.get_monthly_summary(month=last_month_date.month, year=last_month_date.year)
            
            if summary:
                report = f"📢 **BÁO CÁO TỔNG KẾT THÁNG {summary['month']}/{summary['year']}**\n"
                report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                for cat, amt in summary['categories'].items():
                    percent = (amt / summary['total']) * 100
                    report += f"• {cat}: {amt:,} {config.CURRENCY} ({percent:.1f}%)\n"
                report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
                report += f"💰 **TỔNG CHI: {summary['total']:,} {config.CURRENCY}**"
                
                await context.bot.send_message(chat_id=user_id, text=report, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in monthly report: {e}")

async def send_daily_summary(context: ContextTypes.DEFAULT_TYPE):
    """Scheduled task to send daily summary at 23:00."""
    now = datetime.now(vn_tz)
    today_str = now.strftime("%Y-%m-%d")
    
    # Ensure cache is for today
    if today_cache['date'] != today_str:
        # This might happen if no messages were processed today
        # We try to load from sheet to be accurate
        df = expense_mgr.get_expenses(start_date=now, end_date=now)
        if df.empty:
            return # Don't push if nothing was spent
        
        items = []
        for _, row in df.iterrows():
            items.append({'amount': row['Số tiền'], 'desc': row['Mô tả']})
    else:
        items = today_cache['items']

    if not items:
        return # Skip if no expenses recorded today

    # Calculate daily stats
    income = sum(item['amount'] for item in items if item['amount'] > 0)
    spent = abs(sum(item['amount'] for item in items if item['amount'] < 0))
    net = income - spent
    
    date_str = now.strftime("%d/%m/%Y")
    report = f"🌙 **TỔNG KẾT TÀI CHÍNH HÔM NAY ({date_str})**\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for item in items:
        sign = "➕" if item['amount'] > 0 else "➖"
        report += f"{sign} {abs(item['amount']):,} đ - {item['desc']}\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += f"➕ Tổng Thu: {income:,} đ\n"
    report += f"➖ Tổng Chi: {spent:,} đ\n"
    report += f"💰 **Số dư: {net:,} {config.CURRENCY}**\n\n"
    report += "Chúc bạn ngủ ngon! 😴"

    for user_id in config.AUTHORIZED_USER_IDS:
        try:
            await context.bot.send_message(chat_id=user_id, text=report, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error sending daily summary to {user_id}: {e}")

async def post_init(application):
    """Set up the bot's commands menu."""
    commands = [
        ("start", "Bắt đầu sử dụng bot"),
        ("help", "Xem hướng dẫn"),
        ("today", "Xem chi tiêu hôm nay"),
        ("week", "Xem chi tiêu tuần này"),
        ("month", "Xem chi tiêu tháng này"),
        ("stats", "Xem biểu đồ thống kê"),
        ("recent", "Xem 10 giao dịch gần nhất"),
        ("search", "Tìm kiếm chi tiêu theo từ khóa"),
        ("person", "Xem chi tiêu theo người (vợ, con...)"),
        ("edit", "Sửa chi tiêu (ID Tiền Mô tả)"),
        ("delete", "Xóa chi tiêu (ID)"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    """Start the bot with Polling and Keep-Alive Server."""
    keep_alive()  # Start Flask server for Render
    
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("view", view_today))
    application.add_handler(CommandHandler("today", view_today))
    application.add_handler(CommandHandler("week", view_week))
    application.add_handler(CommandHandler("month", view_month))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("recent", recent_expenses))
    application.add_handler(CommandHandler("delete", delete_item))
    application.add_handler(CommandHandler("edit", edit_item))
    application.add_handler(CommandHandler("search", search_items))
    application.add_handler(CommandHandler("person", view_by_person))
    application.add_handler(CommandHandler("debug_sheet", debug_sheet))

    # General messages
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Scheduler 
    if application.job_queue:
        # Monthly report at 08:00
        application.job_queue.run_daily(send_monthly_report, time=time(hour=8, minute=0, tzinfo=vn_tz))
        # Daily EOD Summary at 23:00
        application.job_queue.run_daily(send_daily_summary, time=time(hour=23, minute=0, tzinfo=vn_tz))

    logger.info("Bot is running (Polling Mode)...")
    application.run_polling()

if __name__ == '__main__':
    main()
