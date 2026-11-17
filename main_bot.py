import time
from datetime import datetime
from market_data import get_stock_indicators
from ai_analyst import analyze_trade_signal
from paper_trader import execute_risk_and_trade, load_portfolio
from notifier import send_telegram_alert

# Watchlist of liquid NSE large-cap stocks
WATCHLIST = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS"
]

def run_trading_cycle():
    print("=" * 55)
    print("STARTING AUTONOMOUS AI SWING-TRADING CYCLE")
    print("=" * 55)

    scan_logs = []

    for ticker in WATCHLIST:
        try:
            # 1. Agent 1: Fetch data, indicators & news
            snapshot = get_stock_indicators(ticker)
            if not snapshot:
                continue

            # 2. Agent 2: AI Analyst decision
            decision = analyze_trade_signal(snapshot)
            print(f"AI Reasoning ({ticker}): {decision['reasoning']}")

            # 3. Agent 3: Risk Gatekeeper & Paper Execution
            execute_risk_and_trade(snapshot, decision)

            scan_logs.append(f"• *{ticker}* (₹{snapshot['close_price']}): {decision['action']} ({decision['confidence']}%)")
            time.sleep(1)

        except Exception as e:
            print(f"[ERROR] Failed processing {ticker}: {e}")
            scan_logs.append(f"• *{ticker}*: Error during scan")

    # Build final portfolio summary
    portfolio = load_portfolio()
    today_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    
    summary_lines = [
        f"📊 *NSE AI Trading Bot Report*",
        f"🕒 {today_str}\n",
        "*Watchlist Signals:*",
        *scan_logs,
        f"\n💰 *Available Cash:* ₹{portfolio['cash']:,.2f}",
        f"📂 *Open Positions:* {len(portfolio['positions'])}"
    ]

    for sym, pos in portfolio["positions"].items():
        summary_lines.append(
            f"  └ {sym}: {pos['qty']} qty @ ₹{pos['entry_price']} (SL: ₹{pos['stop_loss']} | Tgt: ₹{pos['target_price']})"
        )

    report = "\n".join(summary_lines)
    print("\n" + "=" * 55)
    print(report.replace("*", ""))
    print("=" * 55)

    # Send report to your phone via Telegram
    send_telegram_alert(report)

if __name__ == "__main__":
    run_trading_cycle()