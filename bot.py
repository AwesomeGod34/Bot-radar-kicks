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

BLienteLE_URLS = [
    "https://www.blientele.com/",
    "https://www.blientele.com/collections/all",
    "https://www.blientele.com/search?q=saucony",
    "https://www.blientele.com/search?q=awesome",
    "https://www.blientele.com/search?q=grid+jazz",
]

SEARCHES = [
    '"S71047-5"',
    '"Westside Gunn" "Saucony"',
    '"Westside Gunn" "Grid Jazz 9"',
    '"Grid Jazz 9" "Awesome Gods"',
    '"Grid Jazz 9" "Awesome God"',
    '"Awesome Gods" sneakers',
]

KEYWORDS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "westside gunn",
    "grid jazz 9",
    "saucony",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    )
}


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


def make_id(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def relevant(text):
    text = text.lower()

    return any(
        keyword in text
        for keyword in KEYWORDS
    )


def classify(text):
    text = text.lower()

    if any(word in text for word in [
        "raffle",
        "draw",
        "eql",
        "entry",
        "register",
        "registration",
    ]):
        return "🔥 RAFFLE / INSCRIPTION"

    if any(word in text for word in [
        "add to cart",
        "add-to-cart",
        "buy",
        "available",
        "in stock",
        "purchase",
    ]):
        return "🚨 DISPONIBILITÉ POSSIBLE"

    if any(word in text for word in [
        "release",
        "drop",
        "launch",
        "august 28",
        "28 august",
        "27 august",
        "27 août",
        "28 août",
    ]):
        return "🟠 SORTIE / ANNONCE"

    return "🔵 NOUVELLE INFORMATION"


def check_blientele(seen):
    new_items = []

    print("🛍️ Surveillance directe de Blientele")

    for page_url in BLienteLE_URLS:

        try:
            response = requests.get(
                page_url,
                headers=HEADERS,
                timeout=20,
                allow_redirects=True,
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            page_text = soup.get_text(
                " ",
                strip=True
            )

            # Vérifie le contenu de la page.
            if relevant(page_text):

    # Ignore les pages de recherche sans résultat.
    no_result_phrases = [
        "0 results",
        "0 result",
        "no results",
        "no result",
        "aucun résultat",
        "aucun resultat",
    ]

    page_text_lower = page_text.lower()

    if any(
        phrase in page_text_lower
        for phrase in no_result_phrases
    ):
        continue

    item_id = make_id(
        page_url + "|" + page_text
    )
            

                if item_id not in seen:
                    seen.add(item_id)

                    new_items.append(
                        (
                            "🚨 BLIENTELE",
                            classify(page_text),
                            page_url,
                            page_text[:800],
                        )
                    )

            # Vérifie également les liens présents.
            for link in soup.find_all("a", href=True):

                title = link.get_text(
                    " ",
                    strip=True
                )

                href = link["href"]

                if href.startswith("/"):
                    href = (
                        "https://www.blientele.com"
                        + href
                    )

                combined = title + " " + href

                if not relevant(combined):
                    continue

                item_id = make_id(href)

                if item_id in seen:
                    continue

                seen.add(item_id)

                new_items.append(
                    (
                        "🚨 BLIENTELE",
                        classify(combined),
                        href,
                        title or href,
                    )
                )

        except Exception as error:
            print(
                f"Erreur Blientele {page_url}: "
                f"{error}"
            )

    return new_items


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

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    results = []

    for link in soup.select("a"):

        href = link.get("href", "")
        title = link.get_text(
            " ",
            strip=True
        )

        if not href.startswith("http"):
            continue

        if not title:
            continue

        results.append(
            (title, href)
        )

    return results


def check_web(seen):
    new_items = []

    print("🌐 Surveillance web")

    for query in SEARCHES:

        print("Recherche :", query)

        try:
            results = search_web(query)

            for title, url in results:

                combined = title + " " + url

                if not relevant(combined):
                    continue

                item_id = make_id(url)

                if item_id in seen:
                    continue

                seen.add(item_id)

                new_items.append(
                    (
                        "🌐 WEB",
                        classify(combined),
                        url,
                        title,
                    )
                )

        except Exception as error:
            print(
                f"Erreur recherche "
                f"{query}: {error}"
            )

    return new_items


def main():

    seen = load_seen()

    print("")
    print("🚨 AWESOME GOD RADAR 🚨")
    print(
        "UTC :",
        datetime.now(
            timezone.utc
        ).isoformat()
    )
    print("")

    new_items = []

    # Blientele en priorité.
    new_items.extend(
        check_blientele(seen)
    )

    # Recherche web en complément.
    new_items.extend(
        check_web(seen)
    )

    save_seen(seen)

    if not new_items:
        print(
            "Aucune nouvelle occurrence."
        )
        return

    print(
        f"{len(new_items)} "
        "nouvelle(s) occurrence(s)."
    )

    # Maximum 10 alertes par exécution.
    for source, category, url, details in new_items[:10]:

        message = (
            "🚨 AWESOME GOD RADAR 🚨\n\n"
            f"{source}\n"
            f"{category}\n\n"
            f"{details[:500]}\n\n"
            f"🔗 {url}"
        )

        try:
            send_telegram(message)

            print(
                "Telegram envoyé :",
                url
            )

        except Exception as error:

            print(
                "Erreur Telegram :",
                error
            )


if __name__ == "__main__":
    main()
