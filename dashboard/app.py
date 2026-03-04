"""
TRADING SYSTEM DASHBOARD
Read-only state visualization
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import os

# Health check endpoint for Render
if __name__ == "__main__":
    # Check if running as health check
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "health":
        print("OK")
        os.sys.exit(0)

# Your existing dashboard code continues below...

st.set_page_config(page_title="Trading System", layout="wide")

# Paths
BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "storage" / "state"

def load_state(filename):
    """Load JSON state file"""
    filepath = STATE_DIR / filename
    try:
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
    return {}

# Load states
daytrade_state = load_state("daytrade_state.json")
momentum_state = load_state("momentum_state.json")
portfolio_state = load_state("portfolio.json")

# Title
st.title("📊 Trading System Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Day Trade", "🔄 Momentum", "💰 Portfolio"])

# ─── DAY TRADE TAB ───────────────────────────────────────────────────────────
with tab1:
    st.header("Day Trade Strategy")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        model_trained = daytrade_state.get('model_trained', False)
        st.metric("Model Status", 
                 "✅ Trained" if model_trained else "❌ Not Trained")
    
    with col2:
        signals = len(daytrade_state.get('daily_signals', []))
        st.metric("Signals Today", signals)
    
    with col3:
        positions = len(daytrade_state.get('positions', {}))
        st.metric("Open Positions", positions)
    
    with col4:
        daily_pnl = daytrade_state.get('daily_pnl', 0)
        st.metric("Daily PnL", f"₹{daily_pnl:,.0f}", 
                 delta=f"{daily_pnl:+,.0f}")
    
    # Capital
    st.subheader("Capital Status")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nav = daytrade_state.get('current_nav', 1_000_000)
        st.metric("NAV", f"₹{nav:,.0f}")
    
    with col2:
        used = daytrade_state.get('used_capital', 0)
        st.metric("Used Capital", f"₹{used:,.0f}")
    
    with col3:
        free = daytrade_state.get('free_capital', 1_000_000)
        st.metric("Free Capital", f"₹{free:,.0f}")
    
    with col4:
        realized_pnl = daytrade_state.get('realized_pnl', 0)
        total_return = (realized_pnl / 1_000_000 * 100) if realized_pnl else 0
        st.metric("Total Return", f"{total_return:+.2f}%", 
                 delta=f"₹{realized_pnl:+,.0f}")
    
    # Open Positions
    if daytrade_state.get('positions'):
        st.subheader("Open Positions")
        positions_data = []
        for symbol, pos in daytrade_state['positions'].items():
            positions_data.append({
                'Symbol': symbol,
                'Direction': pos.get('direction'),
                'Entry': f"₹{pos.get('entry_price', 0):.2f}",
                'Stop': f"₹{pos.get('stop_loss', 0):.2f}",
                'Target': f"₹{pos.get('target_price', 0):.2f}",
                'Shares': pos.get('shares', 0),
                'Cost': f"₹{pos.get('cost_basis', 0):,.0f}",
                'R:R': f"{pos.get('rr_ratio', 0):.1f}:1",
                'Win Prob': f"{pos.get('win_prob', 0):.1%}"
            })
        st.dataframe(pd.DataFrame(positions_data), use_container_width=True)
    
    # Trade History
    if daytrade_state.get('trade_logs'):
        st.subheader("Recent Trades")
        trades = daytrade_state['trade_logs'][-20:]  # Last 20
        trades_data = []
        for trade in trades:
            trades_data.append({
                'Date': trade.get('entry_date'),
                'Symbol': trade.get('symbol'),
                'Direction': trade.get('direction'),
                'Entry': f"₹{trade.get('entry_price', 0):.2f}",
                'Exit': f"₹{trade.get('exit_price', 0):.2f}",
                'PnL': f"₹{trade.get('pnl', 0):+,.0f}",
                'PnL %': f"{trade.get('pnl_pct', 0):+.2f}%"
            })
        st.dataframe(pd.DataFrame(trades_data), use_container_width=True)
    
    # Stats
    st.subheader("Performance Stats")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        win_count = daytrade_state.get('win_count', 0)
        loss_count = daytrade_state.get('loss_count', 0)
        total_trades = win_count + loss_count
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%", 
                 delta=f"{win_count}W / {loss_count}L")
    
    with col2:
        st.metric("Total Trades", total_trades)
    
    with col3:
        last_train = daytrade_state.get('last_train_date', 'Never')
        st.metric("Last Model Train", last_train)

# ─── MOMENTUM TAB ────────────────────────────────────────────────────────────
with tab2:
    st.header("Momentum Strategy")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        positions = len(momentum_state.get('positions', {}))
        st.metric("Open Positions", positions)
    
    with col2:
        days_since = momentum_state.get('days_since_rebalance', 0)
        days_until = max(0, 14 - days_since)
        st.metric("Days to Rebalance", days_until)
    
    with col3:
        last_rebalance = momentum_state.get('last_rebalance_date', 'Never')
        st.metric("Last Rebalance", last_rebalance)
    
    with col4:
        nav = momentum_state.get('current_nav', 1_000_000)
        st.metric("NAV", f"₹{nav:,.0f}")
    
    # Positions
    if momentum_state.get('positions'):
        st.subheader("Open Positions")
        positions_data = []
        for symbol, pos in momentum_state['positions'].items():
            positions_data.append({
                'Symbol': symbol,
                'Entry': f"₹{pos.get('entry_price', 0):.2f}",
                'Current': f"₹{pos.get('live_price', pos.get('entry_price', 0)):.2f}",
                'Stop': f"₹{pos.get('stop_loss', 0):.2f}",
                'Target': f"₹{pos.get('target_price', 0):.2f}",
                'Shares': pos.get('shares', 0),
                'R:R': f"{pos.get('rr_ratio', 0):.1f}:1" if pos.get('rr_ratio') else "—",
                'Entry Date': pos.get('entry_date', '')
            })
        st.dataframe(pd.DataFrame(positions_data), use_container_width=True)

# ─── PORTFOLIO TAB ───────────────────────────────────────────────────────────
with tab3:
    st.header("Portfolio Overview")
    
    total_capital = portfolio_state.get('total_capital', 2_000_000)
    momentum_cap = momentum_state.get('current_nav', 1_000_000)
    daytrade_cap = daytrade_state.get('current_nav', 1_000_000)
    total_nav = momentum_cap + daytrade_cap
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total NAV", f"₹{total_nav:,.0f}")
    
    with col2:
        st.metric("Momentum NAV", f"₹{momentum_cap:,.0f}")
    
    with col3:
        st.metric("Day Trade NAV", f"₹{daytrade_cap:,.0f}")
    
    # Strategy Allocation
    st.subheader("Capital Allocation")
    allocation_data = pd.DataFrame({
        'Strategy': ['Momentum', 'Day Trade'],
        'Capital': [momentum_cap, daytrade_cap]
    })
    st.bar_chart(allocation_data.set_index('Strategy'))

# Auto-refresh
st.button("🔄 Refresh", type="primary")
