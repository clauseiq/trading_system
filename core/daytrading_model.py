"""
Day Trading Model - XGBoost Intraday Strategy
FIXED: Correct function calls for market data
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime, timedelta
from pathlib import Path

from lib.market_data import download_intraday_data, download_nifty_intraday
from lib.logger import setup_logger
from config.config import (
    DAYTRADE_STOCKS,
    DAYTRADE_TRAIN_DAYS,
    DAYTRADE_INTERVAL,
    CONVICTION_MIN,
    STATE_DIR
)

log = setup_logger('daytrading_model')


def compute_rsi(series, period=14):
    """Compute RSI indicator"""
    if len(series) < period + 1:
        return pd.Series(np.nan, index=series.index)
    
    if isinstance(series, pd.DataFrame):
        series = series.squeeze()
    
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_vwap(df):
    """Compute VWAP - returns Series"""
    def extract_series(col):
        if isinstance(col, pd.DataFrame):
            return col.iloc[:, 0] if col.shape[1] == 1 else col.iloc[:, 0]
        return col
    
    close = extract_series(df['Close'])
    high = extract_series(df['High'])
    low = extract_series(df['Low'])
    volume = extract_series(df['Volume'])
    
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap

def compute_atr(df, period=14):
    """Compute Average True Range"""
    def extract_series(col):
        if isinstance(col, pd.DataFrame):
            return col.iloc[:, 0] if col.shape[1] == 1 else col.iloc[:, 0]
        return col
    
    high = extract_series(df['High'])
    low = extract_series(df['Low'])
    close = extract_series(df['Close'])
    
    # True Range calculation
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr
    
def build_nifty_context(nifty_df):
    """Build 3 Nifty context features"""
    df = nifty_df.copy()
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    def extract_col(col):
        if isinstance(df[col], pd.DataFrame):
            return df[col].iloc[:, 0] if df[col].shape[1] == 1 else df[col].iloc[:, 0]
        return df[col]
    
    df['Close'] = extract_col('Close')
    df['Open'] = extract_col('Open')
    
    df.index = pd.to_datetime(df.index)
    df['date'] = df.index.date
    
    close_series = df['Close']
    open_series = df['Open']
    
    prev_close = close_series.groupby(df['date']).transform('last').shift(1)
    day_open = open_series.groupby(df['date']).transform('first')
    
    gap_series = (day_open - prev_close) / prev_close.replace(0, np.nan)
    df['nifty_gap'] = gap_series
    
    morn_ret_series = (close_series - day_open) / day_open.replace(0, np.nan)
    df['nifty_morn_ret'] = morn_ret_series
    
    df['nifty_rsi'] = compute_rsi(close_series, 14)
    
    return df[['nifty_gap', 'nifty_morn_ret', 'nifty_rsi']]


def build_stock_features(stock_df, nifty_ctx):
    """Build features for one stock"""
    df = stock_df.copy()
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    def extract_col(col):
        if isinstance(df[col], pd.DataFrame):
            return df[col].iloc[:, 0] if df[col].shape[1] == 1 else df[col].iloc[:, 0]
        return df[col]
    
    df['Open'] = extract_col('Open')
    df['High'] = extract_col('High')
    df['Low'] = extract_col('Low')
    df['Close'] = extract_col('Close')
    df['Volume'] = extract_col('Volume')
    
    df.index = pd.to_datetime(df.index)
    df['date'] = df.index.date
    
    open_col = df['Open']
    high_col = df['High']
    low_col = df['Low']
    close_col = df['Close']
    volume_col = df['Volume']
    
    df['range_pct'] = (high_col - low_col) / open_col.replace(0, np.nan)
    df['body_pct'] = (close_col - open_col) / open_col.replace(0, np.nan)
    
    vwap_series = compute_vwap(df)
    df['vwap_dist'] = (close_col - vwap_series) / vwap_series.replace(0, np.nan)
    
    df['rsi'] = compute_rsi(close_col, 14)
    
    avg_vol = volume_col.rolling(window=20, min_periods=1).mean()
    df['vol_ratio'] = volume_col / avg_vol.replace(0, np.nan)
    
    df['prev_mom'] = close_col.pct_change(1)
    df['prev_mom_5'] = close_col.pct_change(5)
    
    day_open = open_col.groupby(df['date']).transform('first')
    df['gap_from_open'] = (close_col - day_open) / day_open.replace(0, np.nan)
    
    df = df.join(nifty_ctx, how='left')
    
    future_close = close_col.shift(-1)
    forward_ret_series = (future_close - close_col) / close_col.replace(0, np.nan)
    df['forward_return'] = forward_ret_series
    
    df['label'] = (df['forward_return'] > 0.005).astype(int)
    
    feature_cols = [
        'range_pct', 'body_pct', 'vwap_dist', 'rsi', 'vol_ratio',
        'prev_mom', 'prev_mom_5', 'gap_from_open',
        'nifty_gap', 'nifty_morn_ret', 'nifty_rsi',
        'forward_return', 'label'
    ]
    
    df = df[feature_cols].dropna()
    
    return df


def train_model(state_manager):
    """Train XGBoost model on multiple stocks"""
    log.info("Starting model training...")
    
    log.info("Downloading 14 stocks...")
    
    # Download Nifty intraday data
    nifty_data = download_nifty_intraday(
        days_back=DAYTRADE_TRAIN_DAYS,
        interval=DAYTRADE_INTERVAL
    )
    
    if nifty_data.empty:
        log.error("Failed to download Nifty data")
        return False
    
    # Build Nifty context
    nifty_ctx = build_nifty_context(nifty_data)
    
    # Download stock data
    stock_data_dict = download_intraday_data(
        symbols=DAYTRADE_STOCKS,
        days_back=DAYTRADE_TRAIN_DAYS,
        interval=DAYTRADE_INTERVAL
    )
    
    if not stock_data_dict:
        log.error("Failed to download any stock data")
        return False
    
    # Build features for each stock
    all_data = []
    
    for symbol, stock_data in stock_data_dict.items():
        try:
            features_df = build_stock_features(stock_data, nifty_ctx)
            
            if len(features_df) < 50:
                log.warning(f"{symbol}: Insufficient data ({len(features_df)} rows)")
                continue
            
            all_data.append(features_df)
            log.info(f"{symbol}: {len(features_df)} training samples")
            
        except Exception as e:
            log.warning(f"{symbol}: Feature build failed - {e}")
            continue
    
    if not all_data:
        log.error("No training data built")
        return False
    
    # Combine all stocks
    df_train = pd.concat(all_data, ignore_index=True)
    log.info(f"Training data: {len(df_train)} rows from {len(all_data)} stocks")
    
    # Prepare features and target
    feature_cols = [
        'range_pct', 'body_pct', 'vwap_dist', 'rsi', 'vol_ratio',
        'prev_mom', 'prev_mom_5', 'gap_from_open',
        'nifty_gap', 'nifty_morn_ret', 'nifty_rsi'
    ]
    
    X = df_train[feature_cols]
    y = df_train['label']
    
    # Train XGBoost
    log.info("Training XGBoost classifier...")
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X, y)
    
    # Save model
    model_path = STATE_DIR / 'daytrade_model.json'
    model.save_model(str(model_path))
    log.info(f"Model saved to {model_path}")
    
    # Update state
    state = {
        'model_status': 'trained',
        'last_train_time': datetime.now().isoformat(),
        'train_samples': len(df_train),
        'train_stocks': len(all_data),
        'feature_cols': feature_cols
    }
    
    state_manager.save(state)
    log.info("Model training complete!")
    
    return True
