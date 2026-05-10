import os
import requests
from config import Config
# Test API connection for configured provider (OANDA, Alpaca, Polygon)
def test_api_connection():
    config = Config()
    provider = config.get('api.provider')
    api_key = config.get('api.api_key')
    
    print(f"Testing connection for provider: {provider}")
    
    if api_key == "your_api_key_here" or not api_key:
        print("❌ Error: API key not found. Please ensure you have created a .env file with your keys.")
        return

    if provider == "oanda":
        account_id = config.get('api.account_id')
        url = "https://api-fxpractice.oanda.com/v3/accounts" if config.get('api.sandbox') else "https://api-fxtrade.oanda.com/v3/accounts"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print("✅ OANDA Connection Successful!")
            else:
                print(f"❌ OANDA Connection Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error connecting to OANDA: {e}")

    elif provider == "alpaca":
        api_secret = config.get('api.api_secret')
        base_url = "https://paper-api.alpaca.markets" if config.get('api.sandbox') else "https://api.alpaca.markets"
        headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret
        }
        try:
            response = requests.get(f"{base_url}/v2/account", headers=headers)
            if response.status_code == 200:
                print("✅ Alpaca Connection Successful!")
            else:
                print(f"❌ Alpaca Connection Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Error connecting to Alpaca: {e}")

    else:
        print(f"Test for provider {provider} is not implemented yet, but your API key was loaded: {api_key[:5]}...")

if __name__ == "__main__":
    test_api_connection()
