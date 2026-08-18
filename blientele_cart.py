import requests
import re

BLIEANTELE_URL = "https://www.blientele.com/collections/all"

SEARCH_TERMS = [
    "awesome gods",
    "awesome god",
    "saucony",
    "grid jazz",
    "s71047-5",
]

TARGET_SIZE = "44.5"


def get_blientele_products():
    response = requests.get(
        BLIEANTELE_URL,
        timeout=20,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
            )
        },
    )

    response.raise_for_status()
    return response.text


def find_target(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).lower()

    matches = []

    for term in SEARCH_TERMS:
        if term in text:
            matches.append(term)

    return matches


def main():
    print("🔎 Surveillance Blientele")
    print(f"🎯 Taille cible : EU {TARGET_SIZE}")

    try:
        html = get_blientele_products()

        matches = find_target(html)

        if matches:
            print("🚨 OCCURRENCE DÉTECTÉE")
            print("Mots-clés trouvés :", ", ".join(matches))
        else:
            print("✅ Aucun produit Awesome Gods détecté")

    except Exception as e:
        print(f"❌ Erreur Blientele : {e}")


if __name__ == "__main__":
    main()
