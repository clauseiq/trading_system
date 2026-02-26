#!/usr/bin/env python3
"""
CLOUD SCHEDULER
Replaces cron for Railway/Render deployment
Runs all trading jobs at scheduled times (IST)
"""
import sys
import os
import time
import schedule
import logging
from pathlib import Path
from datetime import datetime
import pytz

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.logger import setup_logger

log = setup_logger('scheduler')

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Job file paths
JOBS = {
    'train_model': BASE_DIR / 'engine' / 'train_daytrade_model.py',
    'momentum_morning': BASE_DIR / 'engine' / 'momentum_morning.py',
    'generate_signals': BASE_DIR / 'engine' / 'generate_daytrade_signals.py',
    'execute_trades': BASE_DIR / 'engine' / 'execute_daytrade.py',
    'close_positions': BASE_DIR / 'engine' / 'close_daytrade.py',
    'momentum_eod': BASE_DIR / 'engine' / 'momentum_eod.py',
    'refresh_prices': BASE_DIR / 'engine' / 'momentum_refresh_prices.py',
}


def is_trading_day():
    """Check if today is a trading day (Monday-Friday)"""
    now = datetime.now(IST)
    return now.weekday() < 5  # 0-4 = Mon-Fri


def run_job(job_name, job_path, timeout=300):
    """
    Run a job by importing and executing its main() function
    
    Args:
        job_name: Display name for the job
        job_path: Path to the Python file
        timeout: Maximum execution time in seconds
    """
    log.info(f"Starting: {job_name}")
    start_time = time.time()
    
    try:
        # Import the job module
        import importlib.util
        spec = importlib.util.spec_from_file_location("job_module", job_path)
        if not spec or not spec.loader:
            log.error(f"Could not load job: {job_path}")
            return
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the main function
        if hasattr(module, 'main'):
            result = module.main()
            duration = time.time() - start_time
            
            if result == 0:
                log.info(f"Completed: {job_name} ({duration:.1f}s)")
            else:
                log.error(f"Failed: {job_name} (exit code {result}, {duration:.1f}s)")
        else:
            log.error(f"No main() function in {job_name}")
    
    except Exception as e:
        duration = time.time() - start_time
        log.error(f"Crashed: {job_name} ({duration:.1f}s) - {str(e)}")
        import traceback
        log.error(traceback.format_exc())


def schedule_jobs():
    """
    Schedule all trading jobs
    
    Note: Cloud platforms run on UTC, so we convert IST times to UTC
    IST = UTC + 5:30
    
    Examples:
    - 09:00 IST = 03:30 UTC
    - 09:30 IST = 04:00 UTC
    - 15:20 IST = 09:50 UTC
    """
    
    # Day Trading Jobs
    
    # 09:00 IST (03:30 UTC) - Train Model
    schedule.every().day.at("03:30").do(
        lambda: is_trading_day() and run_job(
            "Train Day Trade Model", 
            JOBS['train_model'], 
            timeout=180
        )
    ).tag('daytrade')
    
    # 09:29 IST (03:59 UTC) - Generate Signals
    schedule.every().day.at("03:59").do(
        lambda: is_trading_day() and run_job(
            "Generate Day Trade Signals", 
            JOBS['generate_signals'], 
            timeout=30
        )
    ).tag('daytrade')
    
    # 09:30 IST (04:00 UTC) - Execute Trades
    schedule.every().day.at("04:00").do(
        lambda: is_trading_day() and run_job(
            "Execute Day Trades", 
            JOBS['execute_trades'], 
            timeout=30
        )
    ).tag('daytrade')
    
    # 11:15 IST (05:45 UTC) - Close Positions
    schedule.every().day.at("05:45").do(
        lambda: is_trading_day() and run_job(
            "Close Day Trade Positions", 
            JOBS['close_positions'], 
            timeout=30
        )
    ).tag('daytrade')
    
    # Momentum Strategy Jobs
    
    # 09:20 IST (03:50 UTC) - Momentum Morning
    schedule.every().day.at("03:50").do(
        lambda: is_trading_day() and run_job(
            "Momentum Morning Session", 
            JOBS['momentum_morning'], 
            timeout=60
        )
    ).tag('momentum')
    
    # 15:20 IST (09:50 UTC) - Momentum EOD
    schedule.every().day.at("09:50").do(
        lambda: is_trading_day() and run_job(
            "Momentum EOD Session", 
            JOBS['momentum_eod'], 
            timeout=30
        )
    ).tag('momentum')
    
    # Every 5 minutes - Refresh Prices (during market hours)
    # Market hours: 09:15 - 15:30 IST = 03:45 - 10:00 UTC
    schedule.every(5).minutes.do(
        lambda: run_job(
            "Refresh Prices", 
            JOBS['refresh_prices'], 
            timeout=15
        )
    ).tag('refresh')
    
    log.info("All jobs scheduled")
    log.info("   Note: Times shown in UTC, jobs execute at correct IST times")


