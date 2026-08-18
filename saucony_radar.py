import re
import requests
from bs4 import BeautifulSoup

SHOP_URL = "https://www.saucony.com/FR/fr_FR/"

TARGET_SIZE = "44.5"

SEARCH_TERMS = [
    "s71047-5",
    "awesome gods",
    "awesome god",
    "grid jazz 9",
    "westside gunn",
]

CATALOG_URLS = [
    "https://www.saucony.com/FR/fr_FR/home",
    "https://www.saucony.com/FR/fr_FR/originals/",
    "https://www.saucony.com/FR/fr_FR/mens-originals-view-all/",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def get_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()
    return response.text


def normalise(text):
    return re.sub(r"\s+", " ", text).lower()


def search_page(url):
    print()
    print(f"🌐 Analyse : {url}")

    html = get_page(url)
    text = normalise(BeautifulSoup(html, "html.parser").get_text(" "))

    matches = []

    for term in SEARCH_TERMS:
        if term in text:
            matches.append(term)

    if matches:
        print("🚨 Correspondance détectée")
        for term in matches:
            print(f"   🔎 {term}")
    else:
        print("⚪ Aucune correspondance")

    return html, matches


def analyse_inventory(html):
    """
    Cherche les données d'inventaire présentes dans les pages
    produit Saucony.

    Cette fonction ne réalise aucune action d'achat.
    """

    html_lower = html.lower()

    if TARGET_SIZE not in html_lower:
        print(f"⚪ Taille {TARGET_SIZE} absente des données visibles")
        return

    print(f"👟 Taille {TARGET_SIZE} trouvée dans la page")

    # Saucony expose actuellement des structures du type :
    # size / sizeDisplayValue / isAvailable / status
    #
    # On cherche les blocs autour de la taille cible.
    positions = [
        match.start()
        for match in re.finditer(
            rf'"size"\s*:\s*"{re.escape(TARGET_SIZE)}"',
            html_lower,
        )
    ]

    if not positions:
        print("🟡 Taille trouvée, mais aucune structure de variante exploitable")
        return

    found_available = False

    for position in positions:
        section = html_lower[position:position + 1200]

        if '"isavailable":true' in section:
            found_available = True
            print("🟢 44,5 semble disponible dans une variante")

        elif "in_stock" in section:
            found_available = True
            print("🟢 44,5 associée à un statut IN_STOCK")

        else:
            print("🟡 44,5 détectée, disponibilité non confirmée")

    if not found_available:
        print("🔴 44,5 détectée mais disponibilité non confirmée")


def main():
    print("🔎 SAUCONY RADAR")
    print(f"🎯 Taille cible : EU {TARGET_SIZE}")
    print("🎯 Référence prioritaire : S71047-5")
    print()

    total_matches = 0

    try:
        for url in CATALOG_URLS:
            try:
                html, matches = search_page(url)

                if matches:
                    total_matches += len(matches)
                    analyse_inventory(html)

            except requests.RequestException as error:
                print(f"⚠️ Impossible d'analyser cette page : {error}")

    except Exception as error:
        print(f"❌ Erreur Saucony : {error}")
        return

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Résultat Saucony")
    print(f"Correspondances : {total_matches}")

    if total_matches == 0:
        print("✅ Aucun signal Awesome Gods détecté")
    else:
        print("🚨 Signal Saucony détecté")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
