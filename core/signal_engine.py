"""
DAY TRADING SIGNAL ENGINE
Generate intraday trading signals using trained model
FIXED: Correct state check, model path, AND build_stock_features() signature
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
    DAYTRADE_TOP_N_LONGS, DAYTRADE_TOP_N_SHORTS, DAYTRADE_ATR_STOP_MULT,
    STATE_DIR
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
    
    # Check if model is trained (FIXED: check model_status not model_trained)
    if state.get('model_status') != 'trained':
        log.warning("Model not trained - cannot generate signals")
        return []
    
    # Load model (FIXED: use STATE_DIR not DAYTRADE_STATE.parent)
    model_path = STATE_DIR / "daytrade_model.json"
    if not model_path.exists():
        log.error(f"Model file not found at {model_path}")
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
    
    if not stock_data or nifty_data.empty:
        log.error("Failed to download market data")
        return []
    
    # Build NIFTY context once (FIXED: build this first)
    nifty_ctx = build_nifty_context(nifty_data)
    
    # Build features for all stocks
    log.info(f"Building features for {len(stock_data)} stocks...")
    
    predictions = []
    
    for symbol, df in stock_data.items():
        try:
            if df.empty or len(df) < 30:
                continue
            
            # Build features (FIXED: pass nifty_ctx as second argument)
            features_df = build_stock_features(df, nifty_ctx)
            
            if features_df.empty:
                continue
            
            # Get the latest row
            latest_features = features_df.iloc[-1].to_dict()
            
            # Ensure all feature columns exist
            feature_row = pd.DataFrame([latest_features])[feature_cols]
            
            # Predict
            prob = model.predict_proba(feature_row)[0][1]  # Probability of UP
            
            # Get current price and ATR
            current_price = float(df['Close'].iloc[-1])
            atr = compute_atr(df)
            
            predictions.append({
                'symbol': symbol,
                'win_prob': prob,
                'current_price': current_price,
                'atr': atr
            })
        
        except Exception as e:
            log.warning(f"{symbol}: Error generating signal - {e}")
            continue
    
    if not predictions:
        log.warning("No valid predictions generated")
        return []
    
    # Filter by conviction threshold
    high_conviction = [p for p in predictions if p['win_prob'] >= DAYTRADE_CONVICTION_THRESHOLD]
    
    if not high_conviction:
        log.info(f"No signals with conviction >= {DAYTRADE_CONVICTION_THRESHOLD}")
        return []
    
    # Sort by conviction descending
    high_conviction.sort(key=lambda x: x['win_prob'], reverse=True)
    
    # Take top N longs
    signals = []
    for pred in high_conviction[:DAYTRADE_TOP_N_LONGS]:
        stop_loss = pred['current_price'] - (DAYTRADE_ATR_STOP_MULT * pred['atr'])
        
        signals.append({
            'symbol': pred['symbol'],
            'direction': 'LONG',
            'win_prob': pred['win_prob'],
            'live_price': pred['current_price'],
            'stop_loss': stop_loss,
            'atr': pred['atr']
        })
        
        log.info(f"✅ {pred['symbol']}: Conviction={pred['win_prob']:.1%}, Price=₹{pred['current_price']:.2f}, Stop=₹{stop_loss:.2f}")
    
    log.info(f"Generated {len(signals)} signals from {len(predictions)} stocks")
    
    return signals
