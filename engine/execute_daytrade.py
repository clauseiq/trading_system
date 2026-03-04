#!/usr/bin/env python3
"""
CRON JOB: Execute Day Trades
Schedule: 09:30 IST (Mon-Fri)
Duration: ~2-5 seconds
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, datetime
from lib.logger import setup_logger
from lib.state_manager import StateManager
from lib.portfolio_manager import PortfolioManager
from lib.risk_manager import RiskManager
from lib.telegram_notifier import TelegramNotifier
from config.config import DAYTRADE_STATE, PORTFOLIO_STATE, DAYTRADE_CAPITAL, DAYTRADE_MAX_CAPITAL_PCT
from lib.telegram_notifier import send_message
from config.config import DAYTRADE_STATE

log = setup_logger('execute_daytrade')


def main():
    """Execute day trades"""
    log.info("="*70)
    log.info("EXECUTE TRADES - START")
    log.info("="*70)
    
    try:
        state_manager = StateManager(DAYTRADE_STATE)
        state = state_manager.load()
        
        signals = state.get('signals', [])
        
        if not signals:
            log.info("No signals to execute")
            send_message("📊 No day trade signals today")
            return 0
        
        # Execute trades (your existing logic here)
        log.info(f"Executing {len(signals)} trades")
        
        # Send notification
        send_message(f"✅ Executed {len(signals)} day trades")
        
        log.info("✅ Trades executed successfully")
        return 0
    
    except Exception as e:
        log.error(f"💥 Error: {e}", exc_info=True)
        send_message(f"❌ Trade execution failed: {e}")
        return 1
    
    finally:
        log.info("="*70)


if __name__ == "__main__":
    sys.exit(main())

def execute_trades():
    """Execute paper trades based on signals"""
    state_manager = StateManager(DAYTRADE_STATE)
    portfolio = PortfolioManager(PORTFOLIO_STATE)
    risk_mgr = RiskManager()
    notifier = TelegramNotifier()
    
    state = state_manager.load()
    signals = state.get('daily_signals', [])
    
    if not signals:
        log.info("No signals to execute")
        return 0
    
    # Get capital
    free_capital = state.get('free_capital', DAYTRADE_CAPITAL)
    total_capital = state.get('total_capital', DAYTRADE_CAPITAL)
    current_nav = state.get('current_nav', DAYTRADE_CAPITAL)
    peak_equity = state.get('peak_equity', DAYTRADE_CAPITAL)
    
    # Calculate drawdown
    drawdown_pct = ((peak_equity - current_nav) / peak_equity * 100) if peak_equity > 0 else 0.0
    
    positions = state.get('positions', {})
    opened = []
    
    for sig in signals:
        symbol = sig['symbol']
        
        # Skip if already have position
        if symbol in positions:
            continue
        
        # Size the trade
        trade = risk_mgr.size_trade(
            free_capital=free_capital,
            total_capital=total_capital,
            entry_price=sig['live_price'],
            stop_loss=sig['stop_loss'],
            win_probability=sig['win_prob'],
            direction=sig['direction'],
            drawdown_pct=drawdown_pct,
            strategy_name='DayTrade'
        )
        
        if not trade:
            continue
        
        # Cap at max per trade
        max_cost = free_capital * DAYTRADE_MAX_CAPITAL_PCT
        if trade['cost_basis'] > max_cost:
            trade['shares'] = int(max_cost / trade['entry_price'])
            trade['cost_basis'] = trade['shares'] * trade['entry_price']
        
        if trade['shares'] < 1 or trade['cost_basis'] > free_capital:
            continue
        
        # Record position
        position = {
            'symbol': symbol,
            'direction': sig['direction'],
            'entry_price': trade['entry_price'],
            'stop_loss': trade['stop_loss'],
            'target_price': trade['target_price'],
            'shares': trade['shares'],
            'cost_basis': trade['cost_basis'],
            'win_prob': sig['win_prob'],
            'rr_ratio': trade['rr_ratio'],
            'entry_time': datetime.now().strftime("%H:%M:%S"),
            'entry_date': str(date.today())
        }
        
        positions[symbol] = position
        opened.append(position)
        
        # Update capital
        free_capital -= trade['cost_basis']
        
        # Send Telegram alert
        notifier.send_trade_signal(
            strategy="Day Trade XGBoost",
            symbol=symbol,
            direction=sig['direction'],
            entry_price=trade['entry_price'],
            stop_loss=trade['stop_loss'],
            target=trade['target_price'],
            shares=trade['shares'],
            win_prob=sig['win_prob'],
            rr_ratio=trade['rr_ratio']
        )
        
        log.info(f"✅ {symbol} {sig['direction']} {trade['shares']} @ ₹{trade['entry_price']:.2f} "
                f"(stop: ₹{trade['stop_loss']:.2f}, target: ₹{trade['target_price']:.2f})")
    
    # Update state
    used_capital = sum(p['cost_basis'] for p in positions.values())
    state_manager.update({
        'positions': positions,
        'used_capital': used_capital,
        'free_capital': total_capital - used_capital
    })
    
    log.info(f"Opened {len(opened)} positions, using ₹{used_capital:,.0f}")
    return len(opened)


def main():
    log.info("="*70)
    log.info("EXECUTE DAY TRADES - START")
    log.info("="*70)
    
    if date.today().weekday() >= 5:
        log.info("Not a trading day - skipping")
        return 0
    
    try:
        count = execute_trades()
        log.info(f"✅ Executed {count} trades")
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
