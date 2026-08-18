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

WESTSIDE_IDENTIFIERS = [
    "@westsidegunn",
    "westsidegunn",
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


def is_westside_post(text):
    """
    Vérifie que le contenu semble appartenir
    au compte Westside Gunn.

    On accepte les publications contenant
    son identifiant, mais on élimine les cas
    où la présence de @westsidegunn vient
    simplement d'une mention dans une réponse.
    """

    if "@westsidegunn" not in text:
        return False

    # Si le texte commence clairement par une
    # mention d'un autre utilisateur, on évite
    # de le considérer comme un post de Westside.
    first_part = text[:150]

    other_user = re.search(
        r"@\w+",
        first_part,
    )

    if other_user:
        username = other_user.group(0).lower()

        if username != "@westsidegunn":
            return False

    return True


def is_relevant(text):
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

    # Référence exacte
    if "s71047-5" in text:
        return True

    # Nom exact de la collaboration
    if "awesome gods" in text:
        return True

    if "grid jazz 9" in text:
        return True

    # Saucony + action de release
    if saucony and action:
        return True

    return False


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

    if "s71047-5" in matches:
        return "🔴 CRITIQUE"

    if (
        ("awesome gods" in matches
         or "grid jazz 9" in matches)
        and action
    ):
        return "🔴 CRITIQUE"

    if strong:
        return "🟠 IMPORTANT"

    if saucony and action:
        return "🟠 IMPORTANT"

    if saucony:
        return "🟡 À SURVEILLER"

    return "⚪ IGNORÉ"


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

    articles = soup.find_all("article")

    if not articles:
        print("⚠️ Aucun article X identifiable")
        return 0

    print(
        f"📰 Blocs X détectés : {len(articles)}"
    )

    seen_in_this_run = set()
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

        # On ne veut que les contenus
        # appartenant réellement à Westside.
        if not is_westside_post(text):
            continue

        # On ignore les vieux signaux génériques.
        if any(
            term in text
            for term in IGNORE_TERMS
        ):
            if not any(
                term in text
                for term in STRONG_TERMS
            ):
                continue

        if not is_relevant(text):
            continue

        matches = find_terms(text)

        # Déduplication pendant le même passage
        post_id = make_id(text)

        if post_id in seen_in_this_run:
            continue

        seen_in_this_run.add(post_id)

        # Déduplication entre deux exécutions
        if post_id in memory:
            continue

        memory.add(post_id)

        level = calculate_priority(matches)

        print()
        print("🆕 NOUVEAU POST WESTSIDE GUNN")
        print(f"🚨 Priorité : {level}")

        print("🔎 Termes détectés:")

        for term in matches:
            print(f"   • {term}")

        print("📝 Extrait :")
        print(f"   {text[:700]}")

        new_signals += 1

    if new_signals == 0:
        print(
            "♻️ Aucun nouveau post Westside pertinent"
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
                "les requêtes."
            )
            print(
                "ℹ️ Instagram ignoré pour ce passage."
            )
            return 0

        response.raise_for_status()

    except requests.RequestException as error:
        print(
            f"⚠️ Instagram inaccessible : {error}"
        )
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
        print(
            "⚪ Aucun contenu Instagram exploitable"
        )
        return 0

    # Instagram reste secondaire.
    # On ne déclenche que sur une référence
    # extrêmement précise.
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
        print("⚪ Aucun signal Instagram précis")
        return 0

    signal_id = make_id(
        "instagram|" + "|".join(matches)
    )

    if signal_id in memory:
        print("♻️ Signal Instagram déjà connu")
        return 0

    memory.add(signal_id)

    print("🆕 SIGNAL INSTAGRAM")
    print("🔎 Termes :")

    for term in matches:
        print(f"   • {term}")

    return 1


def main():
    print("🔎 WESTSIDE GUNN RADAR")
    print("🎯 X + Instagram")
    print("🎯 Surveillance : S71047-5")
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
