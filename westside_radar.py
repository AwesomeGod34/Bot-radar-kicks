import hashlib
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


MEMORY_FILE = Path("westside_seen.json")

STRONG_TERMS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "grid jazz 9",
]

IMPORTANT_TERMS = [
    "saucony",
    "blientele",
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
    "8/28",
    "8.28",
    "28 août",
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
        data = json.loads(
            MEMORY_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, list):
            return set(data)

    except Exception as error:
        print(f"⚠️ Erreur mémoire : {error}")

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


def fingerprint(source, content):
    raw = f"{source}|{content}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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


def priority(matches):
    has_strong = any(
        term in matches for term in STRONG_TERMS
    )

    has_important = any(
        term in matches for term in IMPORTANT_TERMS
    )

    has_action = any(
        term in matches for term in ACTION_TERMS
    )

    if has_strong and has_action:
        return "🔴 CRITIQUE"

    if has_strong:
        return "🟠 IMPORTANT"

    if has_important and has_action:
        return "🟠 IMPORTANT"

    if has_important:
        return "🟡 À SURVEILLER"

    return "⚪ FAIBLE"


def extract_relevant_blocks(soup):
    """
    Extrait des blocs textuels contenant au moins un
    mot-clé intéressant.

    On ne mémorise plus toute la page.
    """

    blocks = []

    for element in soup.find_all(
        ["article", "div", "li", "p", "span"]
    ):
        text = normalise(
            element.get_text(" ", strip=True)
        )

        if not text:
            continue

        terms = find_terms(text)

        if not terms:
            continue

        # Évite de conserver des blocs gigantesques.
        if len(text) > 1500:
            text = text[:1500]

        blocks.append(text)

    # Suppression des doublons
    unique_blocks = []

    for block in blocks:
        if block not in unique_blocks:
            unique_blocks.append(block)

    return unique_blocks


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

    except requests.RequestException as error:
        print(f"⚠️ Source inaccessible : {error}")
        return 0

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    blocks = extract_relevant_blocks(soup)

    if not blocks:
        print("⚪ Aucun bloc pertinent détecté")
        return 0

    new_blocks = 0

    for block in blocks:

        terms = find_terms(block)

        block_id = fingerprint(
            name,
            block,
        )

        if block_id in memory:
            continue

        memory.add(block_id)

        new_blocks += 1

        level = priority(terms)

        print()
        print("🆕 NOUVEAU CONTENU")
        print(f"🚨 Priorité : {level}")

        print("🔎 Mots-clés :")
        for term in terms:
            print(f"   • {term}")

        print("📝 Extrait :")
        print(f"   {block[:500]}")

    if new_blocks == 0:
        print("♻️ Aucun nouveau contenu pertinent")

    return new_blocks


def main():
    print("🔎 WESTSIDE GUNN RADAR")
    print("🎯 Surveillance publique Instagram + X")
    print("🎯 Référence : S71047-5")
    print()

    memory = load_memory()

    total_new = 0

    for name, url in SOURCES.items():
        total_new += analyse_source(
            name,
            url,
            memory,
        )

    save_memory(memory)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Résultat Westside Gunn")
    print(f"Nouveaux blocs : {total_new}")

    if total_new:
        print("🚨 NOUVEAU SIGNAL DÉTECTÉ")
    else:
        print("✅ Aucun nouveau signal")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
