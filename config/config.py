"""
Trading System Configuration
NIFTY 100 & NIFTY 200 Universe
"""
import os
from pathlib import Path

# ============================================================================
# DIRECTORY PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'storage' / 'state'
LOG_DIR = BASE_DIR / 'storage' / 'logs'

STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
TELEGRAM_ENABLED = bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)

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
DAYTRADE_MAX_CAPITAL_PCT = 1.0  #  ADD THIS - Use 100% of day trade capital
PORTFOLIO_STATE = 'portfolio'  #  ADDED - For compatibility

# ============================================================================
# RISK MANAGEMENT
# ============================================================================

BASE_RISK_PCT = 0.01
MAX_POSITION_PCT = 0.10
MAX_TOTAL_EXPOSURE = 0.50
DAYTRADE_STOP_PCT = 0.05
MOMENTUM_STOP_PCT = 0.08

# ============================================================================
# DAY TRADING STRATEGY - NIFTY 100 UNIVERSE
# ============================================================================

DAYTRADE_STOCKS = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
    'HINDUNILVR', 'BHARTIARTL', 'ITC', 'SBIN', 'BAJFINANCE',
    'KOTAKBANK', 'LT', 'HCLTECH', 'ASIANPAINT', 'MARUTI',
    'AXISBANK', 'TITAN', 'SUNPHARMA', 'ULTRACEMCO', 'BAJAJFINSV',
    'INDUSINDBK', 'ICICIGI', 'SBILIFE', 'HDFCLIFE', 'FEDERALBNK',
    'BANDHANBNK', 'IDFCFIRSTB', 'AUBANK', 'WIPRO', 'TECHM',
    'LTIM', 'PERSISTENT', 'COFORGE', 'MPHASIS', 'LTTS',
    'OFSS', 'BAJAJ-AUTO', 'TATAMOTORS', 'M&M', 'EICHERMOT',
    'HEROMOTOCO', 'TVSMOTOR', 'BOSCHLTD', 'MOTHERSON', 'BHARATFORG',
    'DRREDDY', 'CIPLA', 'DIVISLAB', 'LUPIN', 'AUROPHARMA',
    'TORNTPHARM', 'BIOCON', 'GLENMARK', 'ALKEM', 'NESTLEIND',
    'DABUR', 'MARICO', 'GODREJCP', 'TATACONSUM', 'BRITANNIA',
    'COLPAL', 'PGHH', 'MCDOWELL-N', 'NTPC', 'POWERGRID',
    'ONGC', 'BPCL', 'IOC', 'ADANIGREEN', 'ADANIPOWER',
    'TATAPOWER', 'GAIL', 'TATASTEEL', 'JSWSTEEL', 'HINDALCO',
    'VEDL', 'COALINDIA', 'NMDC', 'SAIL', 'JINDALSTEL',
    'NATIONALUM', 'GRASIM', 'SHREECEM', 'AMBUJACEM', 'ACC',
    'RAMCOCEM', 'ADANIPORTS', 'NBCC', 'INDIGO', 'DMART',
    'PIDILITIND', 'BERGEPAINT', 'HAVELLS', 'VOLTAS', 'CROMPTON',
    'DIXON', 'WHIRLPOOL', 'BATAINDIA', 'SIEMENS', 'ABB'
]

DAYTRADE_UNIVERSE = DAYTRADE_STOCKS
DAYTRADE_CONVICTION_THRESHOLD = 0.85
DAYTRADE_TOP_N_LONGS = 6
DAYTRADE_TOP_N_SHORTS = 0
DAYTRADE_ATR_STOP_MULT = 2.0
DAYTRADE_TRAIN_DAYS = 45
DAYTRADE_INTERVAL = '30m'
CONVICTION_MIN = 0.85
MAX_DAYTRADES_PER_DAY = 6
DAYTRADE_MIN_RR = 2.0
DAYTRADE_MAX_RR = 3.0
DAYTRADE_MAX_HOLD_MINUTES = 105

# ============================================================================
# MOMENTUM STRATEGY - NIFTY 200 UNIVERSE
# ============================================================================

