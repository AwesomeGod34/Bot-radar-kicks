import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


MEMORY_FILE = Path("westside_seen.json")
ALERTS_FILE = Path("westside_alerts.json")

X_URL = "https://x.com/WESTSIDEGUNN"
INSTAGRAM_URL = "https://www.instagram.com/westsidegunn/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

STRONG_TERMS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "grid jazz 9",
]

IMPORTANT_TERMS = [
    "saucony",
    "sauconyorigs",
]

ACTION_TERMS = [
    "release",
    "release details",
    "release date",
    "dropping",
    "available",
    "available now",
    "shop now",
    "link",
    "8/28",
    "8.28",
    "28 août",
]

IGNORE_TERMS = [
    "out now",
]


# --------------------------------------------------
# OUTILS
# --------------------------------------------------

def normalise(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_memory():

    if not MEMORY_FILE.exists():
        return {
            "initialized": False,
            "posts": []
        }

    try:

        data = json.loads(
            MEMORY_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, dict):
            return data

    except Exception as error:

        print(
            f"⚠️ Erreur mémoire : {error}"
        )

    return {
        "initialized": False,
        "posts": []
    }


def save_memory(memory):

    MEMORY_FILE.write_text(
        json.dumps(
            memory,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def load_alerts():

    if not ALERTS_FILE.exists():
        return []

    try:

        data = json.loads(
            ALERTS_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except Exception as error:

        print(
            f"⚠️ Erreur fichier alertes : {error}"
        )

    return []


def save_alerts(alerts):

    ALERTS_FILE.write_text(
        json.dumps(
            alerts,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def content_id(text):

    return hashlib.sha256(
        normalise(text).encode("utf-8")
    ).hexdigest()


# --------------------------------------------------
# DETECTION
# --------------------------------------------------

def find_terms(text):

    matches = []

    for term in STRONG_TERMS:

        if term in text:
            matches.append(term)

    for term in IMPORTANT_TERMS:

        if term in text:
            matches.append(term)

    for term in ACTION_TERMS:

        if term in text:
            matches.append(term)

    return list(
        dict.fromkeys(matches)
    )


def is_relevant(text):

    text = normalise(text)

    if "s71047-5" in text:
        return True

    if "awesome gods" in text:
        return True

    if "grid jazz 9" in text:
        return True

    saucony = (
        "saucony" in text
        or "sauconyorigs" in text
    )

    action = any(
        term in text
        for term in ACTION_TERMS
    )

    if saucony and action:
        return True

    return False


def priority(matches):

    if "s71047-5" in matches:
        return "🔴 CRITIQUE"

    if (
        "awesome gods" in matches
        and any(
            term in matches
            for term in ACTION_TERMS
        )
    ):
        return "🔴 CRITIQUE"

    if (
        "grid jazz 9" in matches
        and any(
            term in matches
            for term in ACTION_TERMS
        )
    ):
        return "🔴 CRITIQUE"

    if any(
        term in matches
        for term in STRONG_TERMS
    ):
        return "🟠 IMPORTANT"

    if (
        any(
            term in matches
            for term in IMPORTANT_TERMS
        )
        and any(
            term in matches
            for term in ACTION_TERMS
        )
    ):
        return "🟠 IMPORTANT"

    return "🟡 À SURVEILLER"


# --------------------------------------------------
# X
# --------------------------------------------------

def extract_status_id(article):

    for link in article.find_all("a"):

        href = link.get(
            "href",
            ""
        )

        match = re.search(
            r"/status/(\d+)",
            href
        )

        if match:
            return match.group(1)

    return None


def extract_articles(soup):

    articles = soup.find_all(
        "article"
    )

    results = []

    for article in articles:

        text = normalise(
            article.get_text(
                " ",
                strip=True
            )
        )

        if not text:
            continue

        status_id = extract_status_id(
            article
        )

        results.append(
            {
                "status_id": status_id,
                "text": text
            }
        )

    return results


def create_alert(
    alerts,
    post_key,
    status_id,
    text,
    matches,
    level,
    url
):

    # Sécurité supplémentaire :
    # ne jamais mettre deux fois
    # le même signal dans la file.
    for alert in alerts:

        if alert.get("post_key") == post_key:
            return

    alerts.append(
        {
            "post_key": post_key,
            "source": "X",
            "priority": level,
            "terms": matches,
            "excerpt": text[:900],
            "url": url,
            "post_id": status_id or "",
            "detected_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }
    )


def analyse_x(memory, alerts):

    print()
    print("🌐 Source : X")
    print(
        f"🔗 {X_URL}"
    )

    try:

        response = requests.get(
            X_URL,
            headers=HEADERS,
            timeout=20
        )

        print(
            f"📡 HTTP : {response.status_code}"
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print(
            f"⚠️ X inaccessible : {error}"
        )

        return 0

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    articles = extract_articles(
        soup
    )

    if not articles:

        print(
            "⚠️ Aucun post X exploitable"
        )

        return 0

    print(
        f"📰 Publications analysables : "
        f"{len(articles)}"
    )

    known_posts = set(
        memory.get(
            "posts",
            []
        )
    )

    current_posts = []

    for article in articles:

        text = article["text"]

        if not is_relevant(text):
            continue

        status_id = article[
            "status_id"
        ]

        if status_id:

            post_key = (
                f"x:{status_id}"
            )

        else:

            post_key = (
                "x-content:"
                + content_id(text)
            )

        current_posts.append(
            post_key
        )

    current_posts = list(
        dict.fromkeys(
            current_posts
        )
    )

    # ------------------------------------------------
    # PREMIER PASSAGE
    # ------------------------------------------------

    if not memory.get(
        "initialized",
        False
    ):

        for post_key in current_posts:
            known_posts.add(
                post_key
            )

        memory["posts"] = list(
            known_posts
        )

        memory["initialized"] = True

        print()
        print(
            "🧠 Initialisation de la mémoire X"
        )

        print(
            f"📌 Publications mémorisées : "
            f"{len(current_posts)}"
        )

        print(
            "✅ Aucun ancien contenu "
            "ne déclenche d'alerte."
        )

        return 0

    # ------------------------------------------------
    # PASSAGES SUIVANTS
    # ------------------------------------------------

    new_signals = 0

    for article in articles:

        text = article["text"]

        if not is_relevant(text):
            continue

        status_id = article[
            "status_id"
        ]

        if status_id:

            post_key = (
                f"x:{status_id}"
            )

        else:

            post_key = (
                "x-content:"
                + content_id(text)
            )

        if post_key in known_posts:
            continue

        known_posts.add(
            post_key
        )

        matches = find_terms(
            text
        )

        level = priority(
            matches
        )

        if status_id:

            post_url = (
                f"https://x.com/"
                f"WESTSIDEGUNN/status/"
                f"{status_id}"
            )

        else:

            post_url = X_URL

        create_alert(
            alerts=alerts,
            post_key=post_key,
            status_id=status_id,
            text=text,
            matches=matches,
            level=level,
            url=post_url,
        )

        print()
        print(
            "🆕 NOUVEAU POST PERTINENT"
        )

        print(
            f"🚨 Priorité : {level}"
        )

        print(
            "🔎 Termes détectés :"
        )

        for term in matches:

            print(
                f"   • {term}"
            )

        if status_id:

            print(
                f"🆔 Post X : "
                f"{status_id}"
            )

        print(
            "📝 Extrait :"
        )

        print(
            f"   {text[:700]}"
        )

        print(
            "📥 Signal ajouté à "
            "westside_alerts.json"
        )

        new_signals += 1

    memory["posts"] = list(
        known_posts
    )

    if new_signals == 0:

        print(
            "♻️ Aucun nouveau post pertinent"
        )

    return new_signals


# --------------------------------------------------
# INSTAGRAM
# --------------------------------------------------

def analyse_instagram(
    memory,
    alerts
):

    print()
    print(
        "🌐 Source : Instagram"
    )

    print(
        f"🔗 {INSTAGRAM_URL}"
    )

    try:

        response = requests.get(
            INSTAGRAM_URL,
            headers=HEADERS,
            timeout=20
        )

        print(
            f"📡 HTTP : "
            f"{response.status_code}"
        )

        if response.status_code == 429:

            print(
                "⏳ Instagram limite "
                "les requêtes."
            )

            print(
                "ℹ️ Instagram ignoré "
                "pour ce passage."
            )

            return 0

        response.raise_for_status()

    except requests.RequestException as error:

        print(
            f"⚠️ Instagram inaccessible : "
            f"{error}"
        )

        return 0

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    text = normalise(
        soup.get_text(
            " ",
            strip=True
        )
    )

    precise_terms = [
        "s71047-5",
        "awesome gods",
        "grid jazz 9",
    ]

    matches = [
        term
        for term in precise_terms
        if term in text
    ]

    if not matches:

        print(
            "⚪ Aucun signal "
            "Instagram précis"
        )

        return 0

    signal_key = (
        "instagram:"
        + "|".join(
            sorted(matches)
        )
    )

    instagram_memory = set(
        memory.get(
            "instagram",
            []
        )
    )

    if signal_key in instagram_memory:

        print(
            "♻️ Signal Instagram "
            "déjà connu"
        )

        return 0

    instagram_memory.add(
        signal_key
    )

    memory["instagram"] = list(
        instagram_memory
    )

    print(
        "🆕 SIGNAL INSTAGRAM PRÉCIS"
    )

    for term in matches:

        print(
            f"   • {term}"
        )

    # Instagram reste secondaire.
    # On le met en file Telegram
    # uniquement lorsqu'un signal précis
    # apparaît pour la première fois.

    create_alert(
        alerts=alerts,
        post_key=signal_key,
        status_id="",
        text=(
            "Signal Instagram précis détecté : "
            + ", ".join(matches)
        ),
        matches=matches,
        level="🟠 IMPORTANT",
        url=INSTAGRAM_URL,
    )

    print(
        "📥 Signal ajouté à "
        "westside_alerts.json"
    )

    return 1


# --------------------------------------------------
# PROGRAMME PRINCIPAL
# --------------------------------------------------

def main():

    print(
        "🔎 WESTSIDE GUNN RADAR"
    )

    print(
        "🎯 X + Instagram"
    )

    print(
        "🎯 Surveillance : S71047-5"
    )

    print()

    memory = load_memory()
    alerts = load_alerts()

    total_new = 0

    total_new += analyse_x(
        memory,
        alerts
    )

    total_new += analyse_instagram(
        memory,
        alerts
    )

    save_memory(
        memory
    )

    save_alerts(
        alerts
    )

    print()
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "📊 Résultat Westside Gunn"
    )

    print(
        f"Nouveaux signaux : "
        f"{total_new}"
    )

    print(
        f"📨 Alertes en attente Telegram : "
        f"{len(alerts)}"
    )

    if total_new:

        print(
            "🚨 NOUVEAU SIGNAL DÉTECTÉ"
        )

    else:

        print(
            "✅ Aucun nouveau signal"
        )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


if __name__ == "__main__":
    main()
