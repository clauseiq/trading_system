#!/usr/bin/env python3
"""
Momentum EOD Update
Schedule: 15:20 IST (Mon-Fri)
Update trailing stops for momentum positions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.telegram_notifier import send_message
from lib.market_data import get_current_prices
from config.config import MOMENTUM_STATE, MOMENTUM_TRAILING_STOP_ATR, STATE_DIR

log = setup_logger('momentum_eod')


def update_trailing_stops(state_manager):
    """Update trailing stops based on highest price"""
    state = state_manager.load()
    
    positions = state.get('positions', {})
    
    if not positions:
        log.info("No momentum positions")
        return
    
    log.info(f"Updating stops for {len(positions)} positions...")
    
    symbols = list(positions.keys())
    current_prices = get_current_prices(symbols)
    
    updates = []
    
    for symbol, pos in positions.items():
        current_price = current_prices.get(symbol)
        
        if not current_price:
            log.warning(f"{symbol}: Could not get current price")
            continue
        
        highest = pos.get('highest_price', pos['entry_price'])
        old_stop = pos['stop_loss']
        atr = pos['atr']
        
        if current_price > highest:
            pos['highest_price'] = current_price
            highest = current_price
            log.info(f"{symbol}: New high @ ₹{current_price:.2f}")
        
        new_stop = highest - (MOMENTUM_TRAILING_STOP_ATR * atr)
        
        if new_stop > old_stop:
            pos['stop_loss'] = new_stop
            updates.append(f"{symbol}: Stop ₹{old_stop:.2f} → ₹{new_stop:.2f}")
            log.info(f"{symbol}: Stop raised to ₹{new_stop:.2f}")
        else:
            log.info(f"{symbol}: Stop unchanged @ ₹{old_stop:.2f}")
        
        pnl_pct = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
        log.info(f"{symbol}: Price ₹{current_price:.2f} ({pnl_pct:+.2f}%)")
    
    state['positions'] = positions
    state['days_since_rebalance'] = state.get('days_since_rebalance', 0) + 1
    state_manager.save(state)
    
    if updates:
        msg = f"📉 <b>TRAILING STOPS UPDATED</b>\n\n"
        msg += "\n".join(updates[:10])
        if len(updates) > 10:
            msg += f"\n... and {len(updates) - 10} more"
        send_message(msg)


def main():
    """Main EOD update function"""
    log.info("="*70)
    log.info("MOMENTUM EOD UPDATE - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        state_manager = StateManager(STATE_DIR / f'{MOMENTUM_STATE}.json')
        update_trailing_stops(state_manager)
        
        log.info("✅ EOD update complete")
        return 0
    
    except Exception as e:
        log.error(f"💥 Fatal error: {e}", exc_info=True)
        send_message(f"❌ Momentum EOD failed: {str(e)[:200]}")
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