def print_schedule():
    """Print the job schedule in a readable format"""
    log.info("JOB SCHEDULE (IST times shown, executed in UTC):")
    log.info("")
    log.info("  Day Trading:")
    log.info("    - 09:00 IST (03:30 UTC) - Train Day Trade Model")
    log.info("    - 09:29 IST (03:59 UTC) - Generate Signals")
    log.info("    - 09:30 IST (04:00 UTC) - Execute Trades")
    log.info("    - 11:15 IST (05:45 UTC) - Close Positions")
    log.info("")
    log.info("  Momentum Strategy:")
    log.info("    - 09:20 IST (03:50 UTC) - Morning Session")
    log.info("    - 15:20 IST (09:50 UTC) - EOD Session")
    log.info("    - Every 5 minutes      - Refresh Prices")
    log.info("")


def check_job_files():
    """Verify all job files exist"""
    missing = []
    for name, path in JOBS.items():
        if not path.exists():
            missing.append(f"{name} ({path})")
    
    if missing:
        log.error("Missing job files:")
        for m in missing:
            log.error(f"   - {m}")
        return False
    
    log.info("All job files found")
    return True


def main():
    """Main scheduler loop"""
    log.info("="*70)
    log.info("CLOUD SCHEDULER STARTING")
    log.info("="*70)
    log.info(f"Timezone: {IST}")
    log.info(f"Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    log.info(f"Base directory: {BASE_DIR}")
    log.info("")
    
    # Check if all job files exist
    if not check_job_files():
        log.error("Cannot start scheduler - missing job files")
        return 1
    
    # Schedule all jobs
    schedule_jobs()
    
    # Print schedule
    print_schedule()
    
    log.info("="*70)
    log.info("Scheduler is running. Press Ctrl+C to stop.")
    log.info("="*70)
    log.info("")
    
    # Check if today is a trading day
    if is_trading_day():
        log.info("Today is a trading day (Mon-Fri)")
    else:
        weekday = datetime.now(IST).strftime('%A')
        log.info(f"Today is {weekday} - No trading scheduled")
    
    log.info("")
    
    # Main loop
    loop_count = 0
    while True:
        try:
            # Run pending jobs
            schedule.run_pending()
            
            # Log heartbeat every 30 minutes
            if loop_count % 60 == 0:  # 60 * 30 seconds = 30 minutes
                now = datetime.now(IST)
                log.info(f"Heartbeat: {now.strftime('%H:%M:%S IST')} - Scheduler running")
            
            # Sleep for 30 seconds
            time.sleep(30)
            loop_count += 1

        except KeyboardInterrupt:
            log.info("")
            log.info("Scheduler stopped by user")
            break
        
        except Exception as e:
            log.error(f"Scheduler error: {e}")
            import traceback
            log.error(traceback.format_exc())
            log.info("Continuing scheduler...")
            time.sleep(60)  # Wait 1 minute before retry
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
