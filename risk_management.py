"""
Risk Management Module - Handle position sizing and risk calculations
"""

import logging
from typing import Dict, Optional
import pandas as pd
from config import Config

# Risk management for trading bot, including position sizing and risk/reward calculations
class RiskManager:
    """Manage trading risks and position sizing"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self, account_balance: float, risk_amount: float, 
                               stop_loss_pips: float, pip_value: float) -> float:
        """
        Calculate position size based on risk management rules
        
        Args:
            account_balance: Total account balance
            risk_amount: Amount willing to risk per trade
            stop_loss_pips: Stop loss distance in pips
            pip_value: Value of one pip
        
        Returns:
            Position size in units
        """
        if stop_loss_pips == 0:
            return 0
        
        position_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Apply max position size limit
        max_position_value = account_balance * self.config.get('trading.max_position_size', 0.05)
        max_position_size = max_position_value / (100000 * pip_value)  # Assuming standard forex
        
        return min(position_size, max_position_size)
    
    def calculate_risk_reward_ratio(self, entry_price: float, stop_loss: float, 
                                   take_profit: float) -> Optional[float]:
        """Calculate risk/reward ratio"""
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return None
        
        return reward / risk
    
    def check_max_drawdown(self, account_balance: float, peak_balance: float) -> float:
        """
        Calculate current drawdown percentage
        
        Returns: Drawdown percentage (0-100)
        """
        if peak_balance == 0:
            return 0
        
        return ((peak_balance - account_balance) / peak_balance) * 100
    
    def is_within_risk_limits(self, current_drawdown: float, position_count: int) -> bool:
        """Check if trading is within risk limits"""
        max_drawdown = self.config.get('risk_management.max_drawdown_percent', 10.0)
        
        if current_drawdown > max_drawdown:
            self.logger.warning(f"Max drawdown exceeded: {current_drawdown:.2f}% > {max_drawdown}%")
            return False
        
        return True
    
    def validate_trade(self, symbol: str, entry_price: float, stop_loss: float, 
                      take_profit: float, position_size: float, account_balance: float) -> Dict:
        """
        Validate trade using multiple criteria
        
        Returns: {"valid": bool, "reasons": [str], "metrics": {}}
        """
        reasons = []
        metrics = {}
        
        # Check minimum pip distance
        min_pips = 5  # Minimum stop loss distance
        pips = abs(entry_price - stop_loss) * 10000  # For most forex pairs
        metrics['pips'] = pips
        
        if pips < min_pips:
            reasons.append(f"Stop loss too tight: {pips:.1f} pips < {min_pips} pips")
        
        # Check risk/reward ratio
        rr_ratio = self.calculate_risk_reward_ratio(entry_price, stop_loss, take_profit)
        metrics['rr_ratio'] = rr_ratio
        
        if rr_ratio and rr_ratio < 1.0:
            reasons.append(f"Poor risk/reward ratio: {rr_ratio:.2f} < 1.0")
        
        # Check position size
        position_value = entry_price * position_size
        max_position_value = account_balance * self.config.get('trading.max_position_size', 0.05)
        metrics['position_value'] = position_value
        metrics['max_position_value'] = max_position_value
        
        if position_value > max_position_value:
            reasons.append(f"Position too large: ${position_value:.2f} > ${max_position_value:.2f}")
        
        return {
            "valid": len(reasons) == 0,
            "reasons": reasons,
            "metrics": metrics
        }
    
    def get_risk_metrics(self, positions: Dict, account_balance: float) -> Dict:
        """Get current portfolio risk metrics"""
        metrics = {
            "total_position_count": len(positions),
            "total_exposure": 0,
            "longest_loss_streak": 0,
            "win_rate": 0
        }
        
        # Calculate total exposure
        for symbol, position in positions.items():
            metrics['total_exposure'] += position.entry_price * position.size
        
        exposure_percent = (metrics['total_exposure'] / account_balance) * 100 if account_balance > 0 else 0
        metrics['exposure_percent'] = exposure_percent
        
        return metrics
