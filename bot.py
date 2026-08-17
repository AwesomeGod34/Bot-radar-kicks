import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATE_FILE = Path("seen.json")

SEARCHES = [
    '"S71047-5"',
    '"Westside Gunn" "Saucony"',
    '"Grid Jazz 9" "Awesome Gods"',
    '"Grid Jazz 9" "Awesome God"',
    '"Westside Gunn" "Grid Jazz 9"',
    '"Awesome Gods" sneakers',
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    )
}

KEYWORDS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "westside gunn",
    "grid jazz 9",
]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
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
    STATE_FILE.write_text(
        json.dumps(sorted(seen), indent=2)
    )


def make_id(url):
    return hashlib.sha256(url.encode()).hexdigest()


def search_web(query):
    response = requests.get(
        "https://www.google.com/search",
        params={
            "q": query,
            "num": 10,
        },
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for link in soup.select("a"):
        href = link.get("href", "")
        title = link.get_text(" ", strip=True)

        if not href.startswith("http"):
            continue

        if not title:
            continue

        results.append((title, href))

    return results


def relevant(title, url):
    text = (title + " " + url).lower()

    return any(
        keyword in text
        for keyword in KEYWORDS
    )


def classify(title, url):
    text = (title + " " + url).lower()

    if any(word in text for word in [
        "raffle",
        "draw",
        "eql",
        "entry",
        "register"
    ]):
        return "🔥 RAFFLE / INSCRIPTION"

    if any(word in text for word in [
        "buy",
        "shop",
        "available",
        "in stock",
        "preorder",
        "pre-order"
    ]):
        return "🚨 DISPONIBILITÉ POSSIBLE"

    if any(word in text for word in [
        "release",
        "drop",
        "launch",
        "august 28",
        "28 august"
    ]):
        return "🟠 SORTIE / ANNONCE"

    return "🔵 NOUVELLE INFORMATION"


def main():
    seen = load_seen()
    new_results = []

    print("🔎 AWESOME GOD RADAR")
    print("Heure UTC :", datetime.now(timezone.utc).isoformat())

    for query in SEARCHES:
        print("Recherche :", query)

        try:
            results = search_web(query)

            for title, url in results:

                if not relevant(title, url):
                    continue

                item_id = make_id(url)

                if item_id in seen:
                    continue

                seen.add(item_id)

                category = classify(title, url)

                new_results.append(
                    (category, title, url)
                )

        except Exception as error:
            print(
                f"Erreur pendant la recherche "
                f"'{query}': {error}"
            )

    save_seen(seen)

    if not new_results:
        print("Aucune nouvelle occurrence.")
        return

    for category, title, url in new_results[:10]:

        message = (
            "🚨 AWESOME GOD RADAR 🚨\n\n"
            f"{category}\n\n"
            f"{title}\n\n"
            f"{url}"
        )

        try:
            send_telegram(message)
            print("Alerte Telegram envoyée :", url)

        except Exception as error:
            print(
                "Erreur Telegram :",
                error
            )


if __name__ == "__main__":
    main()
