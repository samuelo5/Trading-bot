"""
Market Data Fetcher - Handles real-time and historical data retrieval
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from config import Config

# Fetch market data from various sources (OANDA, Alpaca, Polygon)
class MarketDataFetcher:
    """Fetch market data from various sources"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.initialize_provider()
    
    def initialize_provider(self):
        """Initialize the API provider"""
        provider = self.config.get('api.provider')
        sandbox = self.config.get('api.sandbox')
        
        self.logger.info(f"Initializing {provider} provider (Sandbox: {sandbox})")
        
        if provider == "oanda":
            self._setup_oanda()
        elif provider == "alpaca":
            self._setup_alpaca()
        elif provider == "polygon":
            self._setup_polygon()
        else:
            self.logger.warning(f"Unknown provider: {provider}. Using mock data only")
    
    def _setup_oanda(self):
        """Setup OANDA API client"""
        try:
            api_key = self.config.get('api.api_key')
            account_id = self.config.get('api.account_id')
            sandbox = self.config.get('api.sandbox')
            
            # OANDA API initialization would go here
            # For now, we'll mock it
            self.logger.info(f"OANDA client configured (Account: {account_id})")
        except Exception as e:
            self.logger.error(f"Failed to setup OANDA: {str(e)}")
    
    def _setup_alpaca(self):
        """Setup Alpaca API client"""
        self.logger.info("Alpaca client configured")
    
    def _setup_polygon(self):
        """Setup Polygon API client"""
        self.logger.info("Polygon client configured")
    
    def get_forex_quotes(self, pairs: List[str]) -> Dict[str, Dict]:
        """Get current forex quotes for given pairs"""
        quotes = {}
        for pair in pairs:
            quotes[pair] = self._get_mock_quote(pair)
        return quotes
    
    def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Get historical candlestick data"""
        cache_key = f"{symbol}_{timeframe}"
        
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # Generate mock data
        df = self._generate_mock_candles(symbol, timeframe, limit)
        self.data_cache[cache_key] = df
        
        return df
    
    def _get_mock_quote(self, pair: str) -> Dict:
        """Get mock quote data for testing"""
        import random
        
        base_prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 154.50,
            "AUDUSD": 0.6580
        }
        
        base = base_prices.get(pair, 1.0)
        variation = random.uniform(-0.01, 0.01)
        
        return {
            "pair": pair,
            "bid": base - 0.0001,
            "ask": base + 0.0001,
            "mid": base,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_mock_candles(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Generate mock candlestick data for backtesting"""
        import random
        import numpy as np
        
        now = datetime.now()
        candles = []
                    
        # Determine time delta based on timeframe
        timeframe_map = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1)
        }
        
        delta = timeframe_map.get(timeframe, timedelta(hours=1))
        base_price = 100.0
        
        for i in range(limit, 0, -1):
            timestamp = now - (delta * i)
            open_price = base_price + random.uniform(-0.5, 0.5)
            close_price = open_price + random.uniform(-0.5, 0.5)
            high_price = max(open_price, close_price) + random.uniform(0, 0.3)
            low_price = min(open_price, close_price) - random.uniform(0, 0.3)
            volume = random.randint(1000, 100000)
            
            base_price = close_price
            
            candles.append({
                "timestamp": timestamp,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume
            })
        
        return pd.DataFrame(candles)
    
    def get_account_info(self) -> Dict:
        """Get current account information"""
        return {
            "balance": self.config.get('trading.account_balance'),
            "equity": self.config.get('trading.account_balance'),
            "currency": "USD"
        }
    
    def get_open_positions(self) -> List[Dict]:
        """Get list of open positions"""
        # This would fetch actual positions from broker API
        return []
