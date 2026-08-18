import hashlib
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


MEMORY_FILE = Path("westside_seen.json")

TARGET_TERMS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "grid jazz 9",
    "westside gunn",
    "saucony",
    "blientele",
    "release details",
    "release date",
]

STRONG_TERMS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "grid jazz 9",
]

ACTION_TERMS = [
    "release details",
    "release date",
    "dropping",
    "available",
    "available now",
    "out now",
    "shop now",
    "link",
]

SOURCES = {
    "Instagram": "https://www.instagram.com/westsidegunn/",
    "X": "https://x.com/WESTSIDEGUNN",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def normalise(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_memory():
    if not MEMORY_FILE.exists():
        return set()

    try:
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))

        if isinstance(data, list):
            return set(data)

    except Exception as error:
        print(f"⚠️ Impossible de lire la mémoire : {error}")

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


def create_fingerprint(source, content):
    raw = f"{source}|{content}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def find_matches(text):
    matches = []

    for term in TARGET_TERMS:
        if term in text:
            matches.append(term)

    return matches


def calculate_priority(matches):
    strong = any(term in matches for term in STRONG_TERMS)
    action = any(term in matches for term in ACTION_TERMS)

    if strong and action:
        return "🔴 CRITIQUE"

    if strong:
        return "🟠 IMPORTANT"

    if action:
        return "🟡 À SURVEILLER"

    return "⚪ FAIBLE"


def analyse_source(name, url, memory):
    print()
    print(f"🌐 Source : {name}")
    print(f"🔗 {url}")

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )

        print(f"📡 HTTP : {response.status_code}")

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # On récupère le contenu textuel de la page.
        text = normalise(soup.get_text(" ", strip=True))

        matches = find_matches(text)

        if not matches:
            print("⚪ Aucun mot-clé pertinent")
            return False

        print("🔎 Correspondances :")

        for term in matches:
            print(f"   • {term}")

        fingerprint = create_fingerprint(name, text)

        if fingerprint in memory:
            print("♻️ Contenu déjà connu")
            return False

        memory.add(fingerprint)

        priority = calculate_priority(matches)

        print(f"🆕 NOUVEAU CONTENU")
        print(f"🚨 Priorité : {priority}")

        return True

    except requests.RequestException as error:
        print(f"⚠️ Source inaccessible : {error}")
        return False


def main():
    print("🔎 WESTSIDE GUNN RADAR")
    print("🎯 Surveillance publique Instagram + X")
    print("🎯 Référence : S71047-5")
    print()

    memory = load_memory()

    new_signals = 0

    for name, url in SOURCES.items():
        if analyse_source(name, url, memory):
            new_signals += 1

    save_memory(memory)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Résultat Westside Gunn")
    print(f"Nouveaux signaux : {new_signals}")

    if new_signals:
        print("🚨 NOUVEAU SIGNAL DÉTECTÉ")
    else:
        print("✅ Aucun nouveau signal")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
