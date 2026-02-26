#!/usr/bin/env python3
"""
CRON JOB: Close Day Trade Positions
Schedule: 11:15 IST (Mon-Fri)
Duration: ~5-10 seconds
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.market_data import get_current_prices
from lib.telegram_notifier import TelegramNotifier
from config.config import DAYTRADE_STATE, DAYTRADE_COST_PCT

log = setup_logger('close_daytrade')


def close_positions():
    """Close all day trade positions and compute PnL"""
    state_manager = StateManager(DAYTRADE_STATE)
    notifier = TelegramNotifier()
    
    state = state_manager.load()
    
    positions = state.get('positions', {})
    
    if not positions:
        log.info("No open positions to close")
        return
    
    # Get current prices
    symbols = list(positions.keys())
    prices = get_current_prices(symbols)
    
    # Close each position
    trade_logs = state.get('trade_logs', [])
    total_pnl = 0
    wins = 0
    losses = 0
    
    for symbol, pos in positions.items():
        exit_price = prices.get(symbol)
        
        if not exit_price:
            log.warning(f"{symbol}: No exit price available, using entry")
            exit_price = pos['entry_price']
        
        # Calculate PnL
        if pos['direction'] == 'LONG':
            pnl_pct = (exit_price - pos['entry_price']) / pos['entry_price']
        else:  # SHORT
            pnl_pct = (pos['entry_price'] - exit_price) / pos['entry_price']
        
        # Subtract transaction costs
        pnl_pct -= DAYTRADE_COST_PCT
        
        pnl_rupees = pnl_pct * pos['cost_basis']
        total_pnl += pnl_rupees
        
        if pnl_rupees > 0:
            wins += 1
        else:
            losses += 1
        
        # Send Telegram notification
        notifier.send_trade_closed(
            symbol=symbol,
            direction=pos['direction'],
            entry_price=pos['entry_price'],
            exit_price=exit_price,
            pnl=pnl_rupees,
            pnl_pct=pnl_pct * 100
        )
        
        # Log trade
        trade_logs.append({
            'symbol': symbol,
            'direction': pos['direction'],
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'entry_date': pos['entry_date'],
            'entry_time': pos['entry_time'],
            'exit_time': '11:15:00',
            'shares': pos['shares'],
            'pnl': round(pnl_rupees, 2),
            'pnl_pct': round(pnl_pct * 100, 2),
            'strategy': 'DayTrade'
        })
        
        log.info(f"✅ {symbol} {pos['direction']} @ ₹{exit_price:.2f} → PnL: ₹{pnl_rupees:+,.0f} ({pnl_pct*100:+.2f}%)")
    
    # Update state
    total_capital = state.get('total_capital', 1_000_000)
    current_nav = total_capital + state.get('realized_pnl', 0) + total_pnl
    peak_equity = max(state.get('peak_equity', total_capital), current_nav)
    
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    state_manager.update({
        'positions': {},
        'used_capital': 0,
        'free_capital': current_nav,
        'current_nav': current_nav,
        'peak_equity': peak_equity,
        'realized_pnl': state.get('realized_pnl', 0) + total_pnl,
        'daily_pnl': total_pnl,
        'daily_pnl_date': str(date.today()),
        'trade_logs': trade_logs[-200:],  # Keep last 200
        'win_count': state.get('win_count', 0) + wins,
        'loss_count': state.get('loss_count', 0) + losses
    })
    
    # Send daily summary
    notifier.send_daily_summary(
        daytrade_pnl=total_pnl,
        daytrade_trades=wins + losses,
        daytrade_win_rate=win_rate,
        momentum_positions=0,  # Will be updated separately
        total_nav=current_nav
    )
    
    log.info(f"Closed {len(positions)} positions, Total PnL: ₹{total_pnl:+,.0f} ({wins}W/{losses}L)")


def main():
    log.info("="*70)
    log.info("CLOSE DAY TRADE POSITIONS - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        close_positions()
        log.info("✅ Positions closed successfully")
        return 0
    
    except Exception as e:
        log.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())
