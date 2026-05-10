"""
Base Strategy and Strategy Manager for Trading Signals
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from config import Config


class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        """
        Calculate trading signal based on strategy
        Returns: {"action": "BUY"/"SELL"/"HOLD", "strength": 0-1, "parameters": {}}
        """
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate that DataFrame has required columns"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in df.columns for col in required_columns)


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Moving Average Crossover Strategy"""
    
    def __init__(self, config: Config, fast_period: int = 10, slow_period: int = 20):
        super().__init__("moving_average_crossover", config)
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        """Calculate crossover signal"""
        if not self.validate_data(df):
            return {"action": "HOLD", "strength": 0, "parameters": {}}
        
        # Calculate moving averages
        df['fast_ma'] = df['close'].rolling(window=self.fast_period).mean()
        df['slow_ma'] = df['close'].rolling(window=self.slow_period).mean()
        
        if len(df) < 2:
            return {"action": "HOLD", "strength": 0, "parameters": {}}
        
        current_fast = df['fast_ma'].iloc[-1]
        current_slow = df['slow_ma'].iloc[-1]
        prev_fast = df['fast_ma'].iloc[-2]
        prev_slow = df['slow_ma'].iloc[-2]
        
        # Check for crossover
        if pd.isna(current_fast) or pd.isna(current_slow):
            return {"action": "HOLD", "strength": 0, "parameters": {}}
        
        result = {"action": "HOLD", "strength": 0, "parameters": {}}
        
        # Golden cross (bullish)
        if prev_fast <= prev_slow and current_fast > current_slow:
            result["action"] = "BUY"
            result["strength"] = min((current_fast - current_slow) / current_slow, 1.0)
        
        # Death cross (bearish)
        elif prev_fast >= prev_slow and current_fast < current_slow:
            result["action"] = "SELL"
            result["strength"] = min((current_slow - current_fast) / current_slow, 1.0)
        
        result["parameters"] = {
            "fast_ma": float(current_fast) if not pd.isna(current_fast) else 0,
            "slow_ma": float(current_slow) if not pd.isna(current_slow) else 0
        }
        
        return result


class RSIStrategy(BaseStrategy):
    """Relative Strength Index Strategy"""
    
    def __init__(self, config: Config, period: int = 14, overbought: float = 70, oversold: float = 30):
        super().__init__("rsi_strategy", config)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        """Calculate RSI signal"""
        if not self.validate_data(df):
            return {"action": "HOLD", "strength": 0, "parameters": {}}
        
        rsi = self._calculate_rsi(df['close'], self.period)
        
        if len(rsi) == 0 or pd.isna(rsi.iloc[-1]):
            return {"action": "HOLD", "strength": 0, "parameters": {}}
        
        current_rsi = rsi.iloc[-1]
        result = {"action": "HOLD", "strength": 0, "parameters": {"rsi": float(current_rsi)}}
        
        # Oversold - potential BUY
        if current_rsi < self.oversold:
            result["action"] = "BUY"
            result["strength"] = min((self.oversold - current_rsi) / self.oversold, 1.0)
        
        # Overbought - potential SELL
        elif current_rsi > self.overbought:
            result["action"] = "SELL"
            result["strength"] = min((current_rsi - self.overbought) / (100 - self.overbought), 1.0)
        
        return result
    
    def _calculate_rsi(self, closes: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class StrategyManager:
    """Manage multiple trading strategies"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.strategies: Dict[str, BaseStrategy] = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize configured strategies"""
        enabled = self.config.get('strategy.enabled_strategies', [])
        
        if "moving_average_crossover" in enabled:
            self.strategies["moving_average_crossover"] = MovingAverageCrossoverStrategy(self.config)
            self.logger.info("Moving Average Crossover strategy loaded")
        
        if "rsi_strategy" in enabled:
            self.strategies["rsi_strategy"] = RSIStrategy(self.config)
            self.logger.info("RSI strategy loaded")
            
        if "llama_strategy" in enabled:
            try:
                from strategies.llama_strategy import LlamaStrategy
                self.strategies["llama_strategy"] = LlamaStrategy(self.config)
                self.logger.info("Llama strategy loaded")
            except Exception as e:
                self.logger.error(f"Failed to load Llama strategy: {e}")
    
    def get_signals(self, symbol: str, df: pd.DataFrame) -> Dict[str, Dict]:
        """Get signals from all active strategies"""
        signals = {}
        
        for strategy_name, strategy in self.strategies.items():
            try:
                signal = strategy.calculate_signal(df)
                signals[strategy_name] = signal
            except Exception as e:
                self.logger.error(f"Error in {strategy_name}: {str(e)}")
                signals[strategy_name] = {"action": "HOLD", "strength": 0, "error": str(e)}
        
        return signals
    
    def get_consensus_signal(self, symbol: str, df: pd.DataFrame) -> Dict:
        """Get consensus signal from all strategies"""
        signals = self.get_signals(symbol, df)
        
        if not signals:
            return {"action": "HOLD", "strength": 0, "consensus": 0}
        
        buy_strength = sum(s["strength"] for s in signals.values() if s["action"] == "BUY")
        sell_strength = sum(s["strength"] for s in signals.values() if s["action"] == "SELL")
        total_strength = buy_strength + sell_strength
        
        if total_strength == 0:
            return {"action": "HOLD", "strength": 0, "consensus": 0}
        
        buy_consensus = buy_strength / total_strength
        
        if buy_consensus > 0.6:
            action = "BUY"
        elif buy_consensus < 0.4:
            action = "SELL"
        else:
            action = "HOLD"
        
        return {
            "action": action,
            "strength": max(buy_strength, sell_strength) / len(signals),
            "consensus": buy_consensus,
            "individual_signals": signals
        }
