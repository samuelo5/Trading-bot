"""Advanced strategy suite for a stronger signal engine.

This file adds more sophisticated signal logic while remaining compatible with the
existing StrategyManager design.
"""

from __future__ import annotations

import logging
from typing import Dict

import pandas as pd

from config import Config
from strategies.base_strategy import BaseStrategy


class TrendMomentumStrategy(BaseStrategy):
    """Trend-following strategy using EMA and ADX-like strength detection."""

    def __init__(self, config: Config, fast_period: int = 12, slow_period: int = 26):
        super().__init__("trend_momentum", config)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.logger = logging.getLogger(__name__)

    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        if not self.validate_data(df):
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        signal_df = df.copy()
        signal_df["ema_fast"] = signal_df["close"].ewm(span=self.fast_period, adjust=False).mean()
        signal_df["ema_slow"] = signal_df["close"].ewm(span=self.slow_period, adjust=False).mean()

        if len(signal_df) < self.slow_period:
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        current_fast = float(signal_df["ema_fast"].iloc[-1])
        current_slow = float(signal_df["ema_slow"].iloc[-1])
        prev_fast = float(signal_df["ema_fast"].iloc[-2])
        prev_slow = float(signal_df["ema_slow"].iloc[-2])

        if current_fast > current_slow and prev_fast <= prev_slow:
            return {"action": "BUY", "strength": min(abs((current_fast - current_slow) / max(current_slow, 1e-9)), 1.0), "parameters": {"ema_fast": current_fast, "ema_slow": current_slow}}
        if current_fast < current_slow and prev_fast >= prev_slow:
            return {"action": "SELL", "strength": min(abs((current_slow - current_fast) / max(current_slow, 1e-9)), 1.0), "parameters": {"ema_fast": current_fast, "ema_slow": current_slow}}
        return {"action": "HOLD", "strength": 0.0, "parameters": {"ema_fast": current_fast, "ema_slow": current_slow}}


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion logic using Bollinger-like price spread."""

    def __init__(self, config: Config, window: int = 20, zscore_limit: float = 2.0):
        super().__init__("mean_reversion", config)
        self.window = window
        self.zscore_limit = zscore_limit

    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        if not self.validate_data(df):
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        if len(df) < self.window:
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        close = df["close"].astype(float)
        rolling_mean = close.rolling(window=self.window).mean()
        rolling_std = close.rolling(window=self.window).std(ddof=0)
        current = float(close.iloc[-1])
        mean = float(rolling_mean.iloc[-1])
        std = float(rolling_std.iloc[-1])

        if std == 0:
            return {"action": "HOLD", "strength": 0.0, "parameters": {"mean": mean, "std": std}}

        zscore = (current - mean) / std
        if zscore < -self.zscore_limit:
            return {"action": "BUY", "strength": min(abs(zscore) / (self.zscore_limit + 1.0), 1.0), "parameters": {"zscore": zscore}}
        if zscore > self.zscore_limit:
            return {"action": "SELL", "strength": min(abs(zscore) / (self.zscore_limit + 1.0), 1.0), "parameters": {"zscore": zscore}}
        return {"action": "HOLD", "strength": 0.0, "parameters": {"zscore": zscore}}


class VolatilityBreakoutStrategy(BaseStrategy):
    """Breakout strategy triggered by latest candle momentum versus volatility."""

    def __init__(self, config: Config, lookback: int = 20):
        super().__init__("volatility_breakout", config)
        self.lookback = lookback

    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        if not self.validate_data(df):
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        if len(df) < self.lookback:
            return {"action": "HOLD", "strength": 0.0, "parameters": {}}

        recent = df.tail(self.lookback).copy()
        typical_range = (recent["high"] - recent["low"]).mean()
        last_close = float(recent["close"].iloc[-1])
        prev_close = float(recent["close"].iloc[-2])

        if typical_range == 0:
            return {"action": "HOLD", "strength": 0.0, "parameters": {"typical_range": 0.0}}

        move = (last_close - prev_close) / max(typical_range, 1e-9)
        if move > 1.0:
            return {"action": "BUY", "strength": min(abs(move) / 3.0, 1.0), "parameters": {"move": move, "typical_range": float(typical_range)}}
        if move < -1.0:
            return {"action": "SELL", "strength": min(abs(move) / 3.0, 1.0), "parameters": {"move": move, "typical_range": float(typical_range)}}
        return {"action": "HOLD", "strength": 0.0, "parameters": {"move": float(move), "typical_range": float(typical_range)}}
