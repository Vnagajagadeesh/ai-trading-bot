import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from market_data import get_stock_indicators

# Load GEMINI_API_KEY from .env
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Fast, reliable model order to avoid 503 traffic delays
MODELS_TO_TRY = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash"
]

def analyze_trade_signal(market_snapshot):
    news_text = "\n    ".join(f"- {h}" for h in market_snapshot.get("recent_news", []))

    prompt = f"""
    You are an expert NSE swing-trading analyst. Analyze the following technical and news data for {market_snapshot['ticker']}:
    
    - Date: {market_snapshot['date']}
    - Close Price: ₹{market_snapshot['close_price']}
    - 14-Day RSI: {market_snapshot['rsi_14']} (Below 30 = oversold, Above 70 = overbought)
    - 20-Day EMA: ₹{market_snapshot['ema_20']}
    - 50-Day EMA: ₹{market_snapshot['ema_50']}
    - Volume: {market_snapshot['volume']}
    - Recent News Headlines:
    {news_text}

    Rules:
    1. Only recommend BUY if the trend is bullish (Close > EMA_20 > EMA_50 or strong oversold bounce), RSI is not overbought (less than 68), AND there is no severe negative news.
    2. Recommend SELL if trend breaks down (Close < EMA_20 < EMA_50), RSI is heavily overbought (greater than 75), or major negative news threatens the stock.
    3. Otherwise recommend HOLD.
    4. Always set a realistic stop_loss (2% to 4% below entry for BUY) and target_price (4% to 8% above entry for BUY).

    Respond ONLY in valid JSON with this exact structure:
    {{
        "ticker": "{market_snapshot['ticker']}",
        "action": "BUY or SELL or HOLD",
        "confidence": 0 to 100,
        "stop_loss": 0.0,
        "target_price": 0.0,
        "reasoning": "1-2 concise sentences combining technicals and news sentiment"
    }}
    """

    for model_name in MODELS_TO_TRY:
        try:
            print(f"Querying {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Warning: {model_name} unavailable ({e}). Trying next model...")
            time.sleep(1)

    raise RuntimeError("All Gemini models are currently unavailable. Please try again in a minute.")

if __name__ == "__main__":
    snapshot = get_stock_indicators("RELIANCE.NS")
    if snapshot:
        print("\nAsking AI Analyst for decision...")
        decision = analyze_trade_signal(snapshot)
        print(json.dumps(decision, indent=2))