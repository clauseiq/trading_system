#!/usr/bin/env python3
"""
CRON JOB: Train Day Trade Model
Schedule: 09:00 IST (Mon-Fri)
Duration: ~30-60 seconds
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from core.daytrading_model import train_model
from config.config import DAYTRADE_STATE

log = setup_logger('train_daytrade')


def is_trading_day() -> bool:
    """Check if today is a trading day (Mon-Fri)"""
    return date.today().weekday() < 5


def main():
    """Main execution"""
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
            log.info("✅ Model training completed successfully")
            return 0
        else:
            log.error("❌ Model training failed")
            return 1
    
    except Exception as e:
        log.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
