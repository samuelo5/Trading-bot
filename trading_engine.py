"""
Trading Engine - Core trading logic and execution.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List

from config import Config
from market_data import MarketDataFetcher
from risk_management import RiskManager
from strategies.base_strategy import StrategyManager


class Position:
    """Represents an open trading position."""

    def __init__(self, symbol: str, entry_price: float, size: float, position_type: str):
        self.symbol = symbol
        self.entry_price = float(entry_price)
        self.size = float(size)
        self.position_type = position_type.upper()
        self.entry_time = datetime.now()
        self.stop_loss = None
        self.take_profit = None
        self.current_price = self.entry_price

    def update_price(self, price: float):
        """Update current price."""
        self.current_price = float(price)

    def get_pnl(self) -> float:
        """Calculate current P&L."""
        if self.position_type == "LONG":
            return (self.current_price - self.entry_price) * self.size
        return (self.entry_price - self.current_price) * self.size

    def get_pnl_percent(self) -> float:
        """Calculate P&L percentage."""
        if self.entry_price == 0 or self.size == 0:
            return 0.0
        return (self.get_pnl() / (self.entry_price * self.size)) * 100


class TradeLog:
    """Log all trades for analysis."""

    def __init__(self, log_file: str = "trades.csv"):
        self.log_file = log_file
        self.trades = []
        self._write_header()

    def _write_header(self):
        """Write the CSV header if the file is empty."""
        try:
            with open(self.log_file, "w", encoding="utf-8") as file:
                file.write("Entry Time,Symbol,Type,Entry Price,Exit Price,Size,PnL,PnL%,Strategy,Duration\n")
        except Exception as exc:  # pragma: no cover - defensive logging only
            logging.error("Failed to write trade log header: %s", exc)

    def log_trade(self, position: Position, exit_price: float, strategy: str):
        """Log a closed trade."""
        pnl = (exit_price - position.entry_price) * position.size if position.position_type == "LONG" else (
            position.entry_price - exit_price
        ) * position.size
        pnl_percent = (pnl / (position.entry_price * position.size)) * 100 if position.entry_price * position.size else 0.0
        duration = datetime.now() - position.entry_time

        trade_data = {
            "entry_time": position.entry_time,
            "symbol": position.symbol,
            "type": position.position_type,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "size": position.size,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "strategy": strategy,
            "duration": duration,
        }

        self.trades.append(trade_data)

        try:
            with open(self.log_file, "a", encoding="utf-8") as file:
                file.write(
                    f"{position.entry_time},{position.symbol},{position.position_type},"
                    f"{position.entry_price},{exit_price},{position.size},"
                    f"{pnl:.2f},{pnl_percent:.2f}%,{strategy},{duration}\n"
                )
        except Exception as exc:
            logging.error("Failed to log trade: %s", exc)


class TradingEngine:
    """Main trading engine."""

    def __init__(self, config: Config, data_fetcher: MarketDataFetcher, strategy_manager: StrategyManager):
        self.config = config
        self.data_fetcher = data_fetcher
        self.strategy_manager = strategy_manager
        self.risk_manager = RiskManager(config)
        self.logger = logging.getLogger(__name__)
        self.broker_connector = getattr(data_fetcher, "broker_connector", None)

        self.positions: Dict[str, Position] = {}
        self.trade_log = TradeLog()
        self.account_balance = float(config.get("trading.account_balance", 10000.0) or 10000.0)
        self.running = False

    def run(self):
        """Start the trading engine main loop."""
        self.running = True
        self.logger.info("Trading Engine Started")

        update_interval = int(self.config.get("strategy.update_interval_seconds", 60) or 60)
        forex_pairs = self.config.get("forex.pairs", [])
        timeframe = self.config.get("forex.default_timeframe", "1h")

        try:
            while self.running:
                try:
                    self.logger.info("=== Trading Cycle Started ===")

                    account = self.data_fetcher.get_account_info()
                    self.logger.info("Account Balance: $%.2f", account.get("balance", self.account_balance))

                    if self.config.get("trading.enable_forex", True):
                        for pair in forex_pairs:
                            self._process_symbol(pair, timeframe)

                    self._update_positions(forex_pairs)
                    self.logger.info("=== Trading Cycle Complete ===\n")
                    time.sleep(update_interval)

                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received")
                    break
                except Exception as exc:
                    self.logger.error("Error in trading cycle: %s", exc, exc_info=True)
                    time.sleep(5)
        finally:
            self._shutdown()

    def _shutdown(self):
        """Cleanly shut down the engine."""
        self.running = False
        self.logger.info("Trading Engine Shutdown")

    def _process_symbol(self, symbol: str, timeframe: str):
        """Process trading signals for one symbol."""
        try:
            df = self.data_fetcher.get_candles(symbol, timeframe)
            if df is None or len(df) < 20:
                self.logger.warning("Insufficient data for %s", symbol)
                return

            consensus = self.strategy_manager.get_consensus_signal(symbol, df)
            current_price = float(df["close"].iloc[-1])

            self.logger.info("%s Analysis:", symbol)
            self.logger.info("  Action: %s", consensus.get("action", "HOLD"))
            self.logger.info("  Strength: %.2f", float(consensus.get("strength", 0.0)))
            self.logger.info("  Consensus: %.2f%%", float(consensus.get("consensus", 0.0)) * 100)

            if symbol in self.positions:
                self._manage_position(symbol, current_price, consensus)
            else:
                if consensus.get("action") == "BUY" and float(consensus.get("strength", 0.0)) > 0.5:
                    self._open_position(symbol, current_price, "LONG", consensus)
                elif consensus.get("action") == "SELL" and float(consensus.get("strength", 0.0)) > 0.5:
                    self._open_position(symbol, current_price, "SHORT", consensus)

        except Exception as exc:
            self.logger.error("Error processing %s: %s", symbol, exc)

    def _open_position(self, symbol: str, entry_price: float, position_type: str, signal: Dict):
        """Open a new position with validation and risk checks."""
        if entry_price <= 0:
            return

        max_risk = self.account_balance * float(self.config.get("trading.risk_per_trade", 0.02) or 0.02)
        stop_loss_percent = float(self.config.get("risk_management.stop_loss_percent", 2.0) or 2.0) / 100
        take_profit_percent = float(self.config.get("risk_management.take_profit_percent", 5.0) or 5.0) / 100

        if stop_loss_percent <= 0:
            return

        position_size = max_risk / (entry_price * stop_loss_percent)
        max_position_size = self.account_balance * float(self.config.get("trading.max_position_size", 0.05) or 0.05)
        position_size = min(position_size, max_position_size / entry_price if entry_price else 0)

        if position_size <= 0:
            self.logger.warning("Position size too small for %s; skipping entry.", symbol)
            return

        position = Position(symbol, entry_price, position_size, position_type)
        position.stop_loss = entry_price * (1 - stop_loss_percent) if position_type == "LONG" else entry_price * (1 + stop_loss_percent)
        position.take_profit = entry_price * (1 + take_profit_percent) if position_type == "LONG" else entry_price * (1 - take_profit_percent)

        validation = self.risk_manager.validate_trade(
            symbol,
            entry_price,
            position.stop_loss,
            position.take_profit,
            position_size,
            self.account_balance,
        )

        if not validation["valid"]:
            self.logger.warning("Trade rejected for %s: %s", symbol, validation["reasons"])
            return

        self.positions[symbol] = position
        self.logger.info("  ✓ %s Position Opened", position_type)
        self.logger.info("    Size: %.2f units", position_size)
        self.logger.info("    Entry: %.4f", entry_price)
        self.logger.info("    Stop Loss: %.4f", position.stop_loss)
        self.logger.info("    Take Profit: %.4f", position.take_profit)

    def _manage_position(self, symbol: str, current_price: float, signal: Dict):
        """Manage an existing position."""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        position.update_price(current_price)

        self.logger.info("  Position P&L: %.2f (%.2f%%)", position.get_pnl(), position.get_pnl_percent())

        if position.position_type == "LONG" and current_price <= position.stop_loss:
            self._close_position(symbol, current_price, "Stop Loss Hit")
            return
        if position.position_type == "SHORT" and current_price >= position.stop_loss:
            self._close_position(symbol, current_price, "Stop Loss Hit")
            return

        if position.position_type == "LONG" and current_price >= position.take_profit:
            self._close_position(symbol, current_price, "Take Profit Hit")
            return
        if position.position_type == "SHORT" and current_price <= position.take_profit:
            self._close_position(symbol, current_price, "Take Profit Hit")
            return

        action = signal.get("action", "HOLD")
        strength = float(signal.get("strength", 0.0))

        if action == "SELL" and position.position_type == "LONG" and strength > 0.5:
            self._close_position(symbol, current_price, "Exit Signal")
        elif action == "BUY" and position.position_type == "SHORT" and strength > 0.5:
            self._close_position(symbol, current_price, "Exit Signal")

    def _close_position(self, symbol: str, exit_price: float, reason: str):
        """Close an open position and log the trade."""
        if symbol not in self.positions:
            return

        position = self.positions[symbol]
        pnl = position.get_pnl()
        pnl_percent = position.get_pnl_percent()

        self.logger.info("  ✗ Position Closed: %s", reason)
        self.logger.info("    Exit Price: %.4f", exit_price)
        self.logger.info("    PnL: %.2f (%.2f%%)", pnl, pnl_percent)

        self.account_balance += pnl
        self.trade_log.log_trade(position, exit_price, "Strategy")
        del self.positions[symbol]

    def _update_positions(self, symbols: List[str]):
        """Refresh open positions using live quote data and enforce risk checks."""
        if not self.positions:
            return

        for symbol in list(self.positions.keys()):
            try:
                quote = self.data_fetcher.get_forex_quotes([symbol]).get(symbol)
                if not quote:
                    continue
                current_price = float(quote.get("mid", self.positions[symbol].current_price))
                self._manage_position(symbol, current_price, {"action": "HOLD", "strength": 0.0})
            except Exception as exc:
                self.logger.warning("Failed to refresh %s: %s", symbol, exc)

    def stop(self):
        """Stop the engine cleanly."""
        self.running = False

    def _shutdown(self):
        """Shutdown the trading engine."""
        self.logger.info("Shutting down Trading Engine")
        self.logger.info("Open Positions: %s", len(self.positions))
        self.logger.info("Final Balance: $%.2f", self.account_balance)
        self.running = False
