from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import asyncio
import os
import json
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

import config
import bot  # Import existing bot logic

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# FastAPI Setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global variables
telegram_app = None

@app.on_event("startup")
async def startup_event():
    """Start the Telegram Bot on startup."""
    global telegram_app
    
    # Initialize the bot application
    telegram_app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers from bot.py
    telegram_app.add_handler(CommandHandler("start", bot.start))
    telegram_app.add_handler(CommandHandler("help", bot.help_command))
    telegram_app.add_handler(CommandHandler("view", bot.view_today))
    telegram_app.add_handler(CommandHandler("today", bot.view_today))
    telegram_app.add_handler(CommandHandler("week", bot.view_week))
    telegram_app.add_handler(CommandHandler("month", bot.view_month))
    telegram_app.add_handler(CommandHandler("stats", bot.stats))
    telegram_app.add_handler(CommandHandler("export", bot.export_excel))
    telegram_app.add_handler(CommandHandler("recent", bot.recent_expenses))
    telegram_app.add_handler(CommandHandler("delete", bot.delete_item))
    telegram_app.add_handler(CommandHandler("edit", bot.edit_item))
    telegram_app.add_handler(CommandHandler("search", bot.search_items))
    telegram_app.add_handler(CommandHandler("person", bot.view_by_person))

    # Add Web App Data Handler
    telegram_app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, bot.handle_web_app_data))
    
    # General messages
    telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), bot.handle_message))

    # Scheduler 
    if telegram_app.job_queue:
        from datetime import time
        telegram_app.job_queue.run_daily(bot.send_monthly_report_callback, time=time(hour=8, minute=0))

    await telegram_app.initialize()
    await telegram_app.start()

    # Set Webhook
    # IMPORTANT: Ensure WEB_APP_URL is set in Render Environment Variables
    # Or use default, but default might be wrong if you didn't change it
    webhook_url = f"{config.WEB_APP_URL}/webhook"
    logger.info(f"Setting webhook to: {webhook_url}")
    await telegram_app.bot.set_webhook(url=webhook_url)

    logger.info("Bot started via FastAPI startup event (Webhook Mode)")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the bot on shutdown."""
    if telegram_app:
        # await telegram_app.bot.delete_webhook() # Optional: keep webhook if sleeping
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("Bot stopped")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates."""
    try:
        data = await request.json()
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the Mini App HTML."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint for Render."""
    return {"status": "ok"}
