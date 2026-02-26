"""
RISK MANAGER LIBRARY
Position sizing and R:R calculation
"""
import math
from lib.logger import setup_logger

log = setup_logger(__name__)


class RiskManager:
    """Position sizing and risk management"""
    
    # Constants
    BASE_RISK_PCT = 0.01
    MAX_RISK_PCT = 0.015
    MIN_RISK_PCT = 0.005
    MAX_POSITION_PCT = 0.15
    
    RR_HIGH_CONVICTION = 3.0  # win_prob >= 0.95
    RR_BASE = 2.0             # win_prob >= 0.85
    CONVICTION_MIN = 0.85
    CONVICTION_HIGH = 0.95
    
    def get_rr_ratio(self, win_probability: float) -> float:
        """Get R:R ratio based on conviction"""
        if win_probability >= self.CONVICTION_HIGH:
            return self.RR_HIGH_CONVICTION
        return self.RR_BASE
    
    def passes_conviction(self, win_probability: float) -> bool:
        """Check if signal meets conviction threshold"""
        return win_probability >= self.CONVICTION_MIN
    
    def get_risk_pct(self, drawdown_pct: float) -> float:
        """Dynamic risk scaling based on drawdown"""
        if drawdown_pct >= 10.0:
            return self.MIN_RISK_PCT
        elif drawdown_pct >= 5.0:
            return max(self.MIN_RISK_PCT, self.BASE_RISK_PCT * 0.5)
        else:
            return self.BASE_RISK_PCT
    
    def size_trade(
        self,
        free_capital: float,
        total_capital: float,
        entry_price: float,
        stop_loss: float,
        win_probability: float,
        direction: str = 'LONG',
        drawdown_pct: float = 0.0,
        strategy_name: str = 'unknown'
    ):
        """
        Calculate full trade parameters
        
        Returns dict or None if trade should be skipped
        """
        # Check conviction
        if not self.passes_conviction(win_probability):
            log.debug(f"[{strategy_name}] Skipped - low conviction {win_probability:.2%}")
            return None
        
        # Stop distance
        if direction == 'LONG':
            stop_dist = entry_price - stop_loss
        else:
            stop_dist = stop_loss - entry_price
        
        if stop_dist <= 0:
            log.warning(f"[{strategy_name}] Invalid stop distance")
            return None
        
        stop_pct = stop_dist / entry_price
        if stop_pct > 0.15:
            log.warning(f"[{strategy_name}] Stop too wide ({stop_pct:.1%})")
            return None
        
        # Position size
        risk_pct = self.get_risk_pct(drawdown_pct)
        risk_amount = free_capital * risk_pct
        shares = math.floor(risk_amount / stop_dist)
        
        if shares < 1:
            log.debug(f"[{strategy_name}] Position too small")
            return None
        
        cost_basis = shares * entry_price
        
        # Cap at max position size
        max_cost = total_capital * self.MAX_POSITION_PCT
        if cost_basis > max_cost:
            shares = math.floor(max_cost / entry_price)
            cost_basis = shares * entry_price
        
        if cost_basis > free_capital:
            log.warning(f"[{strategy_name}] Insufficient capital")
            return None
        
        # Target via R:R
        rr_ratio = self.get_rr_ratio(win_probability)
        reward = stop_dist * rr_ratio
        
        if direction == 'LONG':
            target_price = entry_price + reward
        else:
            target_price = entry_price - reward
        
        return {
            'shares': shares,
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target_price': round(target_price, 2),
            'rr_ratio': rr_ratio,
            'risk_pct': risk_pct,
            'risk_amount': round(risk_amount, 2),
            'cost_basis': round(cost_basis, 2),
            'win_probability': round(win_probability, 4),
            'direction': direction,
            'strategy': strategy_name
        }
