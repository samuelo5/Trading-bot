"""Broker API integration layer for live trading providers.

This module provides a provider-neutral interface for OANDA, Alpaca and Polygon.
It is intentionally structured to be ready for real credentials without forcing a
live connection during normal local development.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from config import Config


class BrokerConnector(ABC):
    """Base broker connector contract."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.provider = self.config.get("api.provider", "mock").lower()

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """Return account metadata."""

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Return latest quote for a symbol."""

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        """Return historical candles for a symbol."""

    @abstractmethod
    def place_order(self, symbol: str, side: str, units: float, order_type: str = "market") -> Dict[str, Any]:
        """Submit an order to the broker."""

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """Return currently open positions."""


class MockBrokerConnector(BrokerConnector):
    """Fallback connector for local/mock trading."""

    def get_account_info(self) -> Dict[str, Any]:
        return {
            "balance": float(self.config.get("trading.account_balance", 10000.0) or 10000.0),
            "equity": float(self.config.get("trading.account_balance", 10000.0) or 10000.0),
            "currency": "USD",
            "status": "mock",
        }

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        base = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 154.50,
            "AUDUSD": 0.6580,
        }.get(symbol, 1.0)
        return {
            "symbol": symbol,
            "bid": round(base - 0.0001, 6),
            "ask": round(base + 0.0001, 6),
            "mid": round(base, 6),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        from market_data import MarketDataFetcher

        fetcher = MarketDataFetcher(self.config)
        return fetcher._generate_mock_candles(symbol, timeframe, limit)

    def place_order(self, symbol: str, side: str, units: float, order_type: str = "market") -> Dict[str, Any]:
        return {
            "ok": True,
            "symbol": symbol,
            "side": side.upper(),
            "units": units,
            "order_type": order_type,
            "status": "mock_order",
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        return []


class OandaConnector(BrokerConnector):
    """OANDA connector skeleton.

    Real implementation would use the OANDA REST API with the bearer token and
    account ID from environment variables or config.
    """

    def get_account_info(self) -> Dict[str, Any]:
        api_key = self.config.get("api.api_key")
        account_id = self.config.get("api.account_id")
        if not api_key or not account_id:
            return MockBrokerConnector(self.config).get_account_info()

        url = f"https://api-fxpractice.oanda.com/v3/accounts/{account_id}"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        payload = response.json()
        return payload.get("account", {"status": "connected"})

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        api_key = self.config.get("api.api_key")
        if not api_key:
            return MockBrokerConnector(self.config).get_quote(symbol)

        url = "https://api-fxpractice.oanda.com/v3/accounts"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return MockBrokerConnector(self.config).get_quote(symbol)
        return {"symbol": symbol.upper(), "source": "oanda", "status": "connected"}

    def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        raise NotImplementedError("Add real OANDA candle fetching for your account.")

    def place_order(self, symbol: str, side: str, units: float, order_type: str = "market") -> Dict[str, Any]:
        raise NotImplementedError("Add real OANDA order submission for your account.")

    def get_positions(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Add real OANDA position retrieval for your account.")


class AlpacaConnector(BrokerConnector):
    """Alpaca connector skeleton for stocks and crypto."""

    def get_account_info(self) -> Dict[str, Any]:
        api_key = self.config.get("api.api_key")
        if not api_key:
            return MockBrokerConnector(self.config).get_account_info()
        return {"status": "connected", "source": "alpaca"}

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        return {"symbol": symbol.upper(), "source": "alpaca", "status": "connected"}

    def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        raise NotImplementedError("Add real Alpaca historical data fetching.")

    def place_order(self, symbol: str, side: str, units: float, order_type: str = "market") -> Dict[str, Any]:
        raise NotImplementedError("Add real Alpaca order submission.")

    def get_positions(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Add real Alpaca position retrieval.")


class PolygonConnector(BrokerConnector):
    """Polygon connector skeleton for market data and orders."""

    def get_account_info(self) -> Dict[str, Any]:
        return {"status": "connected", "source": "polygon"}

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        return {"symbol": symbol.upper(), "source": "polygon", "status": "connected"}

    def get_candles(self, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
        raise NotImplementedError("Add real Polygon candle fetching.")

    def place_order(self, symbol: str, side: str, units: float, order_type: str = "market") -> Dict[str, Any]:
        raise NotImplementedError("Add real Polygon order submission.")

    def get_positions(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Add real Polygon position retrieval.")


def create_broker_connector(config: Config) -> BrokerConnector:
    """Create the broker connector instance for the configured provider."""
    provider = (config.get("api.provider") or "mock").lower()
    provider_map = {
        "oanda": OandaConnector,
        "alpaca": AlpacaConnector,
        "polygon": PolygonConnector,
    }
    connector_class = provider_map.get(provider, MockBrokerConnector)
    return connector_class(config)
