import os
import requests
from dotenv import load_dotenv

ENV_MODE = os.getenv("ENV_MODE", "development")
ENV_FILE = f".env.{ENV_MODE}"
load_dotenv(ENV_FILE, override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message="", title="", href="", company=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    if not message and title and href and company:
        message = f"<b>{title}</b>\n<i>{company}</i>\n<a href='{href}'>Apply Now</a>"

    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        res = requests.post(url, data=payload)
        if res.status_code != 200:
            print(f"⚠️ Telegram error: {res.text}")
    except Exception as e:
        print(f"⚠️ <b>Failed to send Telegram message:</b>\n{e}")
