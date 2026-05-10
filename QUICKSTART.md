# Quick Start Guide - Trading Bot

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure (Optional)
The bot comes with default settings. Edit `config.json` if you want to customize:
- Trading pairs
- Account balance
- Risk per trade
- API keys

### Step 3: Run the Bot
```bash
python main.py
```

The bot will start trading with mock data in sandbox mode.

## Understanding the Output

When you run the bot, you'll see output like:

```
2026-02-12 10:30:45 - __main__ - INFO - Starting Trading Bot Application
2026-02-12 10:30:45 - __main__ - INFO - === Trading Cycle Started ===
2026-02-12 10:30:45 - __main__ - INFO - Account Balance: $10000.00

EURUSD Analysis:
  Action: BUY
  Strength: 0.65
  Consensus: 0.70
  ✓ LONG Position Opened
    Size: 10.50 units
    Entry: 1.0850
    Stop Loss: 1.0633
    Take Profit: 1.1393

2026-02-12 10:31:45 - __main__ - INFO - === Trading Cycle Complete ===
```

## Key Metrics

- **Action**: BUY, SELL, or HOLD signal
- **Strength**: How confident the strategy is (0-1)
- **Consensus**: Agreement between strategies (0-1)
- **Size**: Number of units in the position
- **Position P&L**: Current profit/loss

## Real Trading (With API)

To trade real markets:

1. **Get an API Key**
   - OANDA: https://www.oanda.com
   - Alpaca: https://alpaca.markets
   - Polygon: https://polygon.io

2. **Update config.json**
   ```json
   "api": {
     "provider": "oanda",
     "api_key": "YOUR_API_KEY",
     "account_id": "YOUR_ACCOUNT_ID",
     "sandbox": false
   }
   ```

3. **Run the bot**
   ```bash
   python main.py
   ```

## Customization Examples

### Change Trading Pairs
Edit `config.json`:
```json
"pairs": ["EURUSD", "GBPUSD", "USDJPY"]
```

### Adjust Risk Per Trade
```json
"risk_per_trade": 0.03  // Risk 3% per trade
```

### Change Update Interval
```json
"update_interval_seconds": 300  // Check every 5 minutes
```

### Enable Different Strategies
```json
"enabled_strategies": ["moving_average_crossover", "rsi_strategy"]
```

## Common Issues & Solutions

### "ImportError: No module named pandas"
**Solution**: Install requirements
```bash
pip install -r requirements.txt
```

### Bot keeps saying "HOLD"
**Solution**: 
- Increase `lookback_periods` in config.json
- Change timeframe to longer periods
- Check strategy thresholds

### Want to stop the bot?
Press `Ctrl+C` in the terminal. The bot will gracefully shut down.

## Performance Tracking

After running, check:
- **trading_bot.log**: Detailed logs of all actions
- **trades.csv**: CSV file with all executed trades

## Tips for Success

1. **Start Small**: Use sandbox mode first
2. **Test Thoroughly**: Run multiple cycles before live trading
3. **Monitor Closely**: Watch the logs to understand behavior
4. **Adjust Gradually**: Change one parameter at a time
5. **Keep Records**: Review trades.csv regularly

## Next Steps

1. ✅ Run in sandbox mode (default)
2. ✅ Review generated trades in trades.csv
3. ✅ Adjust strategy parameters in config.json
4. ✅ Add API keys when ready for real trading
5. ✅ Monitor performance and optimize

## Getting Help

- Check `README.md` for detailed documentation
- Review log files for error messages
- Verify API credentials and endpoints
- Test with smaller amounts first

---

**Remember**: Always start with sandbox mode and test thoroughly before using real money!
