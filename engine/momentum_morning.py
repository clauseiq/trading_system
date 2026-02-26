#!/usr/bin/env python3
"""
CRON JOB: Momentum Morning Session
Schedule: 09:20 IST (Mon-Fri)
Duration: 5-30 seconds (rebalance day: up to 2 minutes)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.telegram_notifier import TelegramNotifier
from lib.market_data import get_current_prices
from config.config import MOMENTUM_STATE

log = setup_logger('momentum_morning')


def check_stops_and_targets(state_manager, notifier):
    """Check stop losses and target prices"""
    state = state_manager.load()
    positions = state.get('positions', {})
    
    if not positions:
        log.info("No positions to check")
        return
    
    # Get current prices
    symbols = list(positions.keys())
    prices = get_current_prices(symbols)
    
    closed = []
    
    for symbol, pos in list(positions.items()):
        current_price = prices.get(symbol)
        if not current_price:
            continue
        
        entry = pos['entry_price']
        stop = pos['stop_loss']
        target = pos.get('target_price')
        
        # Check stop loss
        if current_price <= stop:
            pnl_pct = ((current_price - entry) / entry) * 100
            log.info(f"🛑 {symbol} hit stop: ₹{current_price:.2f} (stop: ₹{stop:.2f})")
            
            if notifier:
                notifier.send(f"🛑 <b>STOP HIT: {symbol}</b>\n\nExit: ₹{current_price:.2f}\nPnL: {pnl_pct:+.2f}%")
            
            closed.append(symbol)
            continue
        
        # Check target
        if target and current_price >= target:
            pnl_pct = ((current_price - entry) / entry) * 100
            log.info(f"🎯 {symbol} hit target: ₹{current_price:.2f} (target: ₹{target:.2f})")
            
            if notifier:
                notifier.send(f"🎯 <b>TARGET HIT: {symbol}</b>\n\nExit: ₹{current_price:.2f}\nPnL: {pnl_pct:+.2f}%")
            
            closed.append(symbol)
    
    # Remove closed positions
    for symbol in closed:
        del positions[symbol]
    
    state['positions'] = positions
    state_manager.save(state)
    
    if closed:
        log.info(f"Closed {len(closed)} positions: {closed}")


def main():
    log.info("="*70)
    log.info("MOMENTUM MORNING SESSION - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        state_manager = StateManager(MOMENTUM_STATE)
        notifier = TelegramNotifier()
        
        check_stops_and_targets(state_manager, notifier)
        
        log.info("✅ Morning session completed")
        return 0
    
    except Exception as e:
        log.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
