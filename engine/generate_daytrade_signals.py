#!/usr/bin/env python3
"""
CRON JOB: Generate Day Trade Signals
Schedule: 09:29 IST (Mon-Fri)
Duration: ~5-10 seconds
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from core.signal_engine import generate_signals
from config.config import DAYTRADE_STATE

log = setup_logger('generate_signals')


def main():
    log.info("="*70)
    log.info("GENERATE DAY TRADE SIGNALS - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        state_manager = StateManager(DAYTRADE_STATE)
        signals = generate_signals(state_manager)
        
        log.info(f"✅ Generated {len(signals)} signals")
        for sig in signals:
            log.info(f"  {sig['symbol']} {sig['direction']} @ ₹{sig['live_price']:.2f} ({sig['win_prob']:.1%})")
        
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
