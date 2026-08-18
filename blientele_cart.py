import requests

SHOP_URL = "https://www.blientele.com"
PRODUCTS_URL = f"{SHOP_URL}/products.json?limit=250"

SEARCH_TERMS = [
    "awesome gods",
    "awesome god",
    "saucony",
    "grid jazz",
    "s71047-5",
]

TARGET_SIZE = "44.5"


def get_products():
    response = requests.get(
        PRODUCTS_URL,
        timeout=20,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
            )
        },
    )

    response.raise_for_status()

    data = response.json()
    return data.get("products", [])


def product_matches(product):
    text = (
        product.get("title", "")
        + " "
        + product.get("handle", "")
        + " "
        + product.get("vendor", "")
    ).lower()

    return any(term in text for term in SEARCH_TERMS)


def inspect_product(product):
    print()
    print("🚨 PRODUIT POTENTIEL DÉTECTÉ")
    print(f"Nom : {product.get('title')}")
    print(f"Handle : {product.get('handle')}")
    print(f"ID produit : {product.get('id')}")

    variants = product.get("variants", [])

    if not variants:
        print("⚠️ Aucune variante trouvée")
        return

    print(f"Nombre de variantes : {len(variants)}")

    found_size = False

    for variant in variants:
        size = str(variant.get("title", "")).strip()

        print(
            f"  Variante : {size} | "
            f"ID : {variant.get('id')} | "
            f"Disponible : {variant.get('available')}"
        )

        normalized = size.replace(",", ".").lower()

        if normalized in ("44.5", "44.5 eu", "eu 44.5"):
            found_size = True

            if variant.get("available"):
                print("🟢 TAILLE 44,5 DISPONIBLE")
            else:
                print("🔴 TAILLE 44,5 EXISTE MAIS INDISPONIBLE")

    if not found_size:
        print("⚪ Taille 44,5 non trouvée")


def main():
    print("🔎 Blientele — détecteur catalogue")
    print(f"🎯 Taille cible : EU {TARGET_SIZE}")

    try:
        products = get_products()

        print(f"📦 Produits trouvés : {len(products)}")

        matches = [
            product for product in products
            if product_matches(product)
        ]

        if not matches:
            print("✅ Aucun produit correspondant détecté")
            return

        for product in matches:
            inspect_product(product)

    except Exception as error:
        print(f"❌ Erreur Blientele : {error}")


if __name__ == "__main__":
    main()
