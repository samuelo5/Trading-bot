# Trading Bot - Python Forex & Asset Trading System

A sophisticated Python-based trading bot designed for automated forex trading and other asset classes with advanced risk management and multiple trading strategies.

## Features

✅ **Multi-Asset Support**
- Forex trading (primary)
- Stocks (configurable)
- Cryptocurrencies (configurable)
- Commodities (configurable)

✅ **Trading Strategies**
- Moving Average Crossover Strategy
- RSI (Relative Strength Index) Strategy
- Consensus-based signal generation
- Easy to extend with custom strategies

✅ **Risk Management**
- Position sizing based on account risk
- Stop loss and take profit levels
- Maximum drawdown limits
- Risk/reward ratio validation
- Max position size limits

✅ **Data Management**
- Real-time market data integration
- Historical data fetching
- Data caching for performance
- Support for multiple data providers (OANDA, Alpaca, Polygon)

✅ **Logging & Analytics**
- Comprehensive trade logging
- Performance metrics tracking
- Real-time P&L monitoring
- CSV export for analysis

✅ **Configuration Management**
- JSON-based configuration
- Easy parameter adjustment
- Sandbox mode for testing
- Environment-specific settings

## Project Structure

```
Trading Bot/
├── main.py                 # Application entry point
├── config.py              # Configuration management
├── config.json            # Configuration file
├── market_data.py         # Market data fetching
├── trading_engine.py      # Core trading logic
├── risk_management.py     # Risk calculations
├── utils.py               # Utility functions
├── strategies/
│   └── base_strategy.py   # Strategy definitions
├── trading_bot.log        # Application logs
├── trades.csv             # Trade history
└── requirements.txt       # Python dependencies
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or extract the trading bot directory**
   ```bash
   cd "Trading Bot"
   ```

2. **Create a virtual environment** (optional but recommended)
   ```bash
   python -m venv venv
   ```
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### config.json

Edit `config.json` to customize your trading bot:

```json
{
  "trading": {
    "enable_forex": true,           // Enable forex trading
    "account_balance": 10000.0,     // Starting account balance
    "risk_per_trade": 0.02,         // Risk 2% per trade
    "max_position_size": 0.05       // Max 5% per position
  },
  "forex": {
    "pairs": ["EURUSD", "GBPUSD"],  // Trading pairs
    "default_timeframe": "1h"       // Candle timeframe
  },
  "api": {
    "provider": "oanda",            // API provider
    "api_key": "your_api_key",      // Your API key
    "account_id": "your_account_id", // Your account ID
    "sandbox": true                 // Test mode
  },
  "strategy": {
    "enabled_strategies": ["moving_average_crossover", "rsi_strategy"],
    "update_interval_seconds": 60   // Update frequency
  },
  "risk_management": {
    "stop_loss_percent": 2.0,       // Stop loss at 2%
    "take_profit_percent": 5.0,     // Take profit at 5%
    "max_drawdown_percent": 10.0    // Max drawdown allowed
  }
}
```

## API Integration

### Supported Providers

1. **OANDA** (Recommended for Forex)
   - Get API key from https://www.oanda.com
   - Set `provider` to "oanda" in config.json
   - Add your API key and account ID

2. **Alpaca** (For Stocks)
   - Get API key from https://alpaca.markets
   - Set `provider` to "alpaca"

3. **Polygon.io** (For Stocks and Crypto)
   - Get API key from https://polygon.io
   - Set `provider` to "polygon"

## Usage

### Run the Trading Bot

```bash
python main.py
```

The bot will:
1. Load configuration from `config.json`
2. Initialize market data fetcher and strategies
3. Enter the main trading loop
4. Analyze each configured trading pair
5. Generate trading signals based on strategies
6. Open/close positions based on signals
7. Log all trades to `trades.csv`

### Monitor Trading

The bot logs information to both console and `trading_bot.log`:
- Market analysis results
- Open/close position details
- P&L updates
- Risk metrics

### Analyze Results

Trade history is automatically logged to `trades.csv` containing:
- Entry/exit times and prices
- P&L and P&L percentage
- Strategy used
- Trade duration

## Trading Strategies

### 1. Moving Average Crossover
- **Fast MA Period**: 10 (default)
- **Slow MA Period**: 20 (default)
- **Signal**: Golden Cross (bullish) / Death Cross (bearish)
- **Best for**: Trend-following

### 2. RSI Strategy
- **Period**: 14 (default)
- **Overbought Level**: 70
- **Oversold Level**: 30
- **Signal**: Oversold (buy) / Overbought (sell)
- **Best for**: Mean reversion

### Adding Custom Strategies

1. Create a new class in `strategies/base_strategy.py` inheriting from `BaseStrategy`
2. Implement the `calculate_signal()` method
3. Return a dict with `action` ("BUY"/"SELL"/"HOLD") and `strength` (0-1)
4. Add to `enabled_strategies` in config.json

Example:
```python
class MyStrategy(BaseStrategy):
    def calculate_signal(self, df):
        # Your logic here
        return {"action": "BUY", "strength": 0.8, "parameters": {}}
