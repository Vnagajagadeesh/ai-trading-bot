import socket
socket.setdefaulttimeout(10)  # Prevents any network request from freezing

import yfinance as yf
import pandas as pd
import pandas_ta as ta

def get_stock_indicators(ticker_symbol):
    print(f"Fetching market data & news for {ticker_symbol}...")
    
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="6mo", interval="1d")
    
    if df.empty:
        print(f"Error: No data returned for {ticker_symbol}.")
        return None

    # Calculate Technical Indicators
    df["RSI_14"] = ta.rsi(df["Close"], length=14)
    df["EMA_20"] = ta.ema(df["Close"], length=20)
    df["EMA_50"] = ta.ema(df["Close"], length=50)

    latest = df.iloc[-1]

    # Fetch top 3 recent news headlines
    headlines = []
    try:
        raw_news = stock.news or []
        for item in raw_news[:3]:
            content = item.get("content", item)
            title = content.get("title")
            if title:
                headlines.append(title)
    except Exception:
        pass

    summary = {
        "ticker": ticker_symbol,
        "date": str(latest.name.date()),
        "close_price": round(float(latest["Close"]), 2),
        "rsi_14": round(float(latest["RSI_14"]), 2),
        "ema_20": round(float(latest["EMA_20"]), 2),
        "ema_50": round(float(latest["EMA_50"]), 2),
        "volume": int(latest["Volume"]),
        "recent_news": headlines if headlines else ["No major recent headlines"]
    }
    return summary

if __name__ == "__main__":
    data = get_stock_indicators("RELIANCE.NS")
    if data:
        print(data)