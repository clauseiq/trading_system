"""
Trading System Configuration
Complete with all required variables
"""
import os
from pathlib import Path

# ============================================================================
# DIRECTORY PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'storage' / 'state'
LOG_DIR = BASE_DIR / 'storage' / 'logs'

# Create directories
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

RETRY_ATTEMPTS = 3
RETRY_DELAY = 2
REQUEST_TIMEOUT = 30

# ============================================================================
# CAPITAL ALLOCATION
# ============================================================================

TOTAL_CAPITAL = 2000000
DAYTRADE_CAPITAL = 1000000
MOMENTUM_CAPITAL = 1000000

# ============================================================================
# RISK MANAGEMENT
# ============================================================================

BASE_RISK_PCT = 0.01
MAX_POSITION_PCT = 0.10
MAX_TOTAL_EXPOSURE = 0.50
DAYTRADE_STOP_PCT = 0.05
MOMENTUM_STOP_PCT = 0.08

# ============================================================================
# DAY TRADING STRATEGY
# ============================================================================

DAYTRADE_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN',
    'BHARTIARTL', 'AXISBANK', 'KOTAKBANK', 'BAJFINANCE',
    'LT', 'HCLTECH', 'WIPRO', 'SUNPHARMA'
]

DAYTRADE_TRAIN_DAYS = 45
DAYTRADE_INTERVAL = '30m'
CONVICTION_MIN = 0.85
MAX_DAYTRADES_PER_DAY = 6
DAYTRADE_MIN_RR = 2.0
DAYTRADE_MAX_RR = 3.0
DAYTRADE_MAX_HOLD_MINUTES = 105

# ============================================================================
# MOMENTUM STRATEGY
# ============================================================================

MOMENTUM_UNIVERSE = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN',
    'BHARTIARTL', 'AXISBANK', 'KOTAKBANK', 'BAJFINANCE',
    'LT', 'HCLTECH', 'WIPRO', 'SUNPHARMA', 'ASIANPAINT',
    'MARUTI', 'HINDUNILVR', 'ITC', 'ULTRACEMCO', 'TITAN'
]

MOMENTUM_MAX_POSITIONS = 6
MOMENTUM_REBALANCE_DAYS = 14
MOMENTUM_LOOKBACK_DAYS = 14
MOMENTUM_ATR_PERIOD = 14
MOMENTUM_ATR_MULTIPLIER = 2.0
MOMENTUM_TRAILING_STOP_ATR = 2.0
MOMENTUM_MAX_HOLD_DAYS = 14

# ============================================================================
# MARKET DATA
# ============================================================================

DATA_PROVIDER = 'yfinance'
NSE_SUFFIX = '.NS'
MARKET_OPEN_TIME = '09:15'
MARKET_CLOSE_TIME = '15:30'
TRADING_START_TIME = '09:30'
TRADING_END_TIME = '15:20'

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

# ============================================================================
# NOTIFICATIONS
# ============================================================================

NOTIFY_TRADE_SIGNALS = True
NOTIFY_TRADE_EXECUTION = True
NOTIFY_TRADE_CLOSE = True
NOTIFY_DAILY_SUMMARY = True
NOTIFY_ERRORS = True

# ============================================================================
# PAPER TRADING
# ============================================================================

PAPER_TRADING = True

# ============================================================================
# SAFETY LIMITS
# ============================================================================

MAX_DAILY_LOSS_PCT = 0.03
MAX_WEEKLY_LOSS_PCT = 0.08
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

# ============================================================================
# STATE FILE NAMES
# ============================================================================

DAYTRADE_STATE = 'daytrade_state'
MOMENTUM_STATE = 'momentum_state'
PORTFOLIO_STATE = 'portfolio'
SYSTEM_STATE = 'system_state'
```

---

### FILE 3: `requirements.txt`
**REPLACE ENTIRE FILE**
```
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.0
schedule>=1.2.0
pytz>=2023.3
streamlit>=1.28.0
streamlit-autorefresh>=0.0.1
pyTelegramBotAPI>=4.14.0
xgboost>=2.0.0
requests>=2.31.0