```

## Risk Management

### Position Sizing
- Risk per trade: Configurable percentage of account
- Maximum position size: Prevents over-concentration
- Risk/reward ratio: Enforces minimum ratio

### Stop Loss & Take Profit
- Automatic SL/TP calculation based on % risk
- Automatic position closure at levels
- P&L monitoring every cycle

### Account Protection
- Maximum drawdown limit
- Risk metrics monitoring
- Position count tracking

## Logging

The bot creates two log files:

1. **trading_bot.log**: Detailed application logs
   - Timestamps and log levels
   - Market analysis details
   - Position changes
   - Errors and warnings

2. **trades.csv**: Trade history
   - All executed trades
   - Entry/exit prices
   - P&L calculations
   - Used for backtesting and analysis

## Testing & Backtesting

### Sandbox Mode
Set `sandbox: true` in config.json to:
- Use simulated account
- Practice without real money
- Test strategies risk-free

### Backtesting
The trading engine generates realistic mock data for backtesting. To backtest:

1. Set `sandbox: true`
2. Configure your strategy parameters
3. Run the bot - it will use mock data
4. Analyze `trades.csv` for performance

## Performance Monitoring

Key metrics tracked:
- **Account Balance**: Current equity
- **Open Positions**: Number and size
- **P&L**: Profit/loss per position
- **Drawdown**: Current account drawdown
- **Win Rate**: Winning trades percentage
- **Risk Metrics**: Exposure and ratios

## Troubleshooting

### API Connection Issues
- Verify API key and account ID in config.json
- Check sandbox setting matches your account type
- Ensure internet connection is stable

### Insufficient Data
- Bot requires 20+ candles for analysis
- Ensure timeframe is available from provider
- Wait for more data to accumulate

### Position Not Opening
- Check account balance is sufficient
- Verify risk management parameters
- Check strategy signals and thresholds

## Advanced Features

### Trailing Stop
Enable in config.json for trailing stop loss:
```json
"trailing_stop_enabled": true,
"trailing_stop_percent": 1.5
```

### Multiple Timeframes
Configure multiple timeframes:
```json
"timeframes": ["15m", "1h", "4h", "1d"]
```

### Custom Indicators
Utility module includes:
- Moving Averages (SMA, EMA)
- Bollinger Bands
- MACD
- ATR
- Stochastic Oscillator

## Important Notes

⚠️ **Disclaimer**
- Trading involves substantial risk of loss
- Past performance is not indicative of future results
- Start with small amounts in sandbox mode
- Never risk more than you can afford to lose
- Thoroughly test strategies before trading live

⚠️ **Development Stage**
- Uses mock data in default configuration
- Integration with real brokers requires API setup
- Requires thorough testing before live trading
- Consider consulting a financial advisor

## Dependencies

```
pandas>=1.3.0
numpy>=1.21.0
requests>=2.26.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Future Enhancements

- [ ] Web dashboard for monitoring
- [ ] Advanced chart visualization
- [ ] Machine learning strategies
- [ ] Mobile notifications
- [ ] Multi-broker support
- [ ] Advanced backtesting engine
- [ ] Live performance metrics
- [ ] Strategy optimization

## Contributing

To extend the bot:

1. Add new strategies in `strategies/base_strategy.py`
2. Add new indicators to `utils.py`
3. Customize `config.json` for your needs
4. Create new modules for additional features

## Support & Resources

- **OANDA Documentation**: https://developer.oanda.com
- **Python Trading**: https://www.python.org
- **Pandas Documentation**: https://pandas.pydata.org
- **Trading Concepts**: https://www.investopedia.com

## License

This project is provided as-is for educational purposes.

---

**Happy Trading!** 🚀

Remember: Always start small, test thoroughly, and never risk more than you can afford to lose.