MOMENTUM_UNIVERSE = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
    'HINDUNILVR', 'BHARTIARTL', 'ITC', 'SBIN', 'BAJFINANCE',
    'KOTAKBANK', 'LT', 'HCLTECH', 'ASIANPAINT', 'MARUTI',
    'AXISBANK', 'TITAN', 'SUNPHARMA', 'ULTRACEMCO', 'BAJAJFINSV',
    'INDUSINDBK', 'ICICIGI', 'SBILIFE', 'HDFCLIFE', 'BAJAJ-AUTO',
    'SIEMENS', 'ADANIENT', 'ADANIPORTS', 'JSWSTEEL', 'NESTLEIND',
    'WIPRO', 'TATAMOTORS', 'NTPC', 'POWERGRID', 'ONGC',
    'BPCL', 'IOC', 'GRASIM', 'TATASTEEL', 'HINDALCO',
    'VEDL', 'COALINDIA', 'DRREDDY', 'CIPLA', 'DIVISLAB',
    'EICHERMOT', 'TECHM', 'SHREECEM', 'BRITANNIA', 'TATACONSUM',
    'ADANIGREEN', 'ADANIPOWER', 'TATAPOWER', 'M&M', 'HEROMOTOCO',
    'TVSMOTOR', 'BOSCHLTD', 'HAVELLS', 'VOLTAS', 'CROMPTON',
    'DIXON', 'WHIRLPOOL', 'BATAINDIA', 'PIDILITIND', 'BERGEPAINT',
    'INDIGO', 'DMART', 'DABUR', 'MARICO', 'GODREJCP',
    'COLPAL', 'PGHH', 'MCDOWELL-N', 'LUPIN', 'AUROPHARMA',
    'TORNTPHARM', 'BIOCON', 'GLENMARK', 'ALKEM', 'AMBUJACEM',
    'ACC', 'RAMCOCEM', 'BALKRISIND', 'AMARAJABAT', 'PERSISTENT',
    'COFORGE', 'MPHASIS', 'LTTS', 'OFSS', 'LTIM',
    'SAIL', 'JINDALSTEL', 'NATIONALUM', 'NMDC', 'APOLLOHOSP',
    'FORTIS', 'MAXHEALTH', 'LALPATHLAB', 'METROPOLIS', 'GAIL',
    'PETRONET', 'IGL', 'MGL', 'CUMMINSIND', 'ABB',
    'SCHAEFFLER', 'SKFINDIA', 'MOTHERSON', 'BHARATFORG', 'ASHOKLEY',
    'ESCORTS', 'EXIDEIND', 'NBCC', 'BEL', 'HAL',
    'IRCTC', 'CONCOR', 'ZOMATO', 'NYKAA', 'PAYTM',
    'PNB', 'BANKBARODA', 'CANBK', 'UNIONBANK', 'IDFCFIRSTB',
    'FEDERALBNK', 'BANDHANBNK', 'RBLBANK', 'AUBANK', 'CHOLAFIN',
    'SBICARD', 'HDFCAMC', 'MUTHOOTFIN', 'MANAPPURAM', 'RECLTD',
    'PFC', 'IRFC', 'HUDCO', 'PAGEIND', 'HINDPETRO',
    'MRPL', 'OIL', 'GNFC', 'UPL', 'PIIND',
    'ATUL', 'DEEPAKNTR', 'TATACHEM', 'CHAMBLFERT', 'COROMANDEL',
    'SUMICHEM', 'NAVINFLUOR', 'SRF', 'TRENT', 'ABFRL',
    'JUBLFOOD', 'WESTLIFE', 'SAPPHIRE', 'PVR', 'INOXLEISURE',
    'RELAXO', 'BATA', 'SYMPHONY', 'ASTRAL', 'SUPREMEIND',
    'POLYCAB', 'KEI', 'FINOLEX', 'CENTURYTEX', 'RAYMOND',
    'ARVIND', 'GUJGAS', 'TORNTPOWER', 'JSWENERGY', 'NHPC',
    'SJVN', 'THERMAX', 'CESC', 'ZEEL', 'SUNTV',
    'PVRINOX', 'DISHTV', 'NETWORK18', 'BALRAMCHIN', 'DCMSHRIRAM',
    'GSPL', 'AIAENG', 'GRINDWELL', 'CARBORUNIV', 'CREDITACC',
    'LINDEINDIA', 'FINEORG', 'EIDPARRY', 'MANINFRA', 'RVNL',
    'IRCON', 'RAILTEL', 'MAZDOCK', 'COCHINSHIP', 'GMRINFRA'
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
