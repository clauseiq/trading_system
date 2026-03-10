#!/usr/bin/env python3
"""
Close Day Trade Positions
Schedule: 11:15 IST (Mon-Fri) - 1h 45m after market open
COMPLETE & FIXED
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.telegram_notifier import send_message
from lib.market_data import get_current_prices
from config.config import DAYTRADE_STATE, STATE_DIR

log = setup_logger('close_daytrade')


def close_positions(state_manager):
    """Close all open day trade positions"""
    state = state_manager.load()
    
    positions = state.get('open_positions', [])
    
    if not positions:
        log.info("No open positions to close")
        send_message("📊 No day trade positions were opened today")
        return []
    
    log.info(f"Closing {len(positions)} positions...")
    
    symbols = [p['symbol'] for p in positions]
    current_prices = get_current_prices(symbols)
    
    closed_trades = []
    total_pnl = 0
    winners = 0
    
    for pos in positions:
        symbol = pos['symbol']
        current_price = current_prices.get(symbol)
        
        if not current_price:
            log.warning(f"{symbol}: Could not get current price")
            continue
        
        entry = pos['entry_price']
        quantity = pos['quantity']
        
        pnl = (current_price - entry) * quantity
        pnl_pct = ((current_price - entry) / entry) * 100
        
        total_pnl += pnl
        if pnl > 0:
            winners += 1
        
        closed_trades.append({
            'symbol': symbol,
            'entry': entry,
            'exit': current_price,
            'quantity': quantity,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        emoji = "💰" if pnl > 0 else "📉"
        log.info(f"{emoji} {symbol}: Entry ₹{entry:.2f} → Exit ₹{current_price:.2f}, PnL: ₹{pnl:+,.0f} ({pnl_pct:+.2f}%)")
    
    # Calculate stats
    win_rate = (winners / len(closed_trades) * 100) if closed_trades else 0
    
    # Update state
    state['closed_trades'] = closed_trades
    state['open_positions'] = []
    state['daily_pnl'] = total_pnl
    state['daily_win_rate'] = win_rate
    state_manager.save(state)
    
    # Send notification
    send_close_notification(closed_trades, total_pnl, win_rate)
    
    log.info(f"✅ Closed {len(closed_trades)} positions")
    log.info(f"Total PnL: ₹{total_pnl:+,.0f}")
    log.info(f"Win Rate: {win_rate:.1f}%")
    
    return closed_trades


def send_close_notification(trades, total_pnl, win_rate):
    """Send position close summary to Telegram"""
    if not trades:
        return
    
    msg = f"🏁 <b>DAY TRADES CLOSED</b>\n\n"
    msg += f"<b>Positions: {len(trades)}</b>\n"
    msg += f"<b>Total PnL: ₹{total_pnl:+,.0f}</b>\n"
    msg += f"<b>Win Rate: {win_rate:.1f}%</b>\n\n"
    
    # Show top 3 winners and losers
    sorted_trades = sorted(trades, key=lambda x: x['pnl'], reverse=True)
    
    msg += "<b>Top Winners:</b>\n"
    for trade in sorted_trades[:3]:
        if trade['pnl'] > 0:
            msg += f"💰 {trade['symbol']}: ₹{trade['pnl']:+,.0f} ({trade['pnl_pct']:+.2f}%)\n"
    
    msg += "\n<b>Losers:</b>\n"
    for trade in sorted_trades[-3:]:
        if trade['pnl'] < 0:
            msg += f"📉 {trade['symbol']}: ₹{trade['pnl']:+,.0f} ({trade['pnl_pct']:+.2f}%)\n"
    
    send_message(msg)


def main():
    """Main close function"""
    log.info("="*70)
    log.info("CLOSE DAY TRADES - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        state_manager = StateManager(STATE_DIR / f'{DAYTRADE_STATE}.json')
        
        trades = close_positions(state_manager)
        
        log.info("✅ Position close complete")
        return 0
    
    except Exception as e:
        log.error(f"💥 Fatal error: {e}", exc_info=True)
        send_message(f"❌ Position close failed: {str(e)[:200]}")
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
