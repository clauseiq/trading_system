"""
TRADING SYSTEM CONFIGURATION
Production-grade configuration management
"""
import os
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "storage" / "state"
LOG_DIR = BASE_DIR / "storage" / "logs"

# Load environment from .env if present (prefer python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except Exception:
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k.strip(), v)
        except Exception:
            pass

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─── State Files ─────────────────────────────────────────────────────────────
MOMENTUM_STATE = STATE_DIR / "momentum_state.json"
DAYTRADE_STATE = STATE_DIR / "daytrade_state.json"
PORTFOLIO_STATE = STATE_DIR / "portfolio.json"

# ─── Logging ─────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ─── Market Data ─────────────────────────────────────────────────────────────
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 30  # seconds

# ─── Telegram ────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_ENABLED = bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)

# ─── Strategy Toggles ────────────────────────────────────────────────────────
ENABLE_MOMENTUM = os.getenv("ENABLE_MOMENTUM", "true").lower() in ("true", "1", "yes")
ENABLE_DAYTRADE = os.getenv("ENABLE_DAYTRADE", "true").lower() in ("true", "1", "yes")

# ─── Trading Parameters ──────────────────────────────────────────────────────
PAPER_TRADING = True  # Set to False for live trading

# Momentum Strategy
MOMENTUM_REBALANCE_DAYS = 14
MOMENTUM_TOP_N = 6
MOMENTUM_BASE_RISK = 0.01  # 1%
MOMENTUM_ATR_MULT = 2.0
MOMENTUM_MAX_POSITION_PCT = 0.15

# Day Trade Strategy
DAYTRADE_TRAIN_DAYS = 30
DAYTRADE_CONVICTION_THRESHOLD = 0.85
DAYTRADE_TOP_N_LONGS = 3
DAYTRADE_TOP_N_SHORTS = 3
DAYTRADE_ATR_STOP_MULT = 1.5
DAYTRADE_MAX_CAPITAL_PCT = 0.10
DAYTRADE_COST_PCT = 0.0015

# Day Trade Capital (independent from momentum)
DAYTRADE_CAPITAL = 1_000_000

# Momentum Capital
MOMENTUM_CAPITAL = 1_000_000

# Risk Management
RR_HIGH_CONVICTION = 3.0  # win_prob >= 0.95
RR_BASE = 2.0             # win_prob >= 0.85
CONVICTION_MIN = 0.85
CONVICTION_HIGH = 0.95

# ─── Market Hours (IST) ──────────────────────────────────────────────────────
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"
TIMEZONE = "Asia/Kolkata"

# ─── Stock Universe ──────────────────────────────────────────────────────────
DAYTRADE_UNIVERSE = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "SBIN", "BHARTIARTL", "AXISBANK", "KOTAKBANK", "BAJFINANCE",
    "LT", "HCLTECH", "WIPRO", "SUNPHARMA",
]

# XGBoost Parameters
XGB_PARAMS = {
    "n_estimators": 60,
    "max_depth": 3,
    "learning_rate": 0.15,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "tree_method": "hist",
    "device": "cpu",
    "n_jobs": 1,
    "verbosity": 0,
    "objective": "multi:softprob",
    "num_class": 3,
    "eval_metric": "mlogloss",
}
