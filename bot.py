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
WESTSIDE_ALERTS_FILE = Path("westside_alerts.json")

BASE_URL = "https://www.blientele.com"

# --------------------------------------------------
# BLIENTELE : surveillance prioritaire
# --------------------------------------------------

BLientele_URLS = [
    f"{BASE_URL}/",
    f"{BASE_URL}/collections/all",
    f"{BASE_URL}/products.json?limit=250",
    f"{BASE_URL}/collections/all/products.json?limit=250",
    f"{BASE_URL}/sitemap_products_1.xml",
    f"{BASE_URL}/search?q=saucony",
    f"{BASE_URL}/search?q=awesome",
    f"{BASE_URL}/search?q=grid+jazz",
]

# --------------------------------------------------
# RECHERCHES WEB : filet de sécurité
# --------------------------------------------------

SEARCHES = [
    '"S71047-5"',
    '"S71047-5" Saucony',
    '"Westside Gunn" "Saucony"',
    '"Westside Gunn" "Grid Jazz 9"',
    '"Grid Jazz 9" "Awesome Gods"',
    '"Grid Jazz 9" "Awesome God"',
    '"Awesome Gods" sneakers',
    '"Awesome Gods" Blientele',
    '"Awesome Gods" release',
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


# --------------------------------------------------
# TELEGRAM
# --------------------------------------------------

def send_telegram(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendMessage"
    )

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


# --------------------------------------------------
# MEMOIRE PRINCIPALE
# --------------------------------------------------

def load_seen():
    if not STATE_FILE.exists():
        return {}

    try:
        data = json.loads(
            STATE_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return {
                item: ""
                for item in data
            }

        return data

    except Exception:
        return {}


def save_seen(seen):
    STATE_FILE.write_text(
        json.dumps(
            seen,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def make_id(value):
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


# --------------------------------------------------
# MEMOIRE WESTSIDE
# --------------------------------------------------

def load_westside_alerts():

    if not WESTSIDE_ALERTS_FILE.exists():
        return []

    try:
        data = json.loads(
            WESTSIDE_ALERTS_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except Exception as error:

        print(
            "⚠️ Erreur lecture Westside alerts :",
            error
        )

    return []


def save_westside_alerts(alerts):

    WESTSIDE_ALERTS_FILE.write_text(
        json.dumps(
            alerts,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# --------------------------------------------------
# FILTRES
# --------------------------------------------------

def relevant(text):

    text = text.lower()

    return any(
        keyword in text
        for keyword in KEYWORDS
    )


def has_no_results(text):

    text = text.lower()

    phrases = [
        "0 results",
        "0 result",
        "no results",
        "no result",
        "aucun résultat",
        "aucun resultat",
        "nothing found",
        "no products found",
    ]

    return any(
        phrase in text
        for phrase in phrases
    )


def classify(text):

    text = text.lower()

    if any(word in text for word in [
        "add to cart",
        "add-to-cart",
        "buy now",
        "buy",
        "available",
        "in stock",
        "purchase",
    ]):
        return "🚨 DISPONIBILITÉ POSSIBLE"

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
        "release",
        "drop",
        "launch",
        "available",
        "august 28",
        "28 august",
        "27 august",
        "27 août",
        "28 août",
    ]):
        return "🟠 SORTIE / ANNONCE"

    return "🔵 NOUVELLE INFORMATION"


# --------------------------------------------------
# WESTSIDE GUNN
# --------------------------------------------------

def send_westside_alerts():

    alerts = load_westside_alerts()

    if not alerts:
        print("")
        print(
            "👤 WESTSIDE GUNN : "
            "aucun nouveau signal Telegram."
        )
        return

    print("")
    print(
        "👤 WESTSIDE GUNN :",
        len(alerts),
        "signal(s) en attente."
    )

    remaining = []

    for alert in alerts:

        try:

            priority = alert.get(
                "priority",
                "🟡 À SURVEILLER"
            )

            terms = alert.get(
                "terms",
                []
            )

            excerpt = alert.get(
                "excerpt",
                ""
            )

            url = alert.get(
                "url",
                "https://x.com/WESTSIDEGUNN"
            )

            post_id = alert.get(
                "post_id",
                ""
            )

            detected_at = alert.get(
                "detected_at",
                ""
            )

            terms_text = ", ".join(
                terms
            )

            message = (
                "🚨 AWESOME GOD RADAR 🚨\n\n"
                "👤 WESTSIDE GUNN\n"
                f"{priority}\n\n"
                "🎯 Référence : S71047-5\n"
                "👟 Sujet : Awesome Gods / Saucony\n\n"
            )

            if terms_text:
                message += (
                    f"🔎 Détection : "
                    f"{terms_text}\n\n"
                )

            if excerpt:
                message += (
                    "📝 Contenu détecté :\n"
                    f"{excerpt[:900]}\n\n"
                )

            if post_id:
                message += (
                    f"🆔 Post X : {post_id}\n"
                )

            if detected_at:
                message += (
                    f"🕐 Détection : "
                    f"{detected_at}\n"
                )

            message += (
                "\n🔗 Source :\n"
                f"{url}"
            )

            send_telegram(message)

            print(
                "📲 Alerte Westside envoyée :",
                post_id or url
            )

        except Exception as error:

            print(
                "❌ Erreur envoi Westside :",
                error
            )

            # On conserve l'alerte pour un prochain passage.
            remaining.append(alert)

    save_westside_alerts(
        remaining
    )

    if remaining:
        print(
            "⚠️ Alertes Westside conservées :",
            len(remaining)
        )
    else:
        print(
            "✅ File Westside vidée."
        )


# --------------------------------------------------
# BLIENTELE
# --------------------------------------------------

def check_blientele(seen):

    new_items = []

    print("")
    print("🔥 BLIENTELE EARLY-DROP SCAN")
    print("")

    for page_url in BLientele_URLS:

        try:

            response = requests.get(
                page_url,
                headers=HEADERS,
                timeout=25,
                allow_redirects=True,
            )

            print(
                response.status_code,
                page_url
            )

            if response.status_code != 200:
                continue

            content_type = response.headers.get(
                "content-type",
                ""
            ).lower()

            # --------------------------------------
            # CAS JSON
            # --------------------------------------

            if "json" in content_type:

                try:
                    data = response.json()
                except Exception:
                    continue

                products = data.get(
                    "products",
                    []
                )

                for product in products:

                    title = product.get(
                        "title",
                        ""
                    )

                    handle = product.get(
                        "handle",
                        ""
                    )

                    product_id = str(
                        product.get(
                            "id",
                            handle
                        )
                    )

                    product_url = (
                        f"{BASE_URL}/products/"
                        f"{handle}"
                    )

                    variants = product.get(
                        "variants",
                        []
                    )

                    variant_text = " ".join(
                        str(v)
                        for v in variants
                    )

                    combined = (
                        title
                        + " "
                        + handle
                        + " "
                        + variant_text
                    )

                    if not relevant(combined):
                        continue

                    item_id = (
                        "blientele-product-"
                        + product_id
                    )

                    fingerprint = make_id(
                        json.dumps(
                            {
                                "title": title,
                                "handle": handle,
                                "variants": variants,
                            },
                            sort_keys=True,
                            default=str,
                        )
                    )

                    previous = seen.get(
                        item_id
                    )

                    if previous != fingerprint:

                        seen[item_id] = fingerprint

                        new_items.append(
                            (
                                "🚨 BLIENTELE EARLY DROP",
                                classify(combined),
                                product_url,
                                title,
                            )
                        )

                continue

            # --------------------------------------
            # CAS HTML / XML
            # --------------------------------------

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            page_text = soup.get_text(
                " ",
                strip=True
            )

            if has_no_results(page_text):
                print(
                    "Recherche vide :",
                    page_url
                )
                continue

            if relevant(page_text):

                fingerprint = make_id(
                    page_text
                )

                item_id = (
                    "blientele-page-"
                    + make_id(page_url)
                )

                previous = seen.get(
                    item_id
                )

                if previous != fingerprint:

                    seen[item_id] = fingerprint

                    new_items.append(
                        (
                            "🚨 BLIENTELE EARLY DROP",
                            classify(page_text),
                            page_url,
                            page_text[:700],
                        )
                    )

            for link in soup.find_all(
                "a",
                href=True
            ):

                title = link.get_text(
                    " ",
                    strip=True
                )

                href = link["href"]

                if href.startswith("/"):
                    href = (
                        BASE_URL
                        + href
                    )

                combined = (
                    title
                    + " "
                    + href
                )

                if not relevant(combined):
                    continue

                if "/products/" not in href:
                    continue

                item_id = (
                    "blientele-link-"
                    + make_id(href)
                )

                if item_id in seen:
                    continue

                seen[item_id] = "detected"

                new_items.append(
                    (
                        "🚨 BLIENTELE EARLY DROP",
                        classify(combined),
                        href,
                        title or href,
                    )
                )

        except Exception as error:

            print(
                "Erreur Blientele :",
                page_url,
                error
            )

    return new_items


# --------------------------------------------------
# RECHERCHE WEB
# --------------------------------------------------

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

        href = link.get(
            "href",
            ""
        )

        title = link.get_text(
            " ",
            strip=True
        )

        if not href.startswith(
            "http"
        ):
            continue

        if not title:
            continue

        results.append(
            (
                title,
                href
            )
        )

    return results


def check_web(seen):

    new_items = []

    print("")
    print("🌐 WEB RADAR")
    print("")

    for query in SEARCHES:

        print(
            "Recherche :",
            query
        )

        try:

            results = search_web(
                query
            )

            for title, url in results:

                combined = (
                    title
                    + " "
                    + url
                )

                if not relevant(
                    combined
                ):
                    continue

                item_id = (
                    "web-"
                    + make_id(url)
                )

                if item_id in seen:
                    continue

                seen[item_id] = "detected"

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
                "Erreur recherche :",
                query,
                error
            )

    return new_items


# --------------------------------------------------
# PROGRAMME PRINCIPAL
# --------------------------------------------------

def main():

    seen = load_seen()

    print("")
    print("==============================")
    print("🚨 AWESOME GOD RADAR 🚨")
    print("==============================")

    print(
        "UTC :",
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    print("")

    # ------------------------------------------------
    # WESTSIDE GUNN EN PREMIER
    # ------------------------------------------------

    send_westside_alerts()

    # ------------------------------------------------
    # BLIENTELE
    # ------------------------------------------------

    new_items = []

    new_items.extend(
        check_blientele(
            seen
        )
    )

    # ------------------------------------------------
    # WEB
    # ------------------------------------------------

    new_items.extend(
        check_web(
            seen
        )
    )

    save_seen(seen)

    if not new_items:

        print("")
        print(
            "✅ Aucune nouvelle occurrence."
        )
        return

    print("")
    print(
        "🚨",
        len(new_items),
        "nouvelle(s) occurrence(s)"
    )

    # Maximum 10 alertes par passage.
    for (
        source,
        category,
        url,
        details
    ) in new_items[:10]:

        message = (
            "🚨 AWESOME GOD RADAR 🚨\n\n"
            f"{source}\n"
            f"{category}\n\n"
            f"{details[:600]}\n\n"
            f"🔗 {url}"
        )

        try:

            send_telegram(
                message
            )

            print(
                "📲 Telegram envoyé :",
                url
            )

        except Exception as error:

            print(
                "❌ Erreur Telegram :",
                error
            )


if __name__ == "__main__":
    main()
