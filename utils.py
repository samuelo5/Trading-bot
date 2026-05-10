"""
Utility functions for the Trading Bot
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency for display"""
    return f"{currency} {amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage for display"""
    return f"{value:.{decimals}f}%"


def get_trading_hours(timezone: str = "UTC") -> Dict[str, str]:
    """Get trading hours for different markets"""
    hours = {
        "forex": "24/5 (Monday-Friday)",
        "us_stocks": "09:30-16:00 EST",
        "uk_stocks": "08:00-16:30 GMT",
        "asia_stocks": "09:00-15:00 JST"
    }
    return hours


def is_trading_hours(market: str = "forex") -> bool:
    """Check if market is currently open"""
    now = datetime.now()
    
    if market == "forex":
        # Forex is open 24/5
        return now.weekday() < 4  # Monday to Friday
    
    return True


def calculate_pip_value(pair: str, lot_size: float = 1.0) -> float:
    """Calculate pip value for forex pairs"""
    # Standard lot = 100,000 units
    # JPY pairs: 1 pip = $1 per mini lot
    
    if pair.endswith("JPY"):
        return 0.01 * lot_size * 1000  # Mini lot
    else:
        return 0.0001 * lot_size * 100000  # Standard


def timeframe_to_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes"""
    timeframe_map = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
        "1w": 10080
    }
    return timeframe_map.get(timeframe, 60)


def calculate_ma(series: pd.Series, period: int) -> pd.Series:
    """Calculate simple moving average"""
    return series.rolling(window=period).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate exponential moving average"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_bb(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands"""
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    
    return upper_band, sma, lower_band


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD"""
    fast_ema = series.ewm(span=fast, adjust=False).mean()
    slow_ema = series.ewm(span=slow, adjust=False).mean()
    
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                        period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator"""
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
    k_line = k_percent.rolling(window=smooth_k).mean()
    d_line = k_line.rolling(window=smooth_d).mean()
    
    return k_line, d_line


class Logger:
    """Custom logger for trading bot"""
    
    @staticmethod
    def setup_logger(name: str, log_file: str = "trading_bot.log") -> logging.Logger:
        """Setup logger with file and console handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # Create file handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
