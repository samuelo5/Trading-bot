"""
Base Strategy and Strategy Manager for Trading Signals
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd

from config import Config


class BaseStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        """Return a signal dict with BUY/SELL/HOLD and confidence."""

    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate the DataFrame contains the required OHLCV columns."""
        required_columns = ["open", "high", "low", "close", "volume"]
        if not isinstance(df, pd.DataFrame):
            return False
        return all(col in df.columns for col in required_columns)


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Moving Average Crossover Strategy."""

    def __init__(self, config: Config, fast_period: int = 10, slow_period: int = 20):
        super().__init__("moving_average_crossover", config)
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        """Calculate a crossover signal."""
        if not self.validate_data(df):
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        signal_df = df.copy()
        signal_df["fast_ma"] = signal_df["close"].rolling(window=self.fast_period).mean()
        signal_df["slow_ma"] = signal_df["close"].rolling(window=self.slow_period).mean()

        if len(signal_df) < 2:
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        current_fast = signal_df["fast_ma"].iloc[-1]
        current_slow = signal_df["slow_ma"].iloc[-1]
        prev_fast = signal_df["fast_ma"].iloc[-2]
        prev_slow = signal_df["slow_ma"].iloc[-2]

        if pd.isna(current_fast) or pd.isna(current_slow) or pd.isna(prev_fast) or pd.isna(prev_slow):
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        result = {"action": "HOLD", "strength": 0.0, "parameters": {}}

        if prev_fast <= prev_slow and current_fast > current_slow:
            result["action"] = "BUY"
            result["strength"] = min(float((current_fast - current_slow) / max(current_slow, 1e-9)), 1.0)
        elif prev_fast >= prev_slow and current_fast < current_slow:
            result["action"] = "SELL"
            result["strength"] = min(float((current_slow - current_fast) / max(current_slow, 1e-9)), 1.0)

        result["parameters"] = {
            "fast_ma": float(current_fast),
            "slow_ma": float(current_slow),
        }

        return result


class RSIStrategy(BaseStrategy):
    """Relative Strength Index Strategy."""

    def __init__(self, config: Config, period: int = 14, overbought: float = 70, oversold: float = 30):
        super().__init__("rsi_strategy", config)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        """Calculate an RSI signal."""
        if not self.validate_data(df):
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        rsi = self._calculate_rsi(df["close"], self.period)
        if len(rsi) == 0 or pd.isna(rsi.iloc[-1]):
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        current_rsi = float(rsi.iloc[-1])
        result = {"action": "HOLD", "strength": 0.0, "parameters": {"rsi": current_rsi}}

        if current_rsi < self.oversold:
            result["action"] = "BUY"
            result["strength"] = min((self.oversold - current_rsi) / max(self.oversold, 1e-9), 1.0)
        elif current_rsi > self.overbought:
            result["action"] = "SELL"
            result["strength"] = min((current_rsi - self.overbought) / max(100 - self.overbought, 1e-9), 1.0)

        return result

    def _calculate_rsi(self, closes: pd.Series, period: int = 14) -> pd.Series:
        """Calculate the RSI indicator."""
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, 1e-9)
        return 100 - (100 / (1 + rs))


class StrategyManager:
    """Manage multiple trading strategies."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.strategies: Dict[str, BaseStrategy] = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        """Initialize configured strategies."""
        enabled = self.config.get("strategy.enabled_strategies", [])

        if "moving_average_crossover" in enabled:
            self.strategies["moving_average_crossover"] = MovingAverageCrossoverStrategy(self.config)
            self.logger.info("Moving Average Crossover strategy loaded")

        if "rsi_strategy" in enabled:
            self.strategies["rsi_strategy"] = RSIStrategy(self.config)
            self.logger.info("RSI strategy loaded")

        if "trend_momentum" in enabled:
            from strategies.advanced_strategy import TrendMomentumStrategy
            self.strategies["trend_momentum"] = TrendMomentumStrategy(self.config)
            self.logger.info("Trend Momentum strategy loaded")

        if "mean_reversion" in enabled:
            from strategies.advanced_strategy import MeanReversionStrategy
            self.strategies["mean_reversion"] = MeanReversionStrategy(self.config)
            self.logger.info("Mean Reversion strategy loaded")

        if "volatility_breakout" in enabled:
            from strategies.advanced_strategy import VolatilityBreakoutStrategy
            self.strategies["volatility_breakout"] = VolatilityBreakoutStrategy(self.config)
            self.logger.info("Volatility Breakout strategy loaded")

        if "llama_strategy" in enabled:
            try:
                from strategies.llama_strategy import LlamaStrategy
                self.strategies["llama_strategy"] = LlamaStrategy(self.config)
                self.logger.info("Llama strategy loaded")
            except Exception as exc:
                self.logger.error("Failed to load Llama strategy: %s", exc)

        if "strategy_manager" in enabled:
            self.logger.info("Strategy manager ready")

    def get_signals(self, symbol: str, df: pd.DataFrame) -> Dict[str, Dict]:
        """Get signals from all active strategies."""
        signals = {}

        for strategy_name, strategy in self.strategies.items():
            try:
                signal = strategy.calculate_signal(df)
                signals[strategy_name] = signal
            except Exception as exc:
                self.logger.error("Error in %s: %s", strategy_name, exc)
                signals[strategy_name] = {"action": "HOLD", "strength": 0.0, "error": str(exc)}

        return signals

    def get_consensus_signal(self, symbol: str, df: pd.DataFrame) -> Dict:
        """Calculate a single consensus signal from all active strategies."""
        signals = self.get_signals(symbol, df)

        if not signals:
            return {"action": "HOLD", "strength": 0.0, "consensus": 0.0}

        buy_strength = sum(float(signal.get("strength", 0.0)) for signal in signals.values() if signal.get("action") == "BUY")
        sell_strength = sum(float(signal.get("strength", 0.0)) for signal in signals.values() if signal.get("action") == "SELL")
        total_strength = buy_strength + sell_strength

        if total_strength == 0:
            return {"action": "HOLD", "strength": 0.0, "consensus": 0.0, "individual_signals": signals}

        buy_consensus = buy_strength / total_strength

        if buy_consensus > 0.6:
            action = "BUY"
        elif buy_consensus < 0.4:
            action = "SELL"
        else:
            action = "HOLD"

        max_strength = max(buy_strength, sell_strength)
        return {
            "action": action,
            "strength": float(max_strength / max(len(signals), 1)),
            "consensus": float(buy_consensus),
            "individual_signals": signals,
        }

