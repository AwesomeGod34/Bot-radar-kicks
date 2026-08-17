import os
import json
import hashlib
from pathlib import Path

import requests
from bs4 import BeautifulSoup

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATE_FILE = Path("seen.json")

SEARCHES = [
    "Saucony Awesome God",
    '"Awesome God" "Westside Gunn"',
    '"Saucony" "Westside Gunn"',
]

SEARCH_URL = "https://www.google.com/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
}


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )

    response.raise_for_status()


def load_seen():
    if not STATE_FILE.exists():
        return set()

    try:
        return set(json.loads(STATE_FILE.read_text()))
    except Exception:
        return set()


def save_seen(seen):
    STATE_FILE.write_text(json.dumps(sorted(seen), indent=2))


def make_id(url):
    return hashlib.sha256(url.encode()).hexdigest()


def search_google(query):
    response = requests.get(
        SEARCH_URL,
        params={"q": query, "num": 10},
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for link in soup.select("a"):
        href = link.get("href", "")
        title = link.get_text(" ", strip=True)

        if href.startswith("http") and title:
            results.append((title, href))

    return results


def main():
    seen = load_seen()
    new_results = []

    for query in SEARCHES:
        try:
            results = search_google(query)

            for title, url in results:
                if not any(
                    keyword.lower() in (title + " " + url).lower()
                    for keyword in ["saucony", "awesome god", "westside gunn"]
                ):
                    continue

                item_id = make_id(url)

                if item_id in seen:
                    continue

                seen.add(item_id)
                new_results.append((title, url))

        except Exception as error:
            print(f"Erreur recherche '{query}': {error}")

    save_seen(seen)

    if not new_results:
        print("Aucune nouvelle occurrence.")
        return

    for title, url in new_results[:10]:
        message = (
            "🚨 AWESOME GOD RADAR 🚨\n\n"
            f"{title}\n\n"
            f"{url}"
        )

        try:
            send_telegram(message)
            print(f"Alerte envoyée : {url}")
        except Exception as error:
            print(f"Erreur Telegram : {error}")


if __name__ == "__main__":
    main()
