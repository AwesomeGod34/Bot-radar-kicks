import requests

SHOP_URL = "https://www.saucony.com"
PRODUCT_URL = "https://www.saucony.com/en/grid-jazz-9/60326U.html"

TARGET_SIZE = "44.5"

SEARCH_TERMS = [
    "awesome gods",
    "awesome god",
    "grid jazz 9",
    "westside gunn",
    "s71047-5",
]


def get_page():
    response = requests.get(
        PRODUCT_URL,
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


def analyse_page(html):
    html_lower = html.lower()

    print(f"📄 Page analysée : {PRODUCT_URL}")

    for term in SEARCH_TERMS:
        if term in html_lower:
            print(f"🔎 Mot-clé trouvé : {term}")

    if TARGET_SIZE in html_lower:
        print(f"👟 Référence taille {TARGET_SIZE} trouvée dans la page")
    else:
        print(f"⚪ Taille {TARGET_SIZE} non détectée")


def main():
    print("🔎 Saucony Radar")
    print(f"🎯 Taille cible : EU {TARGET_SIZE}")

    try:
        html = get_page()
        analyse_page(html)
        print("✅ Test Saucony terminé")

    except Exception as error:
        print(f"❌ Erreur Saucony : {error}")


if __name__ == "__main__":
    main()
