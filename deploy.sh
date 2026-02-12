#!/bin/bash

# Quick deployment script for VPS/Cloud
# Usage: bash deploy.sh

echo "🚀 Telegram Expense Bot - Quick Deploy Script"
echo "=============================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is for Linux only (Ubuntu/Debian)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and pip..."
sudo apt install python3 python3-pip git -y

# Install Python packages
echo "📚 Installing Python dependencies..."
pip3 install python-telegram-bot openpyxl pandas apscheduler matplotlib

# Create data directory
echo "📁 Creating data directory..."
mkdir -p ~/expense-bot/data

# Setup systemd service
echo "⚙️  Setting up systemd service..."
USERNAME=$(whoami)
WORKDIR=$(pwd)

cat > /tmp/expense-bot.service << EOF
[Unit]
Description=Telegram Expense Tracking Bot
After=network.target

[Service]
Type=simple
User=$USERNAME
WorkingDirectory=$WORKDIR
ExecStart=/usr/bin/python3 $WORKDIR/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/expense-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable expense-bot

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.py with your bot token and user ID"
echo "2. Start the bot: sudo systemctl start expense-bot"
echo "3. Check status: sudo systemctl status expense-bot"
echo "4. View logs: sudo journalctl -u expense-bot -f"
