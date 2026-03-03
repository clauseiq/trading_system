"""
DAY TRADING MODEL
XGBoost-based intraday prediction model
"""
import pandas as pd
import numpy as np
from datetime import date
from typing import Dict, List, Tuple
from lib.logger import setup_logger
from lib.market_data import download_intraday_data, download_nifty_intraday
from config.config import (
    DAYTRADE_STATE, DAYTRADE_TRAIN_DAYS, DAYTRADE_UNIVERSE,
    XGB_PARAMS, DAYTRADE_CONVICTION_THRESHOLD
)

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

log = setup_logger(__name__)

# ─── Feature Engineering ─────────────────────────────────────────────────────

def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Compute RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Compute Average True Range"""
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period).mean()


def build_stock_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build 9 stock-specific features"""
    feat = pd.DataFrame(index=df.index)
    
    # Price-based
    feat['returns'] = df['Close'].pct_change()
    feat['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
    
    # Volatility
    feat['volatility'] = feat['returns'].rolling(10).std()
    feat['atr'] = compute_atr(df, 14)
    
    # Momentum
    feat['rsi'] = compute_rsi(df['Close'], 14)
    feat['price_sma_ratio'] = df['Close'] / df['Close'].rolling(20).mean()
    
    # Volume
    feat['volume_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
    feat['vwap'] = (df['Close'] * df['Volume']).rolling(10).sum() / df['Volume'].rolling(10).sum()
    feat['vwap_dist'] = (df['Close'] - feat['vwap']) / feat['vwap']
    
    return feat


def build_nifty_context(nifty_df):
    """
    Build 3 Nifty context features
    FIXED: Handle multi-column DataFrame from yfinance properly
    """
    df = nifty_df.copy()
    
    # Handle multi-level columns from yfinance (e.g., ('Close', '^NSEI'))
    # Flatten to single level if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df.index = pd.to_datetime(df.index)
    df['date'] = df.index.date
    
    # Extract Close and Open as Series (not DataFrames)
    # Use .squeeze() to convert single-column DataFrame to Series
    close_series = df['Close'].squeeze() if isinstance(df['Close'], pd.DataFrame) else df['Close']
    open_series = df['Open'].squeeze() if isinstance(df['Open'], pd.DataFrame) else df['Open']
    
    # Gap - calculate with Series to avoid DataFrame assignment error
    prev_close = close_series.groupby(df['date']).transform('last').shift(1)
    day_open = open_series.groupby(df['date']).transform('first')
    
    # Calculate gap as Series (this will be a Series, not DataFrame)
    gap_series = (day_open - prev_close) / prev_close.replace(0, np.nan)
    df['nifty_gap'] = gap_series
    
    # Morning return - calculate as Series
    morn_ret_series = (close_series - day_open) / day_open.replace(0, np.nan)
    df['nifty_morn_ret'] = morn_ret_series
    
    # RSI - ensure we pass a Series
    df['nifty_rsi'] = compute_rsi(close_series, 14)
    
    return df[['nifty_gap', 'nifty_morn_ret', 'nifty_rsi']]


def make_labels(df: pd.DataFrame, horizon_bars: int = 4) -> pd.Series:
    """
    Create trading labels
    Class 2 (LONG): forward return > +1%
    Class 0 (SHORT): forward return < -1%
    Class 1 (NEUTRAL): else
    """
    fwd_ret = df['Close'].pct_change(horizon_bars).shift(-horizon_bars) * 100
    labels = pd.Series(1, index=df.index, name='label')
    labels[fwd_ret > 1.0] = 2   # LONG
    labels[fwd_ret < -1.0] = 0  # SHORT
    return labels


# ─── Model Training ──────────────────────────────────────────────────────────

def train_model(state_manager) -> bool:
    """
    Train XGBoost model on recent data
    
    Returns:
        True if successful, False otherwise
    """
    if not XGB_AVAILABLE:
        log.error("XGBoost not installed")
        return False
    
    today_str = str(date.today())
    state = state_manager.load()
    
    if state.get('last_train_date') == today_str:
        log.info("Model already trained today")
        return True
    
    log.info("Starting model training...")
    
    # Download data
    log.info(f"Downloading {len(DAYTRADE_UNIVERSE)} stocks...")
    stock_data = download_intraday_data(DAYTRADE_UNIVERSE, DAYTRADE_TRAIN_DAYS + 5)
    nifty_data = download_nifty_intraday(DAYTRADE_TRAIN_DAYS + 5)
    
    if len(stock_data) < 3:
        log.error("Too few stocks downloaded - aborting")
        return False
    
    # Build Nifty context
    nifty_ctx = None
    if not nifty_data.empty:
        nifty_ctx = build_nifty_context(nifty_data)
    
    # Build training data
    all_X, all_y = [], []
    feature_cols = [
        'returns', 'log_returns', 'volatility', 'atr', 'rsi',
        'price_sma_ratio', 'volume_ratio', 'vwap_dist',
        'nifty_gap', 'nifty_morn_ret', 'nifty_rsi'
    ]
    
    for symbol, df in stock_data.items():
        try:
            # Stock features
            stock_feat = build_stock_features(df)
            
            # Merge Nifty context
            if nifty_ctx is not None:
                for col in ['nifty_gap', 'nifty_morn_ret', 'nifty_rsi']:
                    stock_feat[col] = nifty_ctx[col].reindex(df.index, method='ffill')
            else:
                stock_feat['nifty_gap'] = 0.0
                stock_feat['nifty_morn_ret'] = 0.0
                stock_feat['nifty_rsi'] = 50.0
            
            # Labels
            labels = make_labels(df, horizon_bars=4)
            
            # Combine
            stock_feat['label'] = labels
            stock_feat = stock_feat.dropna(subset=feature_cols + ['label'])
            
            if len(stock_feat) < 10:
                continue
            
            all_X.append(stock_feat[feature_cols])
            all_y.append(stock_feat['label'].astype(int))
            
        except Exception as e:
            log.warning(f"{symbol}: Feature build failed - {e}")
            continue
    
    if not all_X:
        log.error("No training data built")
        return False
    
    X = pd.concat(all_X).reset_index(drop=True)
    y = pd.concat(all_y).reset_index(drop=True)
    
    log.info(f"Training on {len(X):,} samples, {y.value_counts().to_dict()} class distribution")
    
    # Train XGBoost
    try:
        # Class weights for imbalance
        class_weights = {0: 2.0, 1: 0.5, 2: 2.0}
        sample_weights = y.map(class_weights)
        
        model = xgb.XGBClassifier(**XGB_PARAMS)
        model.fit(X, y, sample_weight=sample_weights, verbose=False)
        
        # Save model
        model_path = DAYTRADE_STATE.parent / "daytrade_model.json"
        model.save_model(str(model_path))
        
        # Update state
        state_manager.update({
            'model_trained': True,
            'last_train_date': today_str,
            'feature_cols': feature_cols,
            'n_features': len(feature_cols),
            'training_samples': len(X)
        })
        
        log.info(f"✅ Model trained successfully ({len(X):,} samples)")
        return True
        
    except Exception as e:
        log.error(f"Model training failed: {e}")
        import traceback
        traceback.print_exc()
        return False
