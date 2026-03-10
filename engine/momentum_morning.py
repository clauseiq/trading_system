#!/usr/bin/env python3
"""
Momentum Morning Check
Schedule: 09:20 IST (Mon-Fri)
Check stop losses and targets for momentum positions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.telegram_notifier import TelegramNotifier
from lib.market_data import get_current_prices
from config.config import MOMENTUM_STATE, STATE_DIR

log = setup_logger('momentum_morning')


def check_positions(state_manager):
    """Check all momentum positions for stops and targets"""
    state = state_manager.load()
    
    positions = state.get('positions', {})
    
    if not positions:
        log.info("No momentum positions to check")
        return
    
    log.info(f"Checking {len(positions)} momentum positions...")
    
    symbols = list(positions.keys())
    current_prices = get_current_prices(symbols)
    
    alerts = []
    
    for symbol, pos in positions.items():
        current_price = current_prices.get(symbol)
        
        if not current_price:
            log.warning(f"{symbol}: Could not get current price")
            continue
        
        entry = pos['entry_price']
        stop = pos['stop_loss']
        highest = pos.get('highest_price', entry)
        
        pnl_pct = ((current_price - entry) / entry) * 100
        
        if current_price <= stop:
            alerts.append(f"🛑 {symbol}: Hit stop @ ₹{current_price:.2f} ({pnl_pct:+.2f}%)")
            log.warning(f"{symbol}: STOP HIT - Current ₹{current_price:.2f} <= Stop ₹{stop:.2f}")
        
        elif current_price > highest:
            pos['highest_price'] = current_price
            log.info(f"{symbol}: New high @ ₹{current_price:.2f}")
        
        else:
            log.info(f"{symbol}: ₹{current_price:.2f} ({pnl_pct:+.2f}%)")
    
    state['positions'] = positions
    state_manager.save(state)
    
    if alerts:
        notifier = TelegramNotifier()
        notifier.send("\n".join(alerts))


def main():
    """Main morning check function"""
    log.info("="*70)
    log.info("MOMENTUM MORNING CHECK - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        state_manager = StateManager(STATE_DIR / f'{MOMENTUM_STATE}.json')
        check_positions(state_manager)
        
        log.info("✅ Morning check complete")
        return 0
    
    except Exception as e:
        log.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
