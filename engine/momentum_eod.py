#!/usr/bin/env python3
"""
CRON JOB: Momentum EOD Session
Schedule: 15:20 IST (Mon-Fri)
Duration: 5-10 seconds
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.market_data import get_current_prices
from config.config import MOMENTUM_STATE

log = setup_logger('momentum_eod')


def update_trailing_stops(state_manager):
    """Update trailing stops based on day's high"""
    state = state_manager.load()
    positions = state.get('positions', {})
    
    if not positions:
        log.info("No positions to update")
        return
    
    # Get current prices
    symbols = list(positions.keys())
    prices = get_current_prices(symbols)
    
    updated = 0
    
    for symbol, pos in positions.items():
        current_price = prices.get(symbol)
        if not current_price:
            continue
        
        entry = pos['entry_price']
        old_stop = pos['stop_loss']
        highest = max(pos.get('highest_price', entry), current_price)
        
        # Update highest price
        pos['highest_price'] = highest
        
        # Trailing stop: 2 ATR below highest
        atr = pos.get('atr', (highest - entry) * 0.05)
        new_stop = highest - (2.0 * atr)
        
        # Only raise stop, never lower
        if new_stop > old_stop:
            pos['stop_loss'] = new_stop
            updated += 1
            log.info(f"{symbol}: Stop raised ₹{old_stop:.2f} → ₹{new_stop:.2f}")
    
    state['positions'] = positions
    state['days_since_rebalance'] = state.get('days_since_rebalance', 0) + 1
    state_manager.save(state)
    
    log.info(f"Updated {updated} trailing stops")


def main():
    log.info("="*70)
    log.info("MOMENTUM EOD SESSION - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        state_manager = StateManager(MOMENTUM_STATE)
        update_trailing_stops(state_manager)
        
        log.info("✅ EOD session completed")
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
