import logging
import asyncio
from datetime import datetime, timedelta
import re
import matplotlib.pyplot as plt
import io
import os

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from expense_manager import ExpenseManager

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

expense_mgr = ExpenseManager()

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
        "/view - Xem chi tiêu hôm nay\n"
        "/week - Xem chi tiêu tuần này\n"
        "/month - Xem chi tiêu tháng này\n"
        "/stats - Biểu đồ chi tiêu\n"
        "/recent - 10 giao dịch gần nhất\n"
        "/search <từ khóa> - Tìm kiếm\n"
        "/edit <id> <tiền> <mô tả> - Sửa\n"
        "/delete <id> - Xóa\n"
        "/person <tên> - Xem chi tiêu theo người\n"
        "/export - Tải file Excel\n"
        "/help - Xem lại hướng dẫn này"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

@authorized_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await start(update, context)

@authorized_only
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the user message for expense recording."""
    text = update.message.text.strip()
    
    # Regex for "100k cơm" or "50 xăng" or "100k cơm @vợ"
    # Matches: number + optional 'k'/'m' + description + optional @person
    match = re.match(r'^(\d+)(k|m|K|M)?\s+(.+?)(?:\s+@(\w+))?$', text)
    
    if not match:
        await update.message.reply_text("❓ Sai định dạng. Ví dụ đúng: `100k cơm` hoặc `50 xăng @vợ`", parse_mode='Markdown')
        return
        
    amount_raw = match.group(1)
    suffix = match.group(2)
    description = match.group(3)
    person = match.group(4) if match.group(4) else "Bản thân"
    
    amount = int(amount_raw)
    if suffix and suffix.lower() == 'k':
        amount *= 1000
    elif suffix and suffix.lower() == 'm':
        amount *= 1000000
        
    try:
        record = expense_mgr.add_expense(amount, description, person=person)
        response = (
            f"✅ **Đã ghi nhận!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Người: {record['Người']}\n"
            f"💰 Số tiền: {amount:,} {config.CURRENCY}\n"
            f"📂 Danh mục: {record['Danh mục']}\n"
            f"📝 Mô tả: {description}\n"
            f"📅 ID: `{record['ID']}`"
        )
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error recording expense: {e}")
        await update.message.reply_text("❌ Có lỗi xảy ra khi lưu dữ liệu.")

@authorized_only
async def view_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View today's expenses."""
    now = datetime.now()
    start_of_day = datetime(now.year, now.month, now.day)
    df = expense_mgr.get_expenses(start_date=start_of_day, end_date=now)
    
    if df.empty:
        await update.message.reply_text("📅 Hôm nay bạn chưa chi tiêu gì.")
        return
        
    total = df['Số tiền'].sum()
    report = "📅 **Chi tiêu hôm nay:**\n\n"
    for _, row in df.iterrows():
        report += f"• {row['Số tiền']:,} {config.CURRENCY} - {row['Mô tả']}\n"
    report += f"\n💰 **Tổng cộng: {total:,} {config.CURRENCY}**"
    await update.message.reply_text(report, parse_mode='Markdown')

@authorized_only
async def view_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View this week's expenses."""
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = datetime(start_of_week.year, start_of_week.month, start_of_week.day)
    df = expense_mgr.get_expenses(start_date=start_of_week, end_date=now)
    
    if df.empty:
        await update.message.reply_text("📅 Tuần này bạn chưa chi tiêu gì.")
        return
        
    total = df['Số tiền'].sum()
    report = "📅 **Chi tiêu tuần này:**\n\n"
    for _, row in df.iterrows():
        report += f"• {row['Ngày']} - {row['Số tiền']:,} đ: {row['Mô tả']}\n"
    report += f"\n💰 **Tổng cộng: {total:,} {config.CURRENCY}**"
    await update.message.reply_text(report, parse_mode='Markdown')


@authorized_only
async def view_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View this month's summary."""
    summary = expense_mgr.get_monthly_summary()
    if not summary:
        await update.message.reply_text("📅 Tháng này chưa có dữ liệu chi tiêu.")
        return
        
    report = f"📊 **TỔNG HỢP CHI TIÊU THÁNG {summary['month']}/{summary['year']}**\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for cat, amt in summary['categories'].items():
        percent = (amt / summary['total']) * 100
        report += f"• {cat}: {amt:,} {config.CURRENCY} ({percent:.1f}%)\n"
        
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += f"💰 **TỔNG: {summary['total']:,} {config.CURRENCY}**"
    
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
async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export current month's Excel file."""
    now = datetime.now()
    file_path = expense_mgr._get_file_path(now)
    
    if os.path.exists(file_path):
        await update.message.reply_document(document=open(file_path, 'rb'), filename=os.path.basename(file_path))
    else:
        await update.message.reply_text("📂 Hiện tại chưa có file dữ liệu cho tháng này.")

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


async def send_monthly_report(application):
    """Scheduled task to send monthly report."""
    # This needs to be run for each authorized user
    for user_id in config.AUTHORIZED_USER_IDS:
        try:
            now = datetime.now()
            # If it's the 5th, report for previous month if needed, or current month so far.
            # Usually, people want report of the PREVIOUS month on the 5th.
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
                
                await application.bot.send_message(chat_id=user_id, text=report, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in monthly report: {e}")

def main():
    """Start the bot."""
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("view", view_today))
    application.add_handler(CommandHandler("today", view_today))
    application.add_handler(CommandHandler("week", view_week))
    application.add_handler(CommandHandler("month", view_month))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("export", export_excel))
    application.add_handler(CommandHandler("recent", recent_expenses))
    application.add_handler(CommandHandler("delete", delete_item))
    application.add_handler(CommandHandler("edit", edit_item))
    application.add_handler(CommandHandler("search", search_items))
    application.add_handler(CommandHandler("person", view_by_person))

    # General messages
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Scheduler for monthly report (Run on day config.REPORT_DAY at 08:00 AM)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_monthly_report, 'cron', day=config.REPORT_DAY, hour=8, minute=0, args=[application])
    scheduler.start()

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
