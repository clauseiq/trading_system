# TELEGRAM BOT SETUP GUIDE

## Overview

The trading system includes a full-featured Telegram bot for:
- Real-time monitoring
- Trade alerts
- Manual job triggering
- Performance tracking
- System diagnostics

---

## Architecture

```
Trading System
│
├── Cron Jobs (execution)
│   ├── Send alerts via TelegramNotifier
│   └── Execute trades independently
│
└── Telegram Bot Service (monitoring)
    ├── Runs 24/7 as systemd service
    ├── Responds to commands
    └── Displays status on demand
```

**Key Point:** Bot does NOT execute trades. It only monitors and displays information. All trading is done by cron jobs.

---

## Setup Steps

### 1. Create Telegram Bot

```bash
# Talk to @BotFather on Telegram
1. Send: /newbot
2. Choose name: "My Trading Bot"
3. Choose username: "my_trading_bot"
4. Save the TOKEN you receive
```

### 2. Get Your Chat ID

```bash
# Method 1: Use @userinfobot
# Send any message to @userinfobot
# It will reply with your chat ID

# Method 2: API call
# Send a message to your bot, then visit:
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
# Look for "chat":{"id":12345678}
```

### 3. Set Environment Variables

```bash
# Add to ~/.bashrc or /etc/environment
export TELEGRAM_TOKEN='1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
export TELEGRAM_CHAT_ID='123456789'

# Reload
source ~/.bashrc
```

### 4. Install Bot Service

```bash
# Copy systemd service file
sudo cp systemd/telegram-bot.service /etc/systemd/system/

# Edit with your details
sudo nano /etc/systemd/system/telegram-bot.service
# Replace YOUR_TOKEN_HERE and YOUR_CHAT_ID_HERE
# Update paths if not in /opt/trading-system

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot
```

### 5. Test Bot

```bash
# Send /start to your bot on Telegram
# You should see the welcome message

# Try some commands:
/status
/daytrade
/positions
```

---

## Bot Commands

### Status Commands

| Command | Description | Example Output |
|---------|-------------|----------------|
| `/status` | Overall system status | NAV, positions, PnL |
| `/daytrade` | Day trade details | Model status, signals, trades |
| `/momentum` | Momentum strategy | Open positions, rebalance countdown |
| `/portfolio` | Portfolio overview | Total NAV, allocation |
| `/positions` | All open positions | Entry, stop, target for each |
| `/trades` | Recent trade history | Last 10 closed trades |

### Information Commands

| Command | Description |
|---------|-------------|
| `/logs` | Recent log entries from jobs |
| `/performance` | Performance metrics (win rate, return) |
| `/schedule` | Cron job schedule (IST times) |
| `/about` | System information |
| `/help` | Command list |

### Manual Actions

| Command | Description | Use Case |
|---------|-------------|----------|
| `/train` | Train model now | Force retrain if model failed |
| `/refresh` | Refresh prices | Update live prices manually |
| `/rebalance` | Force rebalance | Emergency rebalance (use carefully) |

---

## Notification Flow

### Daily Trade Flow

```
09:00 → Model Training
├─ If fails: ❌ Error alert
└─ If success: ✅ Training complete (silent)

09:29 → Signal Generation
└─ Generates 3-6 high-conviction signals (silent)

09:30 → Trade Execution
└─ For each trade:
    📈 SIGNAL ALERT
    Symbol: RELIANCE
    Direction: LONG
    Entry: ₹2,850
    Stop: ₹2,708
    Target: ₹3,136
    R:R: 3.0:1
    Confidence: 91%

11:15 → Position Closing
├─ For each position:
│   💰 TRADE CLOSED: RELIANCE
│   Entry: ₹2,850
│   Exit: ₹2,920
│   PnL: ₹+2,450 (+2.46%)
│
└─ Daily Summary:
    📊 DAILY SUMMARY
    Day Trading:
    ├─ PnL: ₹+5,240
    ├─ Trades: 4
    └─ Win Rate: 75.0%
    Total NAV: ₹1,005,240
```

### Momentum Alerts

```
When Stop Hit:
🛑 STOP HIT: TCS
Exit: ₹4,185
PnL: -1.52%

When Target Hit:
🎯 TARGET HIT: INFY
Exit: ₹1,742
PnL: +3.89%
```

### Error Alerts

```
🚨 ERROR ALERT
Component: train_daytrade_model
Error: yfinance download failed after 3 attempts
```

---

## Customizing Alerts

### Enable/Disable Notifications

```python
# In lib/telegram_notifier.py

class TelegramNotifier:
    def __init__(self):
        # Disable all notifications
        self.enabled = False  # Change to True to enable
        
        # Or selectively enable
        self.send_signals = True
        self.send_closures = True
        self.send_daily_summary = False
```

### Notification Preferences

```python
# config/config.py

# Alert settings
ALERT_ON_SIGNAL = True       # Trade signals
ALERT_ON_CLOSE = True        # Position closures
ALERT_ON_STOP_HIT = True     # Stop losses
ALERT_ON_TARGET_HIT = True   # Targets hit
ALERT_DAILY_SUMMARY = True   # EOD summary
ALERT_ON_ERROR = True        # Job failures
```

