import hashlib
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


MEMORY_FILE = Path("westside_seen.json")

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

# Termes directement liés à notre sortie
STRONG_TERMS = [
    "s71047-5",
    "awesome gods",
    "grid jazz 9",
]

# Termes utiles mais moins précis
IMPORTANT_TERMS = [
    "saucony",
    "sauconyorigs",
    "blientele",
]

# Termes d'action
ACTION_TERMS = [
    "release",
    "release details",
    "release date",
    "dropping",
    "available",
    "available now",
    "out now",
    "shop now",
    "link",
    "8/28",
    "8.28",
    "28 août",
]


def normalise(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_memory():
    if not MEMORY_FILE.exists():
        return set()

    try:
        data = json.loads(
            MEMORY_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, list):
            return set(data)

    except Exception as error:
        print(f"⚠️ Erreur lecture mémoire : {error}")

    return set()


def save_memory(memory):
    MEMORY_FILE.write_text(
        json.dumps(
            sorted(memory),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def make_id(content):
    return hashlib.sha256(
        normalise(content).encode("utf-8")
    ).hexdigest()


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

    return list(dict.fromkeys(matches))


def calculate_priority(matches):
    strong = any(
        term in matches
        for term in STRONG_TERMS
    )

    saucony = any(
        term in matches
        for term in IMPORTANT_TERMS
    )

    action = any(
        term in matches
        for term in ACTION_TERMS
    )

    # Référence exacte ou nom de la paire + action
    if strong and action:
        return "🔴 CRITIQUE"

    # Référence exacte / nom de paire
    if strong:
        return "🟠 IMPORTANT"

    # Saucony + action
    if saucony and action:
        return "🟠 IMPORTANT"

    # Saucony seul
    if saucony:
        return "🟡 À SURVEILLER"

    return "⚪ IGNORÉ"


def is_relevant(text):
    """
    Évite les faux positifs.
    """

    strong = any(
        term in text
        for term in STRONG_TERMS
    )

    saucony = any(
        term in text
        for term in IMPORTANT_TERMS
    )

    action = any(
        term in text
        for term in ACTION_TERMS
    )

    # La référence exacte suffit
    if "s71047-5" in text:
        return True

    # Un nom de paire seul est pertinent
    if "awesome gods" in text:
        return True

    if "grid jazz 9" in text:
        return True

    # Saucony doit être accompagné d'un élément
    # d'action pour devenir pertinent
    if saucony and action:
        return True

    return False


def analyse_x(memory):
    print()
    print("🌐 Source : X")
    print(f"🔗 {X_URL}")

    try:
        response = requests.get(
            X_URL,
            headers=HEADERS,
            timeout=20,
        )

        print(f"📡 HTTP : {response.status_code}")

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"⚠️ X inaccessible : {error}")
        return 0

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    # X utilise actuellement des balises article
    # pour ses publications lorsqu'elles sont exposées.
    articles = soup.find_all("article")

    if not articles:
        print("⚠️ Aucun article X identifiable")
        return 0

    print(f"📰 Publications détectées : {len(articles)}")

    new_signals = 0

    for article in articles:

        text = normalise(
            article.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        if not is_relevant(text):
            continue

        matches = find_terms(text)

        # Ignore les simples mentions génériques
        if not matches:
            continue

        post_id = make_id(text)

        if post_id in memory:
            continue

        memory.add(post_id)

        level = calculate_priority(matches)

        print()
        print("🆕 NOUVELLE PUBLICATION PERTINENTE")
        print(f"🚨 Priorité : {level}")

        print("🔎 Termes détectés :")

        for term in matches:
            print(f"   • {term}")

        print("📝 Extrait :")
        print(f"   {text[:700]}")

        new_signals += 1

    if new_signals == 0:
        print(
            "♻️ Aucun nouveau post pertinent détecté"
        )

    return new_signals


def analyse_instagram(memory):
    print()
    print("🌐 Source : Instagram")
    print(f"🔗 {INSTAGRAM_URL}")

    try:
        response = requests.get(
            INSTAGRAM_URL,
            headers=HEADERS,
            timeout=20,
        )

        print(f"📡 HTTP : {response.status_code}")

        if response.status_code == 429:
            print(
                "⏳ Instagram limite actuellement "
                "les requêtes (429)"
            )
            print(
                "ℹ️ Instagram sera simplement ignoré "
                "pour ce passage."
            )
            return 0

        response.raise_for_status()

    except requests.RequestException as error:
        print(f"⚠️ Instagram inaccessible : {error}")
        return 0

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    text = normalise(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    if not text:
        print("⚪ Aucun contenu public exploitable")
        return 0

    matches = find_terms(text)

    # Instagram n'est utilisé ici que comme
    # source complémentaire.
    if not matches:
        print("⚪ Aucun signal Instagram")
        return 0

    # On ne mémorise pas toute la page Instagram.
    relevant = [
        term
        for term in matches
        if term in STRONG_TERMS
    ]

    if not relevant:
        print(
            "⚪ Aucun signal Instagram suffisamment "
            "précis"
        )
        return 0

    content = "|".join(sorted(relevant))
    post_id = make_id(
        f"instagram|{content}"
    )

    if post_id in memory:
        print("♻️ Signal Instagram déjà connu")
        return 0

    memory.add(post_id)

    print("🆕 SIGNAL INSTAGRAM")
    print("🔎 Termes :")

    for term in relevant:
        print(f"   • {term}")

    return 1


def main():
    print("🔎 WESTSIDE GUNN RADAR")
    print("🎯 X + Instagram")
    print("🎯 Surveillance de la sortie S71047-5")
    print()

    memory = load_memory()

    total_new = 0

    # X = source principale
    total_new += analyse_x(memory)

    # Instagram = source secondaire
    total_new += analyse_instagram(memory)

    save_memory(memory)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Résultat Westside Gunn")
    print(f"Nouveaux signaux : {total_new}")

    if total_new:
        print("🚨 NOUVEAU SIGNAL DÉTECTÉ")
    else:
        print("✅ Aucun nouveau signal")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
