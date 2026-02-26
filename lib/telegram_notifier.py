"""
TELEGRAM NOTIFIER
Library for sending alerts from cron jobs
"""
import os
import logging
from typing import Optional
from config.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED

try:
    import telebot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

log = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications to Telegram"""
    
    def __init__(self):
        self.enabled = TELEGRAM_ENABLED and TELEGRAM_AVAILABLE
        self.bot = None
        self.chat_id = TELEGRAM_CHAT_ID
        
        if self.enabled:
            try:
                self.bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='HTML')
                log.info("Telegram notifier initialized")
            except Exception as e:
                log.warning(f"Telegram init failed: {e}")
                self.enabled = False
    
    def send(self, message: str, parse_mode: str = 'HTML'):
        """Send a message"""
        if not self.enabled:
            return
        
        try:
            self.bot.send_message(
                self.chat_id,
                message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        except Exception as e:
            log.warning(f"Telegram send failed: {e}")
    
    def send_job_started(self, job_name: str):
        """Notify job started"""
        self.send(f"🔵 <b>{job_name}</b> started")
    
    def send_job_completed(self, job_name: str, duration: float):
        """Notify job completed"""
        self.send(f"✅ <b>{job_name}</b> completed in {duration:.1f}s")
    
    def send_job_failed(self, job_name: str, error: str):
        """Notify job failed"""
        self.send(f"❌ <b>{job_name}</b> failed\n\n<code>{error}</code>")
    
    def send_trade_signal(
        self,
        strategy: str,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        target: float,
        shares: int,
        win_prob: float,
        rr_ratio: float
    ):
        """Send trade signal alert"""
        arrow = "📈" if direction == "LONG" else "📉"
        
        message = f"""
{arrow} <b>{strategy} SIGNAL</b>

<b>Symbol:</b> {symbol}
<b>Direction:</b> {direction}
<b>Shares:</b> {shares}

<b>Entry:</b> ₹{entry_price:.2f}
<b>Stop:</b> ₹{stop_loss:.2f}
<b>Target:</b> ₹{target:.2f}
<b>R:R:</b> {rr_ratio:.1f}:1

<b>Confidence:</b> {win_prob:.1%}
"""
        self.send(message.strip())
    
    def send_trade_closed(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        pnl: float,
        pnl_pct: float
    ):
        """Send trade closure alert"""
        emoji = "💰" if pnl > 0 else "📊"
        
        message = f"""
{emoji} <b>TRADE CLOSED: {symbol}</b>

<b>Direction:</b> {direction}
<b>Entry:</b> ₹{entry_price:.2f}
<b>Exit:</b> ₹{exit_price:.2f}

<b>PnL:</b> ₹{pnl:+,.0f} ({pnl_pct:+.2f}%)
"""
        self.send(message.strip())
    
    def send_daily_summary(
        self,
        daytrade_pnl: float,
        daytrade_trades: int,
        daytrade_win_rate: float,
        momentum_positions: int,
        total_nav: float
    ):
        """Send end-of-day summary"""
        message = f"""
📊 <b>DAILY SUMMARY</b>

<b>Day Trading:</b>
├─ PnL: ₹{daytrade_pnl:+,.0f}
├─ Trades: {daytrade_trades}
└─ Win Rate: {daytrade_win_rate:.1f}%

<b>Momentum:</b>
└─ Positions: {momentum_positions}

<b>Total NAV:</b> ₹{total_nav:,.0f}
"""
        self.send(message.strip())
    
    def send_error_alert(self, component: str, error: str):
        """Send error alert"""
        message = f"""
🚨 <b>ERROR ALERT</b>

<b>Component:</b> {component}
<b>Error:</b>
<code>{error[:500]}</code>
"""
        self.send(message.strip())


# Module-level helper for simple usage (backwards-compatible)
_notifier = TelegramNotifier()

def send_message(message: str, parse_mode: str = 'HTML'):
    """Simple helper to send a message using the default notifier"""
    _notifier.send(message, parse_mode=parse_mode)
