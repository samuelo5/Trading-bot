import os
from config import Config

def test_dotenv_loading():
    # 1. Create a temporary .env file for testing
    env_content = "OANDA_API_KEY=test_oanda_key\nOANDA_ACCOUNT_ID=test_oanda_id"
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("Created temporary .env for testing...")
    
    try:
        # 2. Initialize Config
        config = Config()
        
        # 3. Check values
        api_key = config.get('api.api_key')
        account_id = config.get('api.account_id')
        
        print(f"Loaded API Key: {api_key}")
        print(f"Loaded Account ID: {account_id}")
        
        assert api_key == "test_oanda_key", f"Expected 'test_oanda_key', got '{api_key}'"
        assert account_id == "test_oanda_id", f"Expected 'test_oanda_id', got '{account_id}'"
        
        print("\n✅ Verification SUCCESS: Environment variables correctly override config.json")
        
    finally:
        # 4. Clean up
        if os.path.exists(".env"):
            os.remove(".env")
            print("Cleaned up temporary .env")

if __name__ == "__main__":
    test_dotenv_loading()
