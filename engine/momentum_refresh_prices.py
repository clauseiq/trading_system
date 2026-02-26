#!/usr/bin/env python3
"""
CRON JOB: Momentum Price Refresh
Schedule: Every 5 minutes during market hours (Mon-Fri)
Duration: 2-5 seconds
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, date
import pytz
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.market_data import get_current_prices
from config.config import MOMENTUM_STATE, TIMEZONE

log = setup_logger('momentum_refresh')


def is_market_hours():
    """Check if within market hours (09:15 - 15:30 IST)"""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    current_time = now.time()
    
    from datetime import time
    market_open = time(9, 15)
    market_close = time(15, 30)
    
    return market_open <= current_time <= market_close


def refresh_prices(state_manager):
    """Update live prices for all positions"""
    state = state_manager.load()
    positions = state.get('positions', {})
    
    if not positions:
        log.debug("No positions to refresh")
        return
    
    # Get current prices
    symbols = list(positions.keys())
    prices = get_current_prices(symbols)
    
    updated = 0
    
    for symbol, pos in positions.items():
        current_price = prices.get(symbol)
        if current_price:
            pos['live_price'] = current_price
            pos['price_updated_at'] = datetime.now().strftime("%H:%M:%S")
            updated += 1
    
    state['positions'] = positions
    state['price_last_updated'] = datetime.now().strftime("%H:%M:%S IST")
    state_manager.save(state)
    
    log.info(f"Refreshed prices for {updated}/{len(symbols)} positions")


def main():
    # Don't log header for this frequent job
    if date.today().weekday() >= 5:
        return 0
    
    if not is_market_hours():
        return 0
    
    try:
        state_manager = StateManager(MOMENTUM_STATE)
        refresh_prices(state_manager)
        return 0
    
    except Exception as e:
        log.error(f"Price refresh error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