---

## Advanced Features

### Multiple Users

To allow multiple people to control the bot:

```python
# services/telegram_bot.py

ALLOWED_USERS = [
    123456789,   # Your chat ID
    987654321,   # Friend's chat ID
]

@bot.message_handler(commands=['status'])
def send_status(message):
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "❌ Unauthorized")
        return
    
    # ... rest of code
```

### Scheduled Reports

Add to crontab:

```cron
# Daily report at 16:00 IST (10:30 UTC)
30 10 * * 1-5 cd /opt/trading-system && python3 -c "
from lib.telegram_notifier import TelegramNotifier
from lib.state_manager import StateManager
from config.config import DAYTRADE_STATE
n = TelegramNotifier()
s = StateManager(DAYTRADE_STATE).load()
n.send_daily_summary(
    daytrade_pnl=s.get('daily_pnl', 0),
    daytrade_trades=s.get('win_count', 0) + s.get('loss_count', 0),
    daytrade_win_rate=...,
    momentum_positions=...,
    total_nav=...
)
"
```

---

## Troubleshooting

### Bot Not Responding

```bash
# Check if service is running
sudo systemctl status telegram-bot

# View logs
sudo journalctl -u telegram-bot -f

# Restart
sudo systemctl restart telegram-bot
```

### "Unauthorized" Error

```bash
# Wrong token or chat ID
# Verify environment variables
echo $TELEGRAM_TOKEN
echo $TELEGRAM_CHAT_ID

# Check service file
sudo systemctl cat telegram-bot
```

### Bot Crashes on Startup

```bash
# Missing dependency
pip install pyTelegramBotAPI

# Check Python path
which python3
/opt/trading-system/venv/bin/python3 --version
```

### Commands Not Working

```bash
# Bot might be restarting due to error
# Check logs
sudo journalctl -u telegram-bot -n 50

# Test manually
cd /opt/trading-system
python3 services/telegram_bot.py
# Press Ctrl+C to stop
```

---

## Security Best Practices

### 1. Protect Your Token

```bash
# NEVER commit token to git
echo "TELEGRAM_TOKEN" >> .gitignore

# Use environment variables only
# Don't hardcode in code
```

### 2. Restrict Commands

```python
# Only allow status commands, not execution
ALLOWED_COMMANDS = ['status', 'positions', 'trades']

@bot.message_handler(commands=['train'])
def trigger_train(message):
    bot.reply_to(message, "❌ Manual training disabled for safety")
    return
```

### 3. Rate Limiting

```python
# Prevent spam
from functools import wraps
import time

last_command = {}

def rate_limit(seconds=5):
    def decorator(func):
        @wraps(func)
        def wrapper(message):
            user_id = message.from_user.id
            now = time.time()
            
            if user_id in last_command:
                if now - last_command[user_id] < seconds:
                    bot.reply_to(message, "⏱️ Please wait...")
                    return
            
            last_command[user_id] = now
            return func(message)
        return wrapper
    return decorator

@bot.message_handler(commands=['status'])
@rate_limit(5)  # Max once per 5 seconds
def send_status(message):
    # ... code
```

---

## Production Checklist

- [ ] Token and Chat ID set in environment
- [ ] Service installed and enabled
- [ ] Service starts on boot
- [ ] Commands responding correctly
- [ ] Alerts being received
- [ ] Logs being written
- [ ] Unauthorized access prevented
- [ ] Rate limiting enabled
- [ ] Auto-restart configured

---

## Example Interaction

```
You: /start
Bot: 🤖 Trading System Bot
     
     Status Commands:
     /status - Overall system status
     ...

You: /status
Bot: 📊 SYSTEM STATUS
     
     Day Trading:
     ├─ Model: ✅ Trained
     ├─ Signals: 4
     ├─ Positions: 4
     └─ Daily PnL: ₹+5,240
     
     Momentum:
     ├─ Positions: 6
     └─ Next Rebalance: 10 days
     
     Portfolio:
     ├─ Total NAV: ₹2,012,500
     └─ Open Positions: 10

You: /positions
Bot: 📊 OPEN POSITIONS
     
     Day Trade:
     
     RELIANCE
     ├─ Entry: ₹2,850.00
     ├─ Stop: ₹2,708.00
     ├─ Target: ₹3,136.00
     ├─ Shares: 35
     └─ R:R: 3.0:1
     ...

You: /train
Bot: 🔵 Starting model training...
     ✅ Model training completed successfully
```

---

## Integration with Existing System

The bot is already integrated:

1. **Cron jobs** use `TelegramNotifier` to send alerts
2. **Bot service** reads state files (read-only)
3. **No interference** - bot doesn't modify state
4. **Commands** can trigger jobs via subprocess

Everything works together seamlessly!

---

## Support

If you encounter issues:

1. Check service status: `sudo systemctl status telegram-bot`
2. View logs: `sudo journalctl -u telegram-bot -f`
3. Test manually: `python3 services/telegram_bot.py`
4. Verify environment: `echo $TELEGRAM_TOKEN`

For questions about specific commands, send `/help` to the bot.
