#!/usr/bin/env python3
"""
Generate Day Trade Signals
Schedule: 09:29 IST (Mon-Fri)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.logger import setup_logger
from lib.state_manager import StateManager
from core.signal_engine import generate_signals
from config.config import DAYTRADE_STATE

log = setup_logger('generate_signals')


def main():
    """Generate trading signals"""
    log.info("="*70)
    log.info("GENERATE SIGNALS - START")
    log.info("="*70)
    
    try:
        state_manager = StateManager(DAYTRADE_STATE)
        signals = generate_signals(state_manager)
        
        if signals:
            log.info(f"✅ Generated {len(signals)} signals")
            return 0
        else:
            log.info("No signals generated")
            return 0
    
    except Exception as e:
        log.error(f"💥 Error: {e}", exc_info=True)
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
