#!/usr/bin/env python3
"""
Train Day Trade Model
Schedule: 09:00 IST (Mon-Fri)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from core.daytrading_model import train_model
from config.config import DAYTRADE_STATE

log = setup_logger('train_daytrade')


def is_trading_day():
    """Check if today is Mon-Fri"""
    return date.today().weekday() < 5


def main():
    """Main training function"""
    log.info("="*70)
    log.info("DAY TRADE MODEL TRAINING - START")
    log.info("="*70)
    
    if not is_trading_day():
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        state_manager = StateManager(DAYTRADE_STATE)
        success = train_model(state_manager)
        
        if success:
            log.info("✅ Model training complete")
            return 0
        else:
            log.error("❌ Model training failed")
            return 1
    
    except Exception as e:
        log.error(f"💥 Fatal error: {e}", exc_info=True)
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
