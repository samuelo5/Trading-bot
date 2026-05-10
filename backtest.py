"""
Backtesting Module - Test strategies on historical data
"""

import logging
from typing import Dict, List
import pandas as pd
from config import Config
from market_data import MarketDataFetcher
from strategies.base_strategy import StrategyManager
from datetime import datetime

class BacktestResults:
    """Store and analyze backtest results"""
    
    def __init__(self):
        self.trades = []
        self.equity_curve = []
        self.metrics = {}
    
    def add_trade(self, symbol: str, entry_price: float, exit_price: float, 
                 size: float, entry_time: datetime, exit_time: datetime):
        """Add a trade to results"""
        pnl = (exit_price - entry_price) * size
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        duration = (exit_time - entry_time).total_seconds() / 3600  # hours
        
        trade = {
            "symbol": symbol,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "size": size,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "duration_hours": duration
        }
        self.trades.append(trade)
    
    def calculate_metrics(self, initial_balance: float):
        """Calculate performance metrics"""
        if not self.trades:
            self.metrics = {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0
            }
            return
        
        trades_df = pd.DataFrame(self.trades)
        
        winning = trades_df[trades_df['pnl'] > 0]
        losing = trades_df[trades_df['pnl'] <= 0]
        
        total_pnl = trades_df['pnl'].sum()
        total_pnl_percent = (total_pnl / initial_balance) * 100
        
        self.metrics = {
            "total_trades": len(trades_df),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": (len(winning) / len(trades_df) * 100) if len(trades_df) > 0 else 0,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "avg_win": winning['pnl'].mean() if len(winning) > 0 else 0,
            "avg_loss": losing['pnl'].mean() if len(losing) > 0 else 0,
            "profit_factor": abs(winning['pnl'].sum() / losing['pnl'].sum()) if len(losing) > 0 and losing['pnl'].sum() != 0 else 0,
            "best_trade": trades_df['pnl'].max(),
            "worst_trade": trades_df['pnl'].min()
        }
    
    def print_summary(self):
        """Print backtest summary"""
        print("\n" + "="*50)
        print("BACKTEST RESULTS")
        print("="*50)
        print(f"Total Trades: {self.metrics.get('total_trades', 0)}")
        print(f"Winning Trades: {self.metrics.get('winning_trades', 0)}")
        print(f"Losing Trades: {self.metrics.get('losing_trades', 0)}")
        print(f"Win Rate: {self.metrics.get('win_rate', 0):.2f}%")
        print(f"Total P&L: ${self.metrics.get('total_pnl', 0):.2f}")
        print(f"Total Return: {self.metrics.get('total_pnl_percent', 0):.2f}%")
        print(f"Avg Win: ${self.metrics.get('avg_win', 0):.2f}")
        print(f"Avg Loss: ${self.metrics.get('avg_loss', 0):.2f}")
        print(f"Profit Factor: {self.metrics.get('profit_factor', 0):.2f}")
        print(f"Best Trade: ${self.metrics.get('best_trade', 0):.2f}")
        print(f"Worst Trade: ${self.metrics.get('worst_trade', 0):.2f}")
        print("="*50 + "\n")
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert trades to DataFrame"""
        return pd.DataFrame(self.trades)


class Backtester:
    """Run backtest on historical data"""
    
    def __init__(self, config: Config, data_fetcher: MarketDataFetcher, 
                 strategy_manager: StrategyManager):
        self.config = config
        self.data_fetcher = data_fetcher
        self.strategy_manager = strategy_manager
        self.logger = logging.getLogger(__name__)
    
    def backtest_symbol(self, symbol: str, timeframe: str = "1h", 
                       candles: int = 500) -> BacktestResults:
        """
        Backtest a strategy on a single symbol
        
        Args:
            symbol: Trading pair (e.g., "EURUSD")
            timeframe: Candle timeframe (e.g., "1h")
            candles: Number of historical candles to backtest
        
        Returns:
            BacktestResults object with performance metrics
        """
        self.logger.info(f"Starting backtest for {symbol} on {timeframe} timeframe")
        
        # Get historical data
        df = self.data_fetcher.get_candles(symbol, timeframe, limit=candles)
        
        if df is None or len(df) < 100:
            self.logger.error(f"Insufficient data for backtest: {len(df) if df is not None else 0} candles")
            return BacktestResults()
        
        results = BacktestResults()
        initial_balance = self.config.get('trading.account_balance', 10000)
        
        # Simulate trading through historical data
        position_open = False
        entry_price = 0
        entry_idx = 0
        
        for i in range(50, len(df)):  # Start after 50 candles for sufficient history
            # Get signal
            historical_df = df.iloc[:i+1].copy()
            signal = self.strategy_manager.get_consensus_signal(symbol, historical_df)
            
            # Entry signal
            if not position_open and signal['action'] == "BUY" and signal['strength'] > 0.5:
                position_open = True
                entry_price = df.iloc[i]['close']
                entry_idx = i
                self.logger.info(f"Entry at {df.iloc[i]['timestamp']}: ${entry_price:.4f}")
            
            # Exit signal
            elif position_open and (signal['action'] == "SELL" or self._should_exit(df.iloc[i], entry_price)):
                exit_price = df.iloc[i]['close']
                exit_time = df.iloc[i]['timestamp']
                entry_time = df.iloc[entry_idx]['timestamp']
                
                # Log trade
                size = initial_balance / entry_price * 0.1  # 10% of account per trade
                results.add_trade(symbol, entry_price, exit_price, size, 
                                entry_time, exit_time)
                
                pnl_percent = ((exit_price - entry_price) / entry_price) * 100
                self.logger.info(f"Exit at {exit_time}: ${exit_price:.4f} (P&L: {pnl_percent:.2f}%)")
                
                position_open = False
        
        # Calculate metrics
        results.calculate_metrics(initial_balance)
        
        return results
    
    def _should_exit(self, candle, entry_price):
        """Check if exit criteria are met"""
        # Exit if loss exceeds 2%
        loss = ((entry_price - candle['close']) / entry_price) * 100
        if loss > 2:
            return True
        
        # Exit if profit exceeds 5%
        profit = ((candle['close'] - entry_price) / entry_price) * 100
        if profit > 5:
            return True
        
        return False
    
    def backtest_multiple(self, symbols: List[str], timeframe: str = "1h") -> Dict[str, BacktestResults]:
        """Backtest multiple symbols"""
        results = {}
        
        for symbol in symbols:
            results[symbol] = self.backtest_symbol(symbol, timeframe)
        
        return results
    
    def print_comparison(self, results: Dict[str, BacktestResults]):
        """Print comparison of multiple backtests"""
        print("\n" + "="*70)
        print("BACKTEST COMPARISON")
        print("="*70)
        
        for symbol, result in results.items():
            print(f"\n{symbol}:")
            print(f"  Total Trades: {result.metrics.get('total_trades', 0)}")
            print(f"  Win Rate: {result.metrics.get('win_rate', 0):.2f}%")
            print(f"  Total Return: {result.metrics.get('total_pnl_percent', 0):.2f}%")
            print(f"  Profit Factor: {result.metrics.get('profit_factor', 0):.2f}")


def run_backtest():
    """Run a complete backtest example"""
    logging.basicConfig(level=logging.INFO)
    
    # Setup
    config = Config()
    data_fetcher = MarketDataFetcher(config)
    strategy_manager = StrategyManager(config)
    
    # Create backtester
    backtester = Backtester(config, data_fetcher, strategy_manager)
    
    # Test single symbol
    print("Running backtest on EURUSD...")
    results = backtester.backtest_symbol("EURUSD", "1h", candles=500)
    results.print_summary()
    
    # Save results
    df = results.to_dataframe()
    df.to_csv("backtest_results.csv", index=False)
    print("Results saved to backtest_results.csv")


if __name__ == "__main__":
    run_backtest()
