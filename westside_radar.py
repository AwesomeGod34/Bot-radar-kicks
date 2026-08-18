import re
import requests

TARGET_TERMS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "grid jazz 9",
    "saucony",
    "release details",
    "release date",
    "dropping",
    "drop",
    "blientele",
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
    return re.sub(r"\s+", " ", text).lower()


def analyse_source(name, url):
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

        text = normalise(response.text)

        matches = []

        for term in TARGET_TERMS:
            if term in text:
                matches.append(term)

        if matches:
            print("🚨 MOTS-CLÉS DÉTECTÉS")

            for term in matches:
                print(f"   🔎 {term}")

        else:
            print("⚪ Aucun signal détecté")

        return matches

    except requests.RequestException as error:
        print(f"⚠️ Source inaccessible : {error}")
        return []


def main():
    print("🔎 WESTSIDE GUNN RADAR")
    print("🎯 Surveillance publique Instagram + X")
    print("🎯 Référence : S71047-5")
    print()

    total_matches = 0

    for name, url in SOURCES.items():
        matches = analyse_source(name, url)
        total_matches += len(matches)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Résultat Westside Gunn")
    print(f"Correspondances : {total_matches}")

    if total_matches == 0:
        print("✅ Aucun nouveau signal détecté")
    else:
        print("🚨 SIGNAL WESTSIDE GUNN DÉTECTÉ")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
