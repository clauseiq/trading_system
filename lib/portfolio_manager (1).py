"""
PORTFOLIO MANAGER LIBRARY
Capital and position management
"""
from lib.state_manager import StateManager
from lib.logger import setup_logger

log = setup_logger(__name__)


class PortfolioManager:
    """Portfolio state management"""
    
    def __init__(self, filepath):
        self.state_mgr = StateManager(filepath)
    
    def get_capital(self):
        """Get current capital status"""
        state = self.state_mgr.load()
        return {
            'total': state.get('total_capital', 1_000_000),
            'free': state.get('free_capital', 1_000_000),
            'used': state.get('used_capital', 0),
            'nav': state.get('current_nav', 1_000_000),
            'peak': state.get('peak_equity', 1_000_000)
        }
    
    def allocate(self, amount: float):
        """Reserve capital"""
        state = self.state_mgr.load()
        free = state.get('free_capital', 1_000_000)
        
        if amount > free:
            raise ValueError(f"Insufficient capital: need ₹{amount:,.0f}, have ₹{free:,.0f}")
        
        state['used_capital'] = state.get('used_capital', 0) + amount
        state['free_capital'] = free - amount
        self.state_mgr.save(state)
    
    def release(self, cost_basis: float, pnl: float = 0):
        """Release capital with PnL"""
        state = self.state_mgr.load()
        
        returned = cost_basis + pnl
        state['used_capital'] = max(0, state.get('used_capital', 0) - cost_basis)
        state['free_capital'] = state.get('free_capital', 0) + returned
        state['realized_pnl'] = state.get('realized_pnl', 0) + pnl
        
        # Update NAV
        total = state.get('total_capital', 1_000_000)
        nav = total + state['realized_pnl']
        state['current_nav'] = nav
        state['peak_equity'] = max(state.get('peak_equity', total), nav)
        
        self.state_mgr.save(state)
