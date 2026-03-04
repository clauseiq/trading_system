"""
Trading System Configuration
COMPLETE - ALL VARIABLES INCLUDED
"""
import os
from pathlib import Path

# ============================================================================
# DIRECTORY PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'storage' / 'state'
LOG_DIR = BASE_DIR / 'storage' / 'logs'

# Create directories if they don't exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# ============================================================================
# API / NETWORK CONFIGURATION
# ============================================================================

# Retry configuration for API calls (yfinance, etc.)
RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests
RETRY_DELAY = 2     # Seconds to wait between retries
REQUEST_TIMEOUT = 30  # Seconds before request times out

# ============================================================================
# CAPITAL ALLOCATION
# ============================================================================

# Total capital
TOTAL_CAPITAL = 2000000  # ₹20 lakhs

# Day trading capital (50%)
DAYTRADE_CAPITAL = 1000000  # ₹10 lakhs

# Momentum strategy capital (50%)
MOMENTUM_CAPITAL = 1000000  # ₹10 lakhs

# ============================================================================
# RISK MANAGEMENT
# ============================================================================

# Base risk per trade (% of capital)
BASE_RISK_PCT = 0.01  # 1%

# Maximum position size (% of capital)
MAX_POSITION_PCT = 0.10  # 10%

# Maximum total exposure (% of capital)
MAX_TOTAL_EXPOSURE = 0.50  # 50%

# Stop loss percentages
DAYTRADE_STOP_PCT = 0.05  # 5% for day trades
MOMENTUM_STOP_PCT = 0.08  # 8% for momentum trades

# ============================================================================
# DAY TRADING STRATEGY
# ============================================================================

# Stocks to trade (Nifty 50 liquid stocks)
DAYTRADE_STOCKS = [
    'RELIANCE',
    'TCS',
    'HDFCBANK',
    'INFY',
    'ICICIBANK',
    'SBIN',
    'BHARTIARTL',
    'AXISBANK',
    'KOTAKBANK',
    'BAJFINANCE',
    'LT',
    'HCLTECH',
    'WIPRO',
    'SUNPHARMA'
]

# Model training parameters
DAYTRADE_TRAIN_DAYS = 45  # Days of historical data for training
DAYTRADE_INTERVAL = '30m'  # 30-minute candles

# Trading parameters
CONVICTION_MIN = 0.85  # Minimum model confidence to trade (85%)
MAX_DAYTRADES_PER_DAY = 6  # Maximum concurrent positions

# Risk/Reward
DAYTRADE_MIN_RR = 2.0  # Minimum 2:1 R:R
DAYTRADE_MAX_RR = 3.0  # Maximum 3:1 R:R

# Position holding time
DAYTRADE_MAX_HOLD_MINUTES = 105  # 1h 45m (9:30 AM to 11:15 AM)

# ============================================================================
# MOMENTUM STRATEGY
# ============================================================================

# Universe of stocks
MOMENTUM_UNIVERSE = [
    'RELIANCE',
    'TCS',
    'HDFCBANK',
    'INFY',
    'ICICIBANK',
    'SBIN',
    'BHARTIARTL',
    'AXISBANK',
    'KOTAKBANK',
    'BAJFINANCE',
    'LT',
    'HCLTECH',
    'WIPRO',
    'SUNPHARMA',
    'ASIANPAINT',
    'MARUTI',
    'HINDUNILVR',
    'ITC',
    'ULTRACEMCO',
    'TITAN'
]

# Portfolio parameters
MOMENTUM_MAX_POSITIONS = 6  # Top 6 momentum stocks
MOMENTUM_REBALANCE_DAYS = 14  # Rebalance every 2 weeks

# Technical parameters
MOMENTUM_LOOKBACK_DAYS = 14  # 14-day momentum calculation
MOMENTUM_ATR_PERIOD = 14  # 14-day ATR for stop loss
MOMENTUM_ATR_MULTIPLIER = 2.0  # 2x ATR for trailing stop

# Exit conditions
MOMENTUM_TRAILING_STOP_ATR = 2.0  # Trail stop at 2x ATR
MOMENTUM_MAX_HOLD_DAYS = 14  # Maximum holding period

# ============================================================================
# MARKET DATA
# ============================================================================

# Data source
DATA_PROVIDER = 'yfinance'  # Using Yahoo Finance

# NSE suffix for Indian stocks
NSE_SUFFIX = '.NS'

# Market hours (IST)
MARKET_OPEN_TIME = '09:15'
MARKET_CLOSE_TIME = '15:30'

# Trading hours
TRADING_START_TIME = '09:30'
TRADING_END_TIME = '15:20'

# ============================================================================
# LOGGING
# ============================================================================

# Log levels
LOG_LEVEL = 'INFO'

# Log file settings
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log rotation
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ============================================================================
# NOTIFICATIONS
# ============================================================================

# Telegram notification settings
NOTIFY_TRADE_SIGNALS = True
NOTIFY_TRADE_EXECUTION = True
NOTIFY_TRADE_CLOSE = True
NOTIFY_DAILY_SUMMARY = True
NOTIFY_ERRORS = True

# ============================================================================
# PAPER TRADING
# ============================================================================

PAPER_TRADING = True  # Always use paper trading

# ============================================================================
# SAFETY LIMITS
# ============================================================================

# Daily loss limit
MAX_DAILY_LOSS_PCT = 0.03  # 3%

# Weekly loss limit
MAX_WEEKLY_LOSS_PCT = 0.08  # 8%

# Consecutive loss limit
MAX_CONSECUTIVE_LOSSES = 5

# ============================================================================
# PERFORMANCE TRACKING
# ============================================================================

TRACK_SHARPE_RATIO = True
TRACK_MAX_DRAWDOWN = True
TRACK_WIN_RATE = True
TRACK_PROFIT_FACTOR = True

REVIEW_PERIOD_DAYS = 30

# ============================================================================
# DEBUG
# ============================================================================

DEBUG_MODE = False
VERBOSE = False
SAVE_MODEL_PREDICTIONS = True
SAVE_FEATURE_IMPORTANCE = True
