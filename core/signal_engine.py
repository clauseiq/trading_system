"""
DAY TRADING SIGNAL ENGINE
Generate intraday trading signals using trained model
"""
import pandas as pd
import numpy as np
from datetime import date
from typing import List, Dict
from lib.logger import setup_logger
from lib.market_data import download_intraday_data, download_nifty_intraday
from core.daytrading_model import build_stock_features, build_nifty_context, compute_atr
from config.config import (
    DAYTRADE_STATE, DAYTRADE_UNIVERSE, DAYTRADE_CONVICTION_THRESHOLD,
    DAYTRADE_TOP_N_LONGS, DAYTRADE_TOP_N_SHORTS, DAYTRADE_ATR_STOP_MULT
)

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

log = setup_logger(__name__)


def generate_signals(state_manager) -> List[Dict]:
    """
    Generate trading signals for today
    
    Returns:
        List of signal dicts with: symbol, direction, win_prob, live_price, stop_loss, atr
    """
    if not XGB_AVAILABLE:
        log.error("XGBoost not installed")
        return []
    
    state = state_manager.load()
    
    # Check if model is trained
    if not state.get('model_trained'):
        log.warning("Model not trained - cannot generate signals")
        return []
    
    # Load model
    model_path = DAYTRADE_STATE.parent / "daytrade_model.json"
    if not model_path.exists():
        log.error("Model file not found")
        return []
    
    try:
        model = xgb.XGBClassifier()
        model.load_model(str(model_path))
        feature_cols = state.get('feature_cols', [])
    except Exception as e:
        log.error(f"Failed to load model: {e}")
        return []
    
    # Download latest data
    log.info("Downloading latest market data...")
    stock_data = download_intraday_data(DAYTRADE_UNIVERSE, days_back=7)
    nifty_data = download_nifty_intraday(days_back=7)
    
    if not stock_data:
        log.warning("No stock data downloaded")
        return []
    
    # Build Nifty context
    nifty_ctx = None
    if not nifty_data.empty:
        nifty_ctx = build_nifty_context(nifty_data)
    
    # Generate predictions
    predictions = []
    
    for symbol, df in stock_data.items():
        try:
            # Get latest complete bar
            if len(df) < 20:
                continue
            
            # Build features
            stock_feat = build_stock_features(df)
            
            # Merge Nifty context
            if nifty_ctx is not None:
                for col in ['nifty_gap', 'nifty_morn_ret', 'nifty_rsi']:
                    stock_feat[col] = nifty_ctx[col].reindex(df.index, method='ffill')
            else:
                stock_feat['nifty_gap'] = 0.0
                stock_feat['nifty_morn_ret'] = 0.0
                stock_feat['nifty_rsi'] = 50.0
            
            # Get latest row
            latest = stock_feat[feature_cols].iloc[-1:].fillna(0)
            
            # Predict
            proba = model.predict_proba(latest)[0]
            predicted_class = int(proba.argmax())
            confidence = float(proba[predicted_class])
            
            # Only high-conviction trades
            if confidence < DAYTRADE_CONVICTION_THRESHOLD:
                continue
            
            # Skip neutral signals
            if predicted_class == 1:
                continue
            
            # Get live price and ATR
            live_price = float(df['Close'].iloc[-1])
            atr = float(compute_atr(df, 14).iloc[-1])
            
            # Direction
            direction = "LONG" if predicted_class == 2 else "SHORT"
            
            # Stop loss
            if direction == "LONG":
                stop_loss = live_price - (atr * DAYTRADE_ATR_STOP_MULT)
            else:
                stop_loss = live_price + (atr * DAYTRADE_ATR_STOP_MULT)
            
            predictions.append({
                'symbol': symbol,
                'direction': direction,
                'win_prob': confidence,
                'live_price': live_price,
                'stop_loss': stop_loss,
                'atr': atr,
                'timestamp': str(pd.Timestamp.now())
            })
            
        except Exception as e:
            log.warning(f"{symbol}: Signal generation failed - {e}")
            continue
    
    # Rank and select top signals
    if not predictions:
        log.info("No high-conviction signals generated")
        return []
    
    # Separate longs and shorts
    longs = [p for p in predictions if p['direction'] == 'LONG']
    shorts = [p for p in predictions if p['direction'] == 'SHORT']
    
    # Sort by confidence
    longs.sort(key=lambda x: x['win_prob'], reverse=True)
    shorts.sort(key=lambda x: x['win_prob'], reverse=True)
    
    # Take top N of each
    selected = longs[:DAYTRADE_TOP_N_LONGS] + shorts[:DAYTRADE_TOP_N_SHORTS]
    
    log.info(f"Generated {len(selected)} high-conviction signals ({len(longs[:DAYTRADE_TOP_N_LONGS])} longs, {len(shorts[:DAYTRADE_TOP_N_SHORTS])} shorts)")
    
    # Save to state
    state_manager.update({
        'daily_signals': selected,
        'last_signal_date': str(date.today())
    })
    
    return selected
