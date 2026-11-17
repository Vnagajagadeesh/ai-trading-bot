import os
import json
from datetime import datetime

PORTFOLIO_FILE = "portfolio.json"
STARTING_CAPITAL = 100000.0  # ₹1,00,000 virtual paper money
MAX_POSITION_PCT = 0.20      # Max 20% of capital per stock (₹20,000)
MAX_OPEN_POSITIONS = 4       # Never hold more than 4 stocks at once
MIN_CONFIDENCE = 75          # Ignore AI signals below 75% confidence

def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        portfolio = {
            "cash": STARTING_CAPITAL,
            "positions": {},
            "trade_history": []
        }
        save_portfolio(portfolio)
        return portfolio
    with open(PORTFOLIO_FILE, "r") as f:
        return json.load(f)

def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)

def execute_risk_and_trade(market_snapshot, ai_decision):
    portfolio = load_portfolio()
    ticker = market_snapshot["ticker"]
    current_price = market_snapshot["close_price"]
    action = ai_decision["action"].upper()
    confidence = ai_decision["confidence"]

    print(f"\n[RISK GATEKEEPER] Evaluating {ticker} | Price: ₹{current_price} | AI Signal: {action} ({confidence}%)")

    # 1. Check existing position first (Stop-Loss, Target, or AI SELL signal)
    if ticker in portfolio["positions"]:
        pos = portfolio["positions"][ticker]
        sell_reason = None

        if current_price <= pos["stop_loss"]:
            sell_reason = f"STOP-LOSS HIT (₹{current_price} <= ₹{pos['stop_loss']})"
        elif current_price >= pos["target_price"]:
            sell_reason = f"TARGET HIT (₹{current_price} >= ₹{pos['target_price']})"
        elif action == "SELL" and confidence >= MIN_CONFIDENCE:
            sell_reason = f"AI SELL SIGNAL ({ai_decision['reasoning']})"

        if sell_reason:
            proceeds = round(pos["qty"] * current_price, 2)
            pnl = round(proceeds - (pos["qty"] * pos["entry_price"]), 2)
            portfolio["cash"] = round(portfolio["cash"] + proceeds, 2)
            del portfolio["positions"][ticker]

            portfolio["trade_history"].append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "ticker": ticker,
                "type": "SELL",
                "qty": pos["qty"],
                "price": current_price,
                "pnl": pnl,
                "reason": sell_reason
            })
            save_portfolio(portfolio)
            print(f"  -> [EXECUTED SELL] Sold {pos['qty']} shares of {ticker} @ ₹{current_price} | P&L: ₹{pnl} | Reason: {sell_reason}")
            return
        else:
            print(f"  -> [HOLDING] Keeping existing {pos['qty']} shares of {ticker} (Entry: ₹{pos['entry_price']}, SL: ₹{pos['stop_loss']}, Target: ₹{pos['target_price']})")
            return

    # 2. Evaluate new BUY signal
    if action == "BUY":
        if confidence < MIN_CONFIDENCE:
            print(f"  -> [REJECTED] Confidence {confidence}% is below minimum {MIN_CONFIDENCE}%.")
            return
        if len(portfolio["positions"]) >= MAX_OPEN_POSITIONS:
            print(f"  -> [REJECTED] Max open positions ({MAX_OPEN_POSITIONS}) already reached.")
            return

        budget = min(portfolio["cash"], STARTING_CAPITAL * MAX_POSITION_PCT)
        qty = int(budget // current_price)

        if qty <= 0:
            print(f"  -> [REJECTED] Insufficient cash (₹{portfolio['cash']}) to buy 1 share at ₹{current_price}.")
            return

        stop_loss = ai_decision["stop_loss"] if ai_decision["stop_loss"] > 0 else round(current_price * 0.97, 2)
        target_price = ai_decision["target_price"] if ai_decision["target_price"] > current_price else round(current_price * 1.06, 2)

        cost = round(qty * current_price, 2)
        portfolio["cash"] = round(portfolio["cash"] - cost, 2)
        portfolio["positions"][ticker] = {
            "qty": qty,
            "entry_price": current_price,
            "stop_loss": stop_loss,
            "target_price": target_price,
            "entry_date": market_snapshot["date"]
        }
        portfolio["trade_history"].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": ticker,
            "type": "BUY",
            "qty": qty,
            "price": current_price,
            "pnl": 0.0,
            "reason": ai_decision["reasoning"]
        })
        save_portfolio(portfolio)
        print(f"  -> [EXECUTED BUY] Bought {qty} shares of {ticker} @ ₹{current_price} (Total: ₹{cost}) | SL: ₹{stop_loss} | Target: ₹{target_price}")
    else:
        print(f"  -> [NO TRADE] Signal is {action} and no open position exists for {ticker}.")