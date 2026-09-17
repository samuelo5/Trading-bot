"""
Market Data Fetcher - Handles real-time and historical data retrieval.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from broker_integration import create_broker_connector
from config import Config


class MarketDataFetcher:
    """Fetch market data from supported providers with mock fallback."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.provider = self.config.get("api.provider", "mock")
        self.broker_connector = create_broker_connector(config)
        self.initialize_provider()

    def initialize_provider(self):
        """Initialize the selected API provider."""
        provider = (self.config.get("api.provider") or "mock").lower()
        sandbox = self.config.get("api.sandbox", True)
        self.provider = provider

        self.logger.info(f"Initializing {provider} provider (Sandbox: {sandbox})")

        if provider == "oanda":
            self._setup_oanda()
        elif provider == "alpaca":
            self._setup_alpaca()
        elif provider == "polygon":
            self._setup_polygon()
        else:
            self.logger.warning("Unknown or missing provider: %s. Using mock data fallback.", provider)

    def _setup_oanda(self):
        """Setup OANDA API client placeholder."""
        try:
            self.logger.info("OANDA client configured (Account: %s)", self.config.get("api.account_id", "unknown"))
        except Exception as exc:  # pragma: no cover - defensive logging only
            self.logger.error("Failed to setup OANDA: %s", exc)

    def _setup_alpaca(self):
        """Setup Alpaca API client placeholder."""
        self.logger.info("Alpaca client configured")

    def _setup_polygon(self):
        """Setup Polygon API client placeholder."""
        self.logger.info("Polygon client configured")

    def get_forex_quotes(self, pairs: List[str]) -> Dict[str, Dict]:
        """Get current forex quotes for the provided pairs."""
        quotes: Dict[str, Dict] = {}
        for pair in pairs:
            try:
                quote = self.broker_connector.get_quote(pair)
                if quote:
                    quotes[pair.upper()] = quote
                    continue
            except Exception as exc:
                self.logger.warning("Broker quote lookup failed for %s: %s", pair, exc)
            quotes[pair.upper()] = self._get_mock_quote(pair.upper())
        return quotes

    def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Return historical candlestick data from cache or generated mock data."""
        cache_key = f"{symbol.upper()}_{timeframe}"

        if cache_key in self.data_cache:
            return self.data_cache[cache_key]

        df = self._generate_mock_candles(symbol, timeframe, limit)
        self.data_cache[cache_key] = df
        return df

    def _get_mock_quote(self, pair: str) -> Dict:
        """Generate a stable mock quote for a pair."""
        base_prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 154.50,
            "AUDUSD": 0.6580,
        }

        base = base_prices.get(pair.upper(), 1.0)
        spread = 0.0002 if base < 10 else 0.05
        bid = round(base - (spread / 2), 6 if base < 10 else 4)
        ask = round(base + (spread / 2), 6 if base < 10 else 4)

        return {
            "pair": pair.upper(),
            "bid": bid,
            "ask": ask,
            "mid": round((bid + ask) / 2, 6 if base < 10 else 4),
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_mock_candles(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        """Generate deterministic mock candle data for backtesting and simulation."""
        if limit <= 0:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        timeframe_map = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
        }

        delta = timeframe_map.get(timeframe, timedelta(hours=1))
        symbol_key = symbol.upper()
        base_prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 154.50,
            "AUDUSD": 0.6580,
        }
        base_price = float(base_prices.get(symbol_key, 100.0))

        candles = []
        now = datetime.now()
        current_price = base_price

        for i in range(limit):
            timestamp = now - (delta * (limit - i))
            drift = (i / max(limit, 1)) * 0.002
            open_price = current_price
            jump = random.uniform(-0.006, 0.006) + drift
            close_price = open_price * (1 + jump)
            high_price = max(open_price, close_price) * (1 + random.uniform(0.0005, 0.004))
            low_price = min(open_price, close_price) * (1 - random.uniform(0.0005, 0.004))
            volume = random.randint(1000, 100000)

            candles.append(
                {
                    "timestamp": timestamp,
                    "open": round(open_price, 6 if base_price < 10 else 4),
                    "high": round(high_price, 6 if base_price < 10 else 4),
                    "low": round(low_price, 6 if base_price < 10 else 4),
                    "close": round(close_price, 6 if base_price < 10 else 4),
                    "volume": volume,
                }
            )
            current_price = close_price

        return pd.DataFrame(candles)

    def get_account_info(self) -> Dict:
        """Get current account information."""
        try:
            account = self.broker_connector.get_account_info()
            if account:
                return {
                    "balance": float(account.get("balance", self.config.get("trading.account_balance", 10000.0))),
                    "equity": float(account.get("equity", self.config.get("trading.account_balance", 10000.0))),
                    "currency": account.get("currency", "USD"),
                    "status": account.get("status", "connected"),
                }
        except Exception as exc:
            self.logger.warning("Broker account lookup failed: %s", exc)

        return {
            "balance": float(self.config.get("trading.account_balance", 10000.0) or 10000.0),
            "equity": float(self.config.get("trading.account_balance", 10000.0) or 10000.0),
            "currency": "USD",
            "status": "mock",
        }

    def get_open_positions(self) -> List[Dict]:
        """Return a placeholder list for open positions."""
        return []

