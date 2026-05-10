"""
Trading Engine - Core trading logic and execution
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from config import Config
from market_data import MarketDataFetcher
from strategies.base_strategy import StrategyManager
from risk_management import RiskManager


class Position:
    """Represents an open trading position"""
    
    def __init__(self, symbol: str, entry_price: float, size: float, position_type: str):
        self.symbol = symbol
        self.entry_price = entry_price
        self.size = size
        self.position_type = position_type  # "LONG" or "SHORT"
        self.entry_time = datetime.now()
        self.stop_loss = None
        self.take_profit = None
        self.current_price = entry_price
    
    def update_price(self, price: float):
        """Update current position price"""
        self.current_price = price
    
    def get_pnl(self) -> float:
        """Calculate current P&L"""
        if self.position_type == "LONG":
            return (self.current_price - self.entry_price) * self.size
        else:  # SHORT
            return (self.entry_price - self.current_price) * self.size
    
    def get_pnl_percent(self) -> float:
        """Calculate P&L percentage"""
        if self.entry_price == 0:
            return 0
        return (self.get_pnl() / (self.entry_price * self.size)) * 100


class TradeLog:
    """Log all trades for analysis"""
    
    def __init__(self, log_file: str = "trades.csv"):
        self.log_file = log_file
        self.trades = []
        self._write_header()
    
    def _write_header(self):
        """Write CSV header if file is empty"""
        try:
            with open(self.log_file, 'w') as f:
                f.write("Entry Time,Symbol,Type,Entry Price,Exit Price,Size,PnL,PnL%,Strategy,Duration\n")
        except Exception as e:
            logging.error(f"Failed to write trade log header: {e}")
    
    def log_trade(self, position: Position, exit_price: float, strategy: str):
        """Log a closed trade"""
        pnl = (exit_price - position.entry_price) * position.size if position.position_type == "LONG" else (
            position.entry_price - exit_price) * position.size
        pnl_percent = (pnl / (position.entry_price * position.size)) * 100
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
            "duration": duration
        }
        
        self.trades.append(trade_data)
        
        # Append to CSV
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"{position.entry_time},{position.symbol},{position.position_type},"
                       f"{position.entry_price},{exit_price},{position.size},"
                       f"{pnl:.2f},{pnl_percent:.2f}%,{strategy},{duration}\n")
        except Exception as e:
            logging.error(f"Failed to log trade: {e}")


class TradingEngine:
    """Main trading engine"""
    
    def __init__(self, config: Config, data_fetcher: MarketDataFetcher, strategy_manager: StrategyManager):
        self.config = config
        self.data_fetcher = data_fetcher
        self.strategy_manager = strategy_manager
        self.risk_manager = RiskManager(config)
        self.logger = logging.getLogger(__name__)
        
        self.positions: Dict[str, Position] = {}
        self.trade_log = TradeLog()
        self.account_balance = config.get('trading.account_balance')
        self.running = False
    
    def run(self):
        """Start the trading engine main loop"""
        self.running = True
        self.logger.info("Trading Engine Started")
        
        update_interval = self.config.get('strategy.update_interval_seconds', 60)
        forex_pairs = self.config.get('forex.pairs', [])
        timeframe = self.config.get('forex.default_timeframe', '1h')
        
        try:
            while self.running:
                try:
                    self.logger.info("=== Trading Cycle Started ===")
                    
                    # Get account info
                    account = self.data_fetcher.get_account_info()
                    self.logger.info(f"Account Balance: ${account['balance']:.2f}")
                    
                    # Process each forex pair
                    if self.config.get('trading.enable_forex'):
                        for pair in forex_pairs:
                            self._process_symbol(pair, timeframe)
                    
                    # Update open positions
                    self._update_positions(forex_pairs)
                    
                    self.logger.info("=== Trading Cycle Complete ===\n")
                    
                    # Wait for next update
                    time.sleep(update_interval)
                
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received")
                    break
                except Exception as e:
                    self.logger.error(f"Error in trading cycle: {str(e)}", exc_info=True)
                    time.sleep(5)  # Wait before retry
        
        finally:
            self._shutdown()
    
    def _process_symbol(self, symbol: str, timeframe: str):
        """Process trading signals for a symbol"""
        try:
            # Get historical data
            df = self.data_fetcher.get_candles(symbol, timeframe)
            
            if df is None or len(df) < 20:
                self.logger.warning(f"Insufficient data for {symbol}")
                return
            
            # Get trading signals
            consensus = self.strategy_manager.get_consensus_signal(symbol, df)
            
            self.logger.info(f"\n{symbol} Analysis:")
            self.logger.info(f"  Action: {consensus['action']}")
            self.logger.info(f"  Strength: {consensus['strength']:.2f}")
            self.logger.info(f"  Consensus: {consensus['consensus']:.2%}")
            
            # Get current price
            current_price = df['close'].iloc[-1]
            
            # Check position management
            if symbol in self.positions:
                self._manage_position(symbol, current_price, consensus)
            else:
                # Check for new entry
                if consensus['action'] == "BUY" and consensus['strength'] > 0.5:
                    self._open_position(symbol, current_price, "LONG", consensus)
                elif consensus['action'] == "SELL" and consensus['strength'] > 0.5:
                    self._open_position(symbol, current_price, "SHORT", consensus)
        
        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {str(e)}")
    
    def _open_position(self, symbol: str, entry_price: float, position_type: str, signal: Dict):
        """Open a new position"""
        # Calculate position size
        max_risk = self.account_balance * self.config.get('trading.risk_per_trade', 0.02)
        stop_loss_percent = self.config.get('risk_management.stop_loss_percent', 2.0) / 100
        
        position_size = max_risk / (entry_price * stop_loss_percent)
        max_position_size = self.account_balance * self.config.get('trading.max_position_size', 0.05)
        
        if position_size * entry_price > max_position_size:
            position_size = max_position_size / entry_price
        
        # Create position
        position = Position(symbol, entry_price, position_size, position_type)
        
        # Set risk management levels
        position.stop_loss = entry_price * (1 - stop_loss_percent) if position_type == "LONG" else entry_price * (
            1 + stop_loss_percent)
        position.take_profit = entry_price * (1 + self.config.get('risk_management.take_profit_percent', 5.0) / 100) if position_type == "LONG" else entry_price * (
            1 - self.config.get('risk_management.take_profit_percent', 5.0) / 100)
        
        self.positions[symbol] = position
        
        self.logger.info(f"  ✓ {position_type} Position Opened")
        self.logger.info(f"    Size: {position_size:.2f} units")
        self.logger.info(f"    Entry: {entry_price:.4f}")
        self.logger.info(f"    Stop Loss: {position.stop_loss:.4f}")
        self.logger.info(f"    Take Profit: {position.take_profit:.4f}")
    
    def _manage_position(self, symbol: str, current_price: float, signal: Dict):
        """Manage existing position"""
        position = self.positions[symbol]
        position.update_price(current_price)
        
        self.logger.info(f"  Position P&L: {position.get_pnl():.2f} ({position.get_pnl_percent():.2f}%)")
        
        # Check stop loss
        if position.position_type == "LONG" and current_price <= position.stop_loss:
            self._close_position(symbol, current_price, "Stop Loss Hit")
            return
        elif position.position_type == "SHORT" and current_price >= position.stop_loss:
            self._close_position(symbol, current_price, "Stop Loss Hit")
            return
        
        # Check take profit
        if position.position_type == "LONG" and current_price >= position.take_profit:
            self._close_position(symbol, current_price, "Take Profit Hit")
            return
        elif position.position_type == "SHORT" and current_price <= position.take_profit:
            self._close_position(symbol, current_price, "Take Profit Hit")
            return
        
        # Check for exit signal
        if signal['action'] == "SELL" and position.position_type == "LONG" and signal['strength'] > 0.5:
            self._close_position(symbol, current_price, "Exit Signal")
        elif signal['action'] == "BUY" and position.position_type == "SHORT" and signal['strength'] > 0.5:
            self._close_position(symbol, current_price, "Exit Signal")
    
    def _close_position(self, symbol: str, exit_price: float, reason: str):
        """Close an open position"""
        position = self.positions[symbol]
        pnl = position.get_pnl()
        pnl_percent = position.get_pnl_percent()
        
        self.logger.info(f"  ✗ Position Closed: {reason}")
        self.logger.info(f"    Exit Price: {exit_price:.4f}")
        self.logger.info(f"    PnL: {pnl:.2f} ({pnl_percent:.2f}%)")
        
        # Update account balance
        self.account_balance += pnl
        
        # Log the trade
        self.trade_log.log_trade(position, exit_price, "Strategy")
        
        # Remove position
        del self.positions[symbol]
    
    def _update_positions(self, symbols: List[str]):
        """Update all open positions"""
        for symbol in list(self.positions.keys()):
            quotes = self.data_fetcher.get_forex_quotes([symbol])
            if symbol in quotes:
                current_price = quotes[symbol]['mid']
                position = self.positions[symbol]
                position.update_price(current_price)
    
    def _shutdown(self):
        """Shutdown the trading engine"""
        self.logger.info("Shutting down Trading Engine")
        self.logger.info(f"Open Positions: {len(self.positions)}")
        self.logger.info(f"Final Balance: ${self.account_balance:.2f}")
        self.running = False
