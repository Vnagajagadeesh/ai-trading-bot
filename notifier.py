import os
import ssl
import urllib.request
import urllib.parse
import json
from dotenv import load_dotenv

load_dotenv()

def send_telegram_alert(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("[NOTIFIER] Telegram credentials missing in .env; skipping alert.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }).encode("utf-8")

    # Bypass local Windows SSL certificate chain issues
    ssl_context = ssl._create_unverified_context()

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            if result.get("ok"):
                print("[NOTIFIER] Telegram summary sent successfully!")
    except Exception as e:
        print(f"[NOTIFIER] Failed to send Telegram message: {e}")

if __name__ == "__main__":
    send_telegram_alert("🚀 *Test Alert:* Your NSE AI Trading Bot is connected!")