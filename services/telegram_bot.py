#!/usr/bin/env python3
"""
TELEGRAM BOT SERVICE
Interactive bot for monitoring and control
Run as: python3 services/telegram_bot.py
Or as systemd service
"""
import sys
import os
import time
import subprocess
from pathlib import Path
from datetime import datetime, date

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.logger import setup_logger
from lib.state_manager import StateManager
from config.config import (
    DAYTRADE_STATE, MOMENTUM_STATE, PORTFOLIO_STATE,
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, LOG_DIR
)

try:
    import telebot
    from telebot import types
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("ERROR: pyTelegramBotAPI not installed")
    print("Install: pip install pyTelegramBotAPI")
    sys.exit(1)

log = setup_logger('telegram_bot')

# Initialize bot
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='HTML')

# State managers
daytrade_mgr = StateManager(DAYTRADE_STATE)
momentum_mgr = StateManager(MOMENTUM_STATE)
portfolio_mgr = StateManager(PORTFOLIO_STATE)


# ─── Helper Functions ────────────────────────────────────────────────────────

def get_daytrade_status():
    """Get day trade status"""
    state = daytrade_mgr.load()
    
    model_trained = "✅ Trained" if state.get('model_trained') else "❌ Not Trained"
    last_train = state.get('last_train_date', 'Never')
    signals = len(state.get('daily_signals', []))
    positions = len(state.get('positions', {}))
    daily_pnl = state.get('daily_pnl', 0)
    win_count = state.get('win_count', 0)
    loss_count = state.get('loss_count', 0)
    total_trades = win_count + loss_count
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    nav = state.get('current_nav', 1_000_000)
    used = state.get('used_capital', 0)
    free = state.get('free_capital', 1_000_000)
    realized_pnl = state.get('realized_pnl', 0)
    total_return = (realized_pnl / 1_000_000 * 100) if realized_pnl else 0
    
    return {
        'model_trained': model_trained,
        'last_train': last_train,
        'signals': signals,
        'positions': positions,
        'daily_pnl': daily_pnl,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'nav': nav,
        'used': used,
        'free': free,
        'realized_pnl': realized_pnl,
        'total_return': total_return
    }


def get_momentum_status():
    """Get momentum status"""
    state = momentum_mgr.load()
    
    positions = len(state.get('positions', {}))
    days_since = state.get('days_since_rebalance', 0)
    days_until = max(0, 14 - days_since)
    last_rebalance = state.get('last_rebalance_date', 'Never')
    nav = state.get('current_nav', 1_000_000)
    
    return {
        'positions': positions,
        'days_until': days_until,
        'last_rebalance': last_rebalance,
        'nav': nav
    }


def format_position(symbol, pos):
    """Format position for display"""
    entry = pos.get('entry_price', 0)
    stop = pos.get('stop_loss', 0)
    target = pos.get('target_price', 0)
    shares = pos.get('shares', 0)
    rr = pos.get('rr_ratio', 0)
    
    return f"""
<b>{symbol}</b>
├─ Entry: ₹{entry:.2f}
├─ Stop: ₹{stop:.2f}
├─ Target: ₹{target:.2f}
├─ Shares: {shares}
└─ R:R: {rr:.1f}:1
"""


# ─── Bot Commands ────────────────────────────────────────────────────────────

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Welcome message and command list"""
    help_text = """
🤖 <b>Trading System Bot</b>

<b>Status Commands:</b>
/status - Overall system status
/daytrade - Day trade details
/momentum - Momentum strategy
/portfolio - Portfolio overview
/positions - All open positions
/trades - Recent trade history

<b>Logs & Info:</b>
/logs - Recent log entries
/performance - Performance metrics
/schedule - Cron job schedule

<b>Manual Actions:</b>
/train - Train day trade model now
/rebalance - Force momentum rebalance
/refresh - Refresh prices

<b>Other:</b>
/help - This message
/about - System info
"""
    bot.reply_to(message, help_text.strip())


@bot.message_handler(commands=['status'])
def send_status(message):
    """Overall system status"""
    dt = get_daytrade_status()
    mom = get_momentum_status()
    
    total_nav = dt['nav'] + mom['nav']
    total_positions = dt['positions'] + mom['positions']
    
    status_text = f"""
📊 <b>SYSTEM STATUS</b>

<b>Day Trading:</b>
├─ Model: {dt['model_trained']}
├─ Signals: {dt['signals']}
├─ Positions: {dt['positions']}
└─ Daily PnL: ₹{dt['daily_pnl']:+,.0f}

<b>Momentum:</b>
├─ Positions: {mom['positions']}
└─ Next Rebalance: {mom['days_until']} days

<b>Portfolio:</b>
├─ Total NAV: ₹{total_nav:,.0f}
└─ Open Positions: {total_positions}

<i>Updated: {datetime.now().strftime('%H:%M:%S')}</i>
"""
    bot.reply_to(message, status_text.strip())


@bot.message_handler(commands=['daytrade'])
def send_daytrade(message):
    """Day trade details"""
    dt = get_daytrade_status()
    
    text = f"""
📈 <b>DAY TRADE STATUS</b>

<b>Model:</b>
├─ Status: {dt['model_trained']}
└─ Last Train: {dt['last_train']}

<b>Today:</b>
├─ Signals: {dt['signals']}
├─ Positions: {dt['positions']}
└─ PnL: ₹{dt['daily_pnl']:+,.0f}

<b>Overall:</b>
├─ Win Rate: {dt['win_rate']:.1f}%
├─ Total Trades: {dt['total_trades']}
└─ Total Return: {dt['total_return']:+.2f}%

<b>Capital:</b>
├─ NAV: ₹{dt['nav']:,.0f}
├─ Used: ₹{dt['used']:,.0f}
└─ Free: ₹{dt['free']:,.0f}
"""
    bot.reply_to(message, text.strip())


@bot.message_handler(commands=['momentum'])
def send_momentum(message):
    """Momentum strategy details"""
    mom = get_momentum_status()
    state = momentum_mgr.load()
    
    text = f"""
🔄 <b>MOMENTUM STRATEGY</b>

<b>Status:</b>
├─ Open Positions: {mom['positions']}
├─ Days to Rebalance: {mom['days_until']}
└─ Last Rebalance: {mom['last_rebalance']}

<b>Capital:</b>
└─ NAV: ₹{mom['nav']:,.0f}
"""
    
    # Add positions if any
    positions = state.get('positions', {})
    if positions:
        text += "\n\n<b>Positions:</b>"
        for symbol, pos in list(positions.items())[:5]:  # First 5
            text += f"\n├─ {symbol}: {pos.get('shares', 0)} @ ₹{pos.get('entry_price', 0):.2f}"
        
        if len(positions) > 5:
            text += f"\n└─ ... and {len(positions) - 5} more"
    
    bot.reply_to(message, text.strip())


@bot.message_handler(commands=['portfolio'])
def send_portfolio(message):
    """Portfolio overview"""
    dt = get_daytrade_status()
    mom = get_momentum_status()
    
    total_nav = dt['nav'] + mom['nav']
    total_capital = 2_000_000
    total_return = ((total_nav - total_capital) / total_capital * 100)
    
    text = f"""
💰 <b>PORTFOLIO OVERVIEW</b>

<b>Total NAV:</b> ₹{total_nav:,.0f}
<b>Total Return:</b> {total_return:+.2f}%

<b>Strategy Breakdown:</b>
├─ Momentum: ₹{mom['nav']:,.0f}
└─ Day Trade: ₹{dt['nav']:,.0f}

<b>Capital Allocation:</b>
├─ Momentum: {(mom['nav']/total_nav*100):.1f}%
└─ Day Trade: {(dt['nav']/total_nav*100):.1f}%
"""
    bot.reply_to(message, text.strip())


@bot.message_handler(commands=['positions'])
def send_positions(message):
    """All open positions"""
    dt_state = daytrade_mgr.load()
    mom_state = momentum_mgr.load()
    
    dt_positions = dt_state.get('positions', {})
    mom_positions = mom_state.get('positions', {})
    
    text = "<b>📊 OPEN POSITIONS</b>\n"
    
    if dt_positions:
        text += "\n<b>Day Trade:</b>"
        for symbol, pos in dt_positions.items():
            text += format_position(symbol, pos)
    
    if mom_positions:
        text += "\n<b>Momentum:</b>"
        for symbol, pos in list(mom_positions.items())[:5]:
            text += format_position(symbol, pos)
        
        if len(mom_positions) > 5:
            text += f"\n<i>... and {len(mom_positions) - 5} more</i>"
    
    if not dt_positions and not mom_positions:
        text += "\n<i>No open positions</i>"
    
    bot.reply_to(message, text.strip())


@bot.message_handler(commands=['trades'])
def send_trades(message):
    """Recent trade history"""
    dt_state = daytrade_mgr.load()
    trades = dt_state.get('trade_logs', [])[-10:]  # Last 10
    
    if not trades:
        bot.reply_to(message, "<i>No recent trades</i>")
        return
    
    text = "<b>📝 RECENT TRADES</b>\n"
    
    for trade in reversed(trades):  # Most recent first
        symbol = trade.get('symbol')
        direction = trade.get('direction')
        pnl = trade.get('pnl', 0)
        pnl_pct = trade.get('pnl_pct', 0)
        date_str = trade.get('entry_date', '')
        
        emoji = "💰" if pnl > 0 else "📉"
        text += f"""
{emoji} <b>{symbol}</b> {direction}
├─ Date: {date_str}
└─ PnL: ₹{pnl:+,.0f} ({pnl_pct:+.2f}%)
"""
    
    bot.reply_to(message, text.strip())


@bot.message_handler(commands=['logs'])
def send_logs(message):
    """View recent log entries"""
    log_files = {
        'train': LOG_DIR / 'train_daytrade.log',
        'signals': LOG_DIR / 'generate_signals.log',
        'execute': LOG_DIR / 'execute_daytrade.log'
    }
    
    # Read last 5 lines from each
    text = "<b>📋 RECENT LOGS</b>\n"
    
    for name, path in log_files.items():
        if path.exists():
            try:
                with open(path) as f:
                    lines = f.readlines()[-3:]  # Last 3 lines
                text += f"\n<b>{name.upper()}:</b>\n"
                for line in lines:
                    # Extract just the message part
                    if ']' in line:
                        msg = line.split(']', 2)[-1].strip()
                        text += f"├─ {msg[:60]}\n"
            except Exception as e:
                text += f"├─ Error reading: {e}\n"
    
    bot.reply_to(message, text.strip())


@bot.message_handler(commands=['performance'])
def send_performance(message):
    """Performance metrics"""
    dt = get_daytrade_status()
    
    text = f"""
📈 <b>PERFORMANCE METRICS</b>

<b>Day Trading:</b>
├─ Total Trades: {dt['total_trades']}
├─ Win Rate: {dt['win_rate']:.1f}%
├─ Realized PnL: ₹{dt['realized_pnl']:+,.0f}
└─ Total Return: {dt['total_return']:+.2f}%

<b>Best Practices:</b>
├─ Win Rate Target: >60%
├─ R:R Ratio: 2:1 to 3:1
└─ Max Drawdown: <10%
"""
    bot.reply_to(message, text.strip())


@bot.message_handler(commands=['schedule'])
def send_schedule(message):
    """Show cron job schedule"""
    text = """
⏰ <b>JOB SCHEDULE (IST)</b>

<b>Day Trading:</b>
├─ 09:00 - Train model (30-60s)
├─ 09:29 - Generate signals (5-10s)
├─ 09:30 - Execute trades (2-5s)
└─ 11:15 - Close positions (5-10s)

<b>Momentum:</b>
├─ 09:20 - Morning session (5-30s)
├─ 15:20 - EOD session (5-10s)
└─ */5 min - Refresh prices (2-5s)

<i>All times are India Standard Time</i>
"""
    bot.reply_to(message, text.strip())


@bot.message_handler(commands=['train'])
def trigger_train(message):
    """Manually trigger model training"""
    bot.reply_to(message, "🔵 Starting model training...")
    
    try:
        result = subprocess.run(
            ['python3', 'engine/train_daytrade_model.py'],
            capture_output=True,
            text=True,
            timeout=120  # 2 min timeout
        )
        
        if result.returncode == 0:
            bot.reply_to(message, "✅ Model training completed successfully")
        else:
            error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
            bot.reply_to(message, f"❌ Training failed:\n<code>{error_msg}</code>")
    
    except subprocess.TimeoutExpired:
        bot.reply_to(message, "⏱️ Training timeout (>2 min)")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


@bot.message_handler(commands=['refresh'])
def trigger_refresh(message):
    """Manually refresh prices"""
    bot.reply_to(message, "🔄 Refreshing prices...")
    
    try:
        result = subprocess.run(
            ['python3', 'engine/momentum_refresh_prices.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            bot.reply_to(message, "✅ Prices refreshed")
        else:
            bot.reply_to(message, f"❌ Failed: {result.stderr[-200:]}")
    
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


@bot.message_handler(commands=['about'])
def send_about(message):
    """System information"""
    text = """
🤖 <b>Trading System v2.0</b>

<b>Architecture:</b>
├─ Cron-based microservices
├─ Independent job execution
└─ File-locked state management

<b>Strategies:</b>
├─ Day Trading (XGBoost ML)
└─ Momentum (Swing Trading)

<b>Technology:</b>
├─ Python 3.11+
├─ XGBoost 2.0
├─ yfinance API
└─ Telegram Bot API

<b>Status:</b> 🟢 Production Ready
"""
    bot.reply_to(message, text.strip())


# ─── Error Handler ───────────────────────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def unknown_command(message):
    """Handle unknown commands"""
    bot.reply_to(
        message,
        "❓ Unknown command. Send /help for available commands."
    )


# ─── Main Loop ───────────────────────────────────────────────────────────────

def main():
    """Main bot loop with auto-restart"""
    log.info("="*70)
    log.info("TELEGRAM BOT SERVICE STARTING")
    log.info("="*70)
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        log.error("TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set")
        log.error("Set environment variables:")
        log.error("  export TELEGRAM_TOKEN='your_token'")
        log.error("  export TELEGRAM_CHAT_ID='your_chat_id'")
        return 1
    
    log.info(f"Bot initialized for chat ID: {TELEGRAM_CHAT_ID}")
    log.info("Send /help to the bot to see available commands")
    
    # Run bot with auto-restart on error
    while True:
        try:
            log.info("Starting bot polling...")
            bot.polling(none_stop=True, interval=1, timeout=60)
        
        except KeyboardInterrupt:
            log.info("Bot stopped by user")
            break
        
        except Exception as e:
            log.error(f"Bot crashed: {e}")
            log.info("Restarting in 10 seconds...")
            time.sleep(10)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
