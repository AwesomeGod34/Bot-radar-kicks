import re
import requests

TARGET_TERMS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "grid jazz 9",
    "westside gunn",
]

EQL_URLS = [
    "https://eql.com/",
    "https://app.eql.com/",
]

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


def analyse(url):
    print()
    print(f"🌐 Analyse EQL : {url}")

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
            print("🚨 CORRESPONDANCE DÉTECTÉE")

            for term in matches:
                print(f"   🔎 {term}")

        else:
            print("⚪ Aucun signal Awesome Gods détecté")

        return matches

    except requests.RequestException as error:
        print(f"⚠️ Impossible d'analyser EQL : {error}")
        return []


def main():
    print("🔎 EQL RADAR")
    print("🎯 Référence prioritaire : S71047-5")
    print("🎯 Objectif : détecter l'apparition du lancement")
    print()

    total_matches = 0

    for url in EQL_URLS:
        matches = analyse(url)
        total_matches += len(matches)

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Résultat EQL")
    print(f"Correspondances : {total_matches}")

    if total_matches == 0:
        print("✅ Aucun signal Awesome Gods détecté")
    else:
        print("🚨 SIGNAL EQL DÉTECTÉ")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
