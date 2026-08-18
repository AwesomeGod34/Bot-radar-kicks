```python
import json
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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


def get_products():
    response = requests.get(
        PRODUCTS_URL,
        timeout=20,
        headers=HEADERS,
    )

    print(f"📡 HTTP : {response.status_code}")

    response.raise_for_status()

    data = response.json()

    return data.get("products", [])


def product_matches(product):
    """
    Recherche dans l'ensemble des informations
    textuelles principales du produit.
    """

    searchable = {
        "title": product.get("title", ""),
        "handle": product.get("handle", ""),
        "vendor": product.get("vendor", ""),
        "product_type": product.get("product_type", ""),
        "body_html": product.get("body_html", ""),
        "tags": product.get("tags", ""),
    }

    text = json.dumps(
        searchable,
        ensure_ascii=False,
        default=str,
    ).lower()

    return any(
        term.lower() in text
        for term in SEARCH_TERMS
    )


def normalize_size(value):
    value = str(value or "").strip().lower()

    value = value.replace(",", ".")

    value = value.replace("eu", "")
    value = value.replace("size", "")
    value = value.strip()

    return value


def is_target_size(variant):
    """
    Détecte EU 44,5 dans le titre de variante.
    """

    title = normalize_size(
        variant.get("title", "")
    )

    return title in {
        "44.5",
        "44.5 us",
        "44.5 uk",
        "44.5 eu",
        "eu 44.5",
    }


def product_url(product):
    handle = product.get("handle", "")

    if not handle:
        return SHOP_URL

    return (
        f"{SHOP_URL}/products/"
        f"{handle}"
    )


def inspect_product(product):
    print()
    print("🚨 PRODUIT POTENTIEL DÉTECTÉ")
    print(
        f"Nom : {product.get('title', '')}"
    )
    print(
        f"Handle : {product.get('handle', '')}"
    )
    print(
        f"ID produit : {product.get('id', '')}"
    )
    print(
        f"🔗 {product_url(product)}"
    )

    variants = product.get(
        "variants",
        []
    )

    if not variants:
        print(
            "⚠️ Aucune variante trouvée"
        )
        return False

    print(
        f"📦 Nombre de variantes : "
        f"{len(variants)}"
    )

    found_size = False
    available = False

    for variant in variants:

        title = str(
            variant.get(
                "title",
                ""
            )
        ).strip()

        variant_id = variant.get(
            "id"
        )

        is_available = bool(
            variant.get(
                "available",
                False
            )
        )

        print(
            f"  Variante : {title} | "
            f"ID : {variant_id} | "
            f"Disponible : {is_available}"
        )

        if is_target_size(variant):

            found_size = True

            if is_available:

                available = True

                print(
                    "🟢 TAILLE EU 44,5 "
                    "DISPONIBLE"
                )

                print(
                    f"🆔 Variant ID : "
                    f"{variant_id}"
                )

            else:

                print(
                    "🔴 TAILLE EU 44,5 "
                    "EXISTE MAIS "
                    "INDISPONIBLE"
                )

    if not found_size:

        print(
            "⚪ Taille EU 44,5 "
            "non trouvée"
        )

    return available


def main():

    print("")
    print("==============================")
    print("🔥 BLIENTELE RADAR")
    print("==============================")
    print(
        f"🎯 Taille cible : EU {TARGET_SIZE}"
    )
    print(
        f"🌐 Catalogue : {PRODUCTS_URL}"
    )
    print("")

    try:

        products = get_products()

        print(
            f"📦 Produits trouvés : "
            f"{len(products)}"
        )

        matches = [
            product
            for product in products
            if product_matches(product)
        ]

        if not matches:

            print("")
            print(
                "⚪ Aucun produit "
                "correspondant détecté"
            )
            return

        print("")
        print(
            f"🎯 Produits pertinents : "
            f"{len(matches)}"
        )

        available_count = 0

        for product in matches:

            if inspect_product(
                product
            ):
                available_count += 1

        print("")
        print(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        print("📊 Résultat Blientele")
        print(
            f"Produits pertinents : "
            f"{len(matches)}"
        )
        print(
            f"EU 44,5 disponible : "
            f"{available_count}"
        )

        if available_count:

            print(
                "🚨 DISPONIBILITÉ DÉTECTÉE"
            )

        else:

            print(
                "✅ Aucun EU 44,5 disponible"
            )

        print(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    except requests.RequestException as error:

        print(
            f"❌ Erreur HTTP Blientele : "
            f"{error}"
        )

    except Exception as error:

        print(
            f"❌ Erreur Blientele : "
            f"{error}"
        )


if __name__ == "__main__":
    main()
```
