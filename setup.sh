#!/bin/bash
# TRADING SYSTEM SETUP SCRIPT
# Run this after cloning the repository

set -e

echo "=========================================="
echo "TRADING SYSTEM SETUP"
echo "=========================================="

# Check Python version
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directory structure
echo "Creating directories..."
mkdir -p storage/state
mkdir -p storage/logs
mkdir -p storage/backups

# Initialize state files
echo "Initializing state files..."

# Day trade state
cat > storage/state/daytrade_state.json << EOF
{
  "model_trained": false,
  "last_train_date": null,
  "positions": {},
  "daily_signals": [],
  "total_capital": 1000000,
  "free_capital": 1000000,
  "used_capital": 0,
  "current_nav": 1000000,
  "peak_equity": 1000000,
  "realized_pnl": 0,
  "daily_pnl": 0,
  "win_count": 0,
  "loss_count": 0,
  "trade_logs": []
}
EOF

# Momentum state
cat > storage/state/momentum_state.json << EOF
{
  "positions": {},
  "last_rebalance_date": null,
  "days_since_rebalance": 0,
  "total_capital": 1000000,
  "free_capital": 1000000,
  "peak_equity": 1000000,
  "current_nav": 1000000
}
EOF

# Portfolio state
cat > storage/state/portfolio.json << EOF
{
  "total_capital": 1000000,
  "momentum_capital": 1000000,
  "daytrade_capital": 1000000
}
EOF

# Set permissions
chmod +x engine/*.py
chmod 600 storage/state/*.json

echo ""
echo "=========================================="
echo "SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Set environment variables:"
echo "   export TELEGRAM_TOKEN='your_token'"
echo "   export TELEGRAM_CHAT_ID='your_chat_id'"
echo "   (Get token from @BotFather on Telegram)"
echo "   (Get chat ID from @userinfobot)"
echo ""
echo "2. Test day trade training:"
echo "   python3 engine/train_daytrade_model.py"
echo ""
echo "3. Setup crontab:"
echo "   Edit crontab.txt with correct paths"
echo "   crontab crontab.txt"
echo ""
echo "4. Start Telegram bot (optional):"
echo "   sudo cp systemd/telegram-bot.service /etc/systemd/system/"
echo "   sudo systemctl enable telegram-bot"
echo "   sudo systemctl start telegram-bot"
echo ""
echo "5. Start dashboard (optional):"
echo "   streamlit run dashboard/app.py"
echo ""
echo "=========================================="
