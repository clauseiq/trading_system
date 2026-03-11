#!/usr/bin/env python3
"""
Momentum Rebalance - Select and Enter Top Momentum Stocks
Schedule: Every 14 days at 09:20 IST
FIXED: Use correct download_daily_data function
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
import pandas as pd
import numpy as np
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.market_data import download_daily_data, get_current_prices
from lib.telegram_notifier import send_message
from config.config import (
    MOMENTUM_STATE, MOMENTUM_UNIVERSE, MOMENTUM_MAX_POSITIONS,
    MOMENTUM_CAPITAL, MOMENTUM_LOOKBACK_DAYS, MOMENTUM_ATR_PERIOD,
    MOMENTUM_ATR_MULTIPLIER, MOMENTUM_REBALANCE_DAYS, STATE_DIR
)

log = setup_logger('momentum_rebalance')

def extract_scalar(value):
    """Extract scalar value from Series/DataFrame/scalar"""
    if isinstance(value, pd.Series):
        return float(value.iloc[0]) if len(value) > 0 else float(value)
    elif isinstance(value, pd.DataFrame):
        return float(value.iloc[0, 0]) if not value.empty else 0.0
    else:
        return float(value)


def calculate_momentum_scores():
    """Calculate 14-day momentum for all stocks"""
    log.info(f"Calculating momentum for {len(MOMENTUM_UNIVERSE)} stocks...")
    
    stock_data = download_daily_data(
        symbols=MOMENTUM_UNIVERSE,
        period='3mo'
    )
    
    if not stock_data:
        log.error("Failed to download any stock data")
        return {}
    
    scores = {}
    
    for symbol, df in stock_data.items():
        try:
            if df.empty or len(df) < MOMENTUM_LOOKBACK_DAYS + 5:
                log.warning(f"{symbol}: Insufficient data")
                continue
            
            close = df['Close'].iloc[-1]
            close_14d_ago = df['Close'].iloc[-(MOMENTUM_LOOKBACK_DAYS + 1)]
            
            momentum = ((close - close_14d_ago) / close_14d_ago) * 100
            
            high = df['High']
            low = df['Low']
            close_series = df['Close']
            
            tr1 = high - low
            tr2 = abs(high - close_series.shift(1))
            tr3 = abs(low - close_series.shift(1))
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.tail(MOMENTUM_ATR_PERIOD).mean()
            
            scores[symbol] = {
                'momentum': momentum,
                'current_price': close,
                'atr': atr
            }
            
            log.info(f"{symbol}: Momentum={momentum:.2f}%, Price=₹{close:.2f}, ATR=₹{atr:.2f}")
        
        except Exception as e:
            log.error(f"{symbol}: Error - {e}")
            continue
    
    return scores


def select_top_stocks(scores):
    """Select top N stocks by momentum"""
    if not scores:
        log.error("No valid momentum scores calculated")
        return []
    
    sorted_stocks = sorted(scores.items(), key=lambda x: x[1]['momentum'], reverse=True)
    
    top_stocks = sorted_stocks[:MOMENTUM_MAX_POSITIONS]
    
    log.info(f"Selected top {len(top_stocks)} stocks:")
    for symbol, data in top_stocks:
        log.info(f"  {symbol}: {data['momentum']:.2f}% momentum")
    
    return top_stocks


def calculate_position_sizes(top_stocks):
    """Calculate equal-weight position sizes"""
    if not top_stocks:
        return {}
    
    capital_per_stock = MOMENTUM_CAPITAL / len(top_stocks)
    
    positions = {}
    
    for symbol, data in top_stocks:
        current_price = data['current_price']
        atr = data['atr']
        
        quantity = int(capital_per_stock / current_price)
        
        if quantity == 0:
            log.warning(f"{symbol}: Price too high for position (₹{current_price:.2f})")
            continue
        
        stop_loss = current_price - (MOMENTUM_ATR_MULTIPLIER * atr)
        
        positions[symbol] = {
            'entry_price': current_price,
            'quantity': quantity,
            'invested': quantity * current_price,
            'stop_loss': stop_loss,
            'atr': atr,
            'highest_price': current_price,
            'entry_date': date.today().isoformat(),
            'momentum_score': data['momentum']
        }
        
        log.info(f"{symbol}: {quantity} shares @ ₹{current_price:.2f}, Stop: ₹{stop_loss:.2f}")
    
    return positions


def close_existing_positions(state_manager):
    """Close all existing positions before rebalancing"""
    state = state_manager.load()
    old_positions = state.get('positions', {})
    
    if not old_positions:
        log.info("No existing positions to close")
        return
    
    log.info(f"Closing {len(old_positions)} existing positions...")
    
    symbols = list(old_positions.keys())
    prices = get_current_prices(symbols)
    
    total_pnl = 0
    closed_summary = []
    
    for symbol, pos in old_positions.items():
        current_price = prices.get(symbol)
        if not current_price:
            log.warning(f"{symbol}: Could not get current price")
            continue
        
        entry = pos['entry_price']
        quantity = pos['quantity']
        
        pnl = (current_price - entry) * quantity
        pnl_pct = ((current_price - entry) / entry) * 100
        
        total_pnl += pnl
        
        closed_summary.append(f"{symbol}: {pnl_pct:+.2f}% (₹{pnl:+,.0f})")
        log.info(f"Closed {symbol}: Entry ₹{entry:.2f} → Exit ₹{current_price:.2f}, PnL: ₹{pnl:+,.0f}")
    
    if closed_summary:
        msg = f"📊 <b>MOMENTUM REBALANCE</b>\n\n"
        msg += f"<b>Closed Positions ({len(closed_summary)}):</b>\n"
        msg += "\n".join(closed_summary[:10])
        if len(closed_summary) > 10:
            msg += f"\n... and {len(closed_summary) - 10} more"
        msg += f"\n\n<b>Total PnL:</b> ₹{total_pnl:+,.0f}"
        send_message(msg)


def enter_new_positions(positions, state_manager):
    """Enter new momentum positions"""
    if not positions:
        log.warning("No new positions to enter")
        send_message("⚠️ Momentum rebalance: No valid positions found")
        return
    
    log.info(f"Entering {len(positions)} new positions...")
    
    entry_summary = []
    total_invested = 0
    
    for symbol, pos in positions.items():
        entry_summary.append(
            f"{symbol}: {pos['quantity']} @ ₹{pos['entry_price']:.2f}\n"
            f"  Stop: ₹{pos['stop_loss']:.2f} | Score: {pos['momentum_score']:.1f}%"
        )
        total_invested += pos['invested']
    
    state = state_manager.load()
    state['positions'] = positions
    state['days_since_rebalance'] = 0
    state['last_rebalance'] = date.today().isoformat()
    state_manager.save(state)
    
    msg = f"🚀 <b>NEW MOMENTUM POSITIONS</b>\n\n"
    msg += "\n\n".join(entry_summary[:6])
    msg += f"\n\n<b>Total Invested:</b> ₹{total_invested:,.0f}"
    send_message(msg)
    
    log.info(f"Successfully entered {len(positions)} positions")


def should_rebalance(state_manager):
    """Check if it's time to rebalance"""
    state = state_manager.load()
    
    days_since = state.get('days_since_rebalance', MOMENTUM_REBALANCE_DAYS)
    
    if days_since >= MOMENTUM_REBALANCE_DAYS:
        log.info(f"Rebalancing due: {days_since} days since last rebalance")
        return True
    
    if not state.get('positions'):
        log.info("Initial run: No positions exist, will create them")
        return True
    
    log.info(f"Rebalancing not due: {days_since}/{MOMENTUM_REBALANCE_DAYS} days")
    return False


def main():
    """Main rebalance function"""
    log.info("="*70)
    log.info("MOMENTUM REBALANCE - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        state_manager = StateManager(STATE_DIR / f'{MOMENTUM_STATE}.json')
        
        if not should_rebalance(state_manager):
            log.info("Rebalance not required today")
            return 0
        
        close_existing_positions(state_manager)
        
        scores = calculate_momentum_scores()
        
        top_stocks = select_top_stocks(scores)
        
        positions = calculate_position_sizes(top_stocks)
        
        enter_new_positions(positions, state_manager)
        
        log.info("✅ Momentum rebalance complete")
        return 0
    
    except Exception as e:
        log.error(f"💥 Fatal error: {e}", exc_info=True)
        send_message(f"❌ Momentum rebalance failed: {e}")
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
