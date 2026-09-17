"""
Configuration Management for Trading Bot
"""

import json
import os
from typing import Any, Dict

from dotenv import load_dotenv


class Config:
    """Load and manage trading bot configuration."""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = os.path.abspath(config_file)
        load_dotenv()
        self.settings = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON or return safe defaults."""
        defaults = self._get_default_config()

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                if isinstance(loaded, dict):
                    merged = defaults.copy()
                    self._deep_merge(merged, loaded)
                    return merged
            except (json.JSONDecodeError, OSError):
                return defaults

        return defaults

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Merge nested dictionaries without overwriting nested structures unexpectedly."""
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "trading": {
                "enable_forex": True,
                "enable_stocks": False,
                "enable_crypto": False,
                "enable_commodities": False,
                "account_balance": 10000.0,
                "risk_per_trade": 0.02,
                "max_position_size": 0.05,
            },
            "forex": {
                "pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
                "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
                "default_timeframe": "1h",
            },
            "api": {
                "provider": "oanda",
                "api_key": "your_api_key_here",
                "account_id": "your_account_id_here",
                "sandbox": True,
            },
            "strategy": {
                "enabled_strategies": ["moving_average_crossover", "rsi_strategy"],
                "lookback_periods": 20,
                "update_interval_seconds": 60,
            },
            "risk_management": {
                "stop_loss_percent": 2.0,
                "take_profit_percent": 5.0,
                "trailing_stop_enabled": False,
                "trailing_stop_percent": 1.5,
                "max_drawdown_percent": 10.0,
            },
            "logging": {
                "level": "INFO",
                "log_file": "trading_bot.log",
                "log_trades": True,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot notation (e.g., 'trading.enable_forex')."""
        env_mapping = {
            "api.api_key": ["OANDA_API_KEY", "ALPACA_API_KEY", "POLYGON_API_KEY"],
            "api.account_id": ["OANDA_ACCOUNT_ID", "ALPACA_ACCOUNT_ID", "POLYGON_ACCOUNT_ID"],
            "api.api_secret": ["ALPACA_SECRET_KEY", "POLYGON_API_SECRET"],
        }

        if key in env_mapping:
            for env_key in env_mapping[key]:
                value = os.getenv(env_key)
                if value not in (None, ""):
                    return value

        keys = key.split(".")
        value: Any = self.settings
        for nested_key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(nested_key, default)
            if value is default:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by dot notation."""
        keys = key.split(".")
        config = self.settings
        for nested_key in keys[:-1]:
            if nested_key not in config or not isinstance(config[nested_key], dict):
                config[nested_key] = {}
            config = config[nested_key]
        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to JSON file."""
        with open(self.config_file, "w", encoding="utf-8") as file:
            json.dump(self.settings, file, indent=4)

    def get_summary(self) -> str:
        """Get a summary of the current configuration."""
        balance = self.get("trading.account_balance", 10000.0)
        risk = self.get("trading.risk_per_trade", 0.02)
        return (
            f"Forex: {self.get('trading.enable_forex')}, "
            f"Account: ${balance}, Risk/Trade: {float(risk) * 100}%"
        )
