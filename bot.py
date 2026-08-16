import os
import requests
from bs4 import BeautifulSoup

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False
        },
        timeout=20
    )

# Premier test : vérifier que Telegram fonctionne
send_telegram(
    "🚨 AWESOME GOD RADAR 🚨\n\n"
    "Le radar est bien connecté à Telegram !"
)
