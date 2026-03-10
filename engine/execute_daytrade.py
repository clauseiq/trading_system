#!/usr/bin/env python3
"""
Execute Day Trades
Schedule: 09:30 IST (Mon-Fri)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.telegram_notifier import send_message
from lib.market_data import get_current_prices
from config.config import (
    DAYTRADE_STATE, DAYTRADE_CAPITAL, MAX_DAYTRADES_PER_DAY,
    DAYTRADE_STOP_PCT, DAYTRADE_MIN_RR, DAYTRADE_MAX_RR, STATE_DIR
)

log = setup_logger('execute_daytrade')


def calculate_position_size(signal, capital_per_trade):
    """Calculate position size with risk management"""
    entry = signal['entry_price']
    stop = signal['stop_loss']
    
    risk_per_share = entry - stop
    risk_amount = capital_per_trade * (DAYTRADE_STOP_PCT / 2)
    quantity = int(risk_amount / risk_per_share)
    
    max_quantity = int(capital_per_trade / entry)
    quantity = min(quantity, max_quantity)
    
    return max(1, quantity)


def execute_trades(state_manager):
    """Execute all valid day trade signals"""
    state = state_manager.load()
    
    signals = state.get('signals', [])
    
    if not signals:
        log.info("No signals to execute")
        send_message("📊 No day trade signals today")
        return []
    
    symbols = [s['symbol'] for s in signals]
    current_prices = get_current_prices(symbols)
    
    valid_signals = []
    for signal in signals:
        symbol = signal['symbol']
        current_price = current_prices.get(symbol)
        
        if not current_price:
            log.warning(f"{symbol}: Could not get current price")
            continue
        
        entry = signal['entry_price']
        
        if abs(current_price - entry) / entry > 0.01:
            log.warning(f"{symbol}: Price moved too much")
            continue
        
        signal['actual_entry'] = current_price
        valid_signals.append(signal)
    
    if not valid_signals:
        log.info("No valid signals (prices moved)")
        send_message("⚠️ Signals invalidated - price movement too large")
        return []
    
    valid_signals = valid_signals[:MAX_DAYTRADES_PER_DAY]
    capital_per_trade = DAYTRADE_CAPITAL / len(valid_signals)
    
    executed_trades = []
    
    for signal in valid_signals:
        symbol = signal['symbol']
        entry = signal['actual_entry']
        stop = signal['stop_loss']
        target = signal['target_price']
        
        quantity = calculate_position_size(signal, capital_per_trade)
        
        position = {
            'symbol': symbol,
            'entry_price': entry,
            'quantity': quantity,
            'stop_loss': stop,
            'target_price': target,
            'invested': quantity * entry,
            'entry_time': datetime.now().isoformat(),
            'direction': signal.get('direction', 'LONG'),
            'confidence': signal.get('confidence', 0.85)
        }
        
        executed_trades.append(position)
        
        log.info(f"✅ {symbol}: {quantity} shares @ ₹{entry:.2f}, Stop: ₹{stop:.2f}, Target: ₹{target:.2f}")
    
    state['open_positions'] = executed_trades
    state['execution_time'] = datetime.now().isoformat()
    state_manager.save(state)
    
    send_execution_notification(executed_trades)
    
    return executed_trades


def send_execution_notification(trades):
    """Send trade execution summary to Telegram"""
    if not trades:
        return
    
    total_invested = sum(t['invested'] for t in trades)
    
    msg = f"📈 <b>DAY TRADES EXECUTED</b>\n\n"
    msg += f"<b>Trades: {len(trades)}</b>\n"
    msg += f"<b>Capital: ₹{total_invested:,.0f}</b>\n\n"
    
    for i, trade in enumerate(trades, 1):
        msg += f"<b>{i}. {trade['symbol']}</b>\n"
        msg += f"   Qty: {trade['quantity']} @ ₹{trade['entry_price']:.2f}\n"
        msg += f"   Stop: ₹{trade['stop_loss']:.2f}\n"
        msg += f"   Target: ₹{trade['target_price']:.2f}\n"
        
        rr_ratio = (trade['target_price'] - trade['entry_price']) / (trade['entry_price'] - trade['stop_loss'])
        msg += f"   R:R: {rr_ratio:.1f}:1\n"
        msg += f"   Confidence: {trade['confidence']*100:.1f}%\n\n"
    
    send_message(msg)


def main():
    """Main execution function"""
    log.info("="*70)
    log.info("EXECUTE DAY TRADES - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        # ✅ FIXED: Use correct path
        state_manager = StateManager(STATE_DIR / f'{DAYTRADE_STATE}.json')
        
        trades = execute_trades(state_manager)
        
        if trades:
            log.info(f"✅ Executed {len(trades)} trades successfully")
            return 0
        else:
            log.info("No trades executed")
            return 0
    
    except Exception as e:
        log.error(f"💥 Fatal error: {e}", exc_info=True)
        send_message(f"❌ Trade execution failed: {str(e)[:200]}")
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
