import json
import requests
import pandas as pd
from typing import Dict
from strategies.base_strategy import BaseStrategy
from config import Config
import logging

class LlamaStrategy(BaseStrategy):
    """Llama-based prediction strategy via Ollama API"""
    
    def __init__(self, config: Config, model: str = "llama3", host: str = "http://127.0.0.1:11434"):
        super().__init__("llama_strategy", config)
        self.model = model
        self.host = host
    
    def calculate_signal(self, df: pd.DataFrame) -> Dict:
        """Calculate signal using Llama prediction"""
        if not self.validate_data(df):
            return {"action": "HOLD", "strength": 0, "parameters": {}}
        
        # Get the latest 10 candles to keep prompt size manageable
        recent_data = df.tail(10).to_dict('records')
        
        prompt = (
            "You are a trading assistant. Below is the recent candlestick data for an asset. "
            "Analyze the action and give a single prediction of BUY, SELL, or HOLD. "
            "Also provide a confidence score from 0.0 to 1.0.\n\n"
            f"Data: {json.dumps(recent_data, indent=2)}\n\n"
            "Format your response as a valid JSON object EXACTLY like this:\n"
            '{"action": "BUY", "confidence": 0.85}'
        )
        
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=15
            )
            response.raise_for_status()
            result = response.json()
            response_text = result.get('response', '{}')
            
            # Parse response
            data = json.loads(response_text)
            action = data.get("action", "HOLD").upper()
            confidence = float(data.get("confidence", 0.0))
            
            if action not in ["BUY", "SELL", "HOLD"]:
                action = "HOLD"
                
            return {
                "action": action, 
                "strength": confidence, 
                "parameters": {"model": self.model}
            }
            
        except Exception as e:
            self.logger.error(f"Llama prediction error: {str(e)}")
            return {"action": "HOLD", "strength": 0, "parameters": {"error": str(e)}}
