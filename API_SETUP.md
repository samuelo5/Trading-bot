# API Integration Guide

This guide explains how to set up the trading bot with real broker APIs.

## Supported Brokers & Providers

### 1. OANDA (Recommended for Forex)

Best for: Forex trading, multiple currency pairs

**Setup Steps:**

1. **Create Account**
   - Go to https://www.oanda.com
   - Sign up and create a trading account
   - Create a v20 API token

2. **Get API Credentials**
   - Log in to OANDA account
   - Go to Manage API Access
   - Create a new Personal Access Token
   - Copy your Account ID (e.g., 101-001-12345678-001)

3. **Update config.json**
   ```json
   "api": {
     "provider": "oanda",
     "api_key": "your_v20_token_here",
     "account_id": "101-001-12345678-001",
     "sandbox": false
   }
   ```

4. **Test Connection**
   ```bash
   python main.py
   ```

**OANDA Features:**
- 24/5 forex trading
- ~100 currency pairs
- Low spreads
- Reliable execution
- Real-time data

---

### 2. Alpaca (Best for US Stocks)

Best for: US stocks, ETFs, options

**Setup Steps:**

1. **Create Account**
   - Go to https://alpaca.markets
   - Sign up for a free account
   - Verify email and phone

2. **Get API Credentials**
   - Dashboard → Settings → API Keys
   - Generate API Key
   - Copy API Key and Secret Key

3. **Update config.json**
   ```json
   "api": {
     "provider": "alpaca",
     "api_key": "your_api_key_here",
     "api_secret": "your_secret_key_here",
     "base_url": "https://paper-api.alpaca.markets",
     "sandbox": true
   }
   ```

4. **Enable Stocks**
   ```json
   "trading": {
     "enable_stocks": true,
     "enable_forex": false
   }
   ```

**Alpaca Features:**
- US stock trading
- Commission-free
- Paper trading (sandbox)
- Real-time quotes
- Technical analysis indicators

---

### 3. Polygon.io (For Stocks & Crypto Data)

Best for: Stocks, crypto data, technical analysis

**Setup Steps:**

1. **Create Account**
   - Go to https://polygon.io
   - Sign up and choose plan
   - Verify email

2. **Get API Key**
   - Dashboard → API Keys
   - Copy your API key

3. **Update config.json**
   ```json
   "api": {
     "provider": "polygon",
     "api_key": "your_polygon_api_key",
     "sandbox": true
   }
   ```

**Polygon Features:**
- Stock market data
- Cryptocurrency data
- Real-time quotes
- Historical data
- News and events

---

## Environment Setup

### Using .env File (Secure)

Instead of storing keys in config.json:

1. **Create .env file**
   ```
   OANDA_API_KEY=your_api_key
   OANDA_ACCOUNT_ID=your_account_id
   ALPACA_API_KEY=your_api_key
   ALPACA_SECRET_KEY=your_secret_key
   ```

2. **Load in config.py**
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   api_key = os.getenv('OANDA_API_KEY')
   ```

3. **Add to .gitignore**
   ```
   .env
   ```

---

## Testing Your Setup

### Step 1: Verify Credentials
```python
# test_connection.py
from market_data import MarketDataFetcher
from config import Config

config = Config()
fetcher = MarketDataFetcher(config)

# Get account info
account = fetcher.get_account_info()
print(f"Account Balance: {account['balance']}")
```

### Step 2: Test Data Fetching
```python
# Get historical data
df = fetcher.get_candles("EURUSD", "1h", limit=10)
print(df)
```

### Step 3: Test Quotes
```python
# Get current quotes
quotes = fetcher.get_forex_quotes(["EURUSD", "GBPUSD"])
for pair, quote in quotes.items():
    print(f"{pair}: {quote['mid']}")
```

---

## Sandbox vs Live Trading

### Sandbox Mode (Testing)
```json
"sandbox": true
```
- Paper trading with virtual money
- No real money risk
- Same API interface
- Perfect for testing strategies

### Live Trading (Real Money)
```json
"sandbox": false
```
- REAL MONEY involved
- Actual trades executed
- Fees and commissions apply
- USE EXTREME CAUTION

**Always test in sandbox first!**

---

## API Rate Limits

Each provider has rate limits:

| Provider | Rate Limit | Recommended Interval |
|----------|-----------|---------------------|
| OANDA | 50 requests/second | 1-5 minutes |
| Alpaca | 720 requests/minute | 10-60 seconds |
| Polygon | 5 requests/minute (Free) | 10-14 seconds |

Adjust `update_interval_seconds` accordingly.

---

## Troubleshooting

### Authentication Errors
```
Error: Invalid API Key
```
**Solutions:**
- Verify API key in config.json
- Check API key hasn't expired
- Ensure correct account ID
- Recreate API key if needed

### Connection Errors
```
Error: Connection refused / Timeout
```
**Solutions:**
- Check internet connection
- Verify API endpoint is correct
- Check firewall settings
- Try again later (servers may be down)

### No Data Available
```
Warning: Insufficient data for EURUSD
```
**Solutions:**
- Use longer timeframes (1h instead of 1m)
- Ensure pair is supported by provider
- Wait for data to accumulate
- Check market hours

### Permission Denied
```
Error: Account doesn't have permission
```
**Solutions:**
- Check account type (live vs paper)
- Verify API permissions
- Ensure account is funded (for live trading)
- Create new API token with correct permissions

---

## Security Best Practices

1. **Never commit API keys**
   ```bash
   git add .gitignore  # Make sure .env is ignored
   ```

2. **Use environment variables**
   ```bash
   export OANDA_API_KEY="your_key"
   ```

3. **Restrict API key permissions**
   - Only enable necessary scopes
   - Disable if not in use

4. **Rotate keys regularly**
   - Update API keys every 3-6 months
   - Create new keys before rotating

5. **Monitor usage**
   - Check API call history
   - Alert on unusual activity
   - Review logs regularly

---

## Advanced Configuration

### Multiple Providers
```json
"primary_provider": "oanda",
"fallback_provider": "polygon"
```

### Custom Endpoints
```json
"api": {
  "provider": "oanda",
  "base_url": "https://custom-api.example.com",
  "api_key": "key"
}
```

### Proxy Settings
```python
# In market_data.py
proxies = {
    "http": "http://proxy.example.com:8080",
    "https": "https://proxy.example.com:8080",
}
requests.get(url, proxies=proxies)
```

---

## Support & Resources

- **OANDA Help**: https://help.oanda.com
- **Alpaca Docs**: https://docs.alpaca.markets
- **Polygon Docs**: https://polygon.io/docs
- **API Status**: https://status.oanda.com

---

## Next Steps

1. ✅ Choose a broker
2. ✅ Create account and get API key
3. ✅ Update config.json
4. ✅ Test in sandbox mode
5. ✅ Start trading!

**⚠️ IMPORTANT**: Always test thoroughly before trading with real money!
