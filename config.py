"""
Configuration Management for Trading Bot
"""

import json
import os
from typing import Dict, Any
from dotenv import load_dotenv


class Config:
    """Load and manage trading bot configuration"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        load_dotenv()
        self.settings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file or use defaults"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "trading": {
                "enable_forex": True,
                "enable_stocks": False,
                "enable_crypto": False,
                "enable_commodities": False,
                "account_balance": 10000.0,
                "risk_per_trade": 0.02,  # 2% of account
                "max_position_size": 0.05  # 5% of account
            },
            "forex": {
                "pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
                "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
                "default_timeframe": "1h"
            },
            "api": {
                "provider": "oanda",  # oanda, alpaca, polygon, etc.
                "api_key": "your_api_key_here",
                "account_id": "your_account_id_here",
                "sandbox": True  # Use sandbox for testing
            },
            "strategy": {
                "enabled_strategies": ["moving_average_crossover", "rsi_strategy"],
                "lookback_periods": 20,
                "update_interval_seconds": 60
            },
            "risk_management": {
                "stop_loss_percent": 2.0,
                "take_profit_percent": 5.0,
                "trailing_stop_enabled": False,
                "trailing_stop_percent": 1.5,
                "max_drawdown_percent": 10.0
            },
            "logging": {
                "level": "INFO",
                "log_file": "trading_bot.log",
                "log_trades": True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot notation (e.g., 'trading.enable_forex')"""
        # Check environment variables first for sensitive keys
        env_mapping = {
            'api.api_key': ['OANDA_API_KEY', 'ALPACA_API_KEY', 'POLYGON_API_KEY'],
            'api.account_id': ['OANDA_ACCOUNT_ID'],
            'api.api_secret': ['ALPACA_SECRET_KEY']
        }
        
        if key in env_mapping:
            provider = self.settings.get('api', {}).get('provider', '').upper()
            for env_key in env_mapping[key]:
                if provider in env_key:
                    value = os.getenv(env_key)
                    if value:
                        return value

        keys = key.split('.')
        value = self.settings
        for k in keys:
            value = value.get(k, {})
        return value if value else default
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by dot notation"""
        keys = key.split('.')
        config = self.settings
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save configuration to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def get_summary(self) -> str:
        """Get a summary of current configuration"""
        return f"Forex: {self.get('trading.enable_forex')}, Account: ${self.get('trading.account_balance')}, Risk/Trade: {self.get('trading.risk_per_trade')*100}%"
