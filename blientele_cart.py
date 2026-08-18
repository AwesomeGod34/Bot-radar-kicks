```python
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import requests


# ============================================================
# CONFIGURATION
# ============================================================

SHOP_URL = "https://www.blientele.com"
PRODUCTS_URL = f"{SHOP_URL}/products.json?limit=250"

MEMORY_FILE = Path("blientele_cart_seen.json")

TARGET_SIZES = {
    "44.5",
    "44,5",
    "us 10.5",
    "us10.5",
    "10.5",
}

SEARCH_TERMS = [
    "awesome gods",
    "awesome god",
    "saucony",
    "grid jazz",
    "s71047-5",
]

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

TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.environ.get(
    "TELEGRAM_CHAT_ID"
)


# ============================================================
# MEMOIRE
# ============================================================

def load_memory():

    if not MEMORY_FILE.exists():
        return {
            "products": []
        }

    try:

        data = json.loads(
            MEMORY_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, dict):
            return data

    except Exception as error:

        print(
            f"⚠️ Erreur mémoire : {error}"
        )

    return {
        "products": []
    }


def save_memory(memory):

    MEMORY_FILE.write_text(
        json.dumps(
            memory,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def make_id(value):

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):

    if not TELEGRAM_TOKEN:
        print(
            "⚠️ TELEGRAM_BOT_TOKEN absent"
        )
        return False

    if not TELEGRAM_CHAT_ID:
        print(
            "⚠️ TELEGRAM_CHAT_ID absent"
        )
        return False

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    try:

        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "disable_web_page_preview": False,
            },
            timeout=20,
        )

        response.raise_for_status()

        return True

    except requests.RequestException as error:

        print(
            f"❌ Telegram : {error}"
        )

        return False


# ============================================================
# CATALOGUE
# ============================================================

def get_products():

    print(
        f"🌐 Catalogue : {PRODUCTS_URL}"
    )

    response = requests.get(
        PRODUCTS_URL,
        headers=HEADERS,
        timeout=20,
    )

    print(
        f"📡 HTTP catalogue : "
        f"{response.status_code}"
    )

    response.raise_for_status()

    try:

        data = response.json()

    except ValueError as error:

        raise RuntimeError(
            "Réponse catalogue non JSON"
        ) from error

    products = data.get(
        "products",
        []
    )

    if not isinstance(
        products,
        list
    ):
        return []

    return products


# ============================================================
# DETECTION PRODUIT
# ============================================================

def searchable_text(product):

    fields = [
        product.get("title", ""),
        product.get("handle", ""),
        product.get("vendor", ""),
        product.get("product_type", ""),
        product.get("body_html", ""),
        product.get("tags", ""),
    ]

    return " ".join(
        str(field or "")
        for field in fields
    ).lower()


def product_matches(product):

    text = searchable_text(
        product
    )

    return any(
        term.lower() in text
        for term in SEARCH_TERMS
    )


# ============================================================
# TAILLES
# ============================================================

def normalize_size(value):

    text = str(
        value or ""
    ).lower().strip()

    text = (
        text
        .replace(",", ".")
        .replace("eu", "")
        .replace("size", "")
        .strip()
    )

    return text


def is_target_size(variant):

    title = normalize_size(
        variant.get("title", "")
    )

    option1 = normalize_size(
        variant.get("option1", "")
    )

    candidates = {
        title,
        option1,
    }

    for value in candidates:

        if value in {
            "44.5",
            "10.5",
        }:
            return True

        if value in {
            "44.5 us",
            "us 10.5",
            "us10.5",
        }:
            return True

    return False


def find_target_variants(product):

    variants = product.get(
        "variants",
        []
    )

    results = []

    for variant in variants:

        if is_target_size(
            variant
        ):
            results.append(
                variant
            )

    return results


# ============================================================
# URL PRODUIT
# ============================================================

def product_url(product):

    handle = product.get(
        "handle",
        ""
    )

    if not handle:
        return SHOP_URL

    return (
        f"{SHOP_URL}/products/"
        f"{handle}"
    )


# ============================================================
# PREPARATION PANIER
# ============================================================

def build_cart_url(variant):

    variant_id = variant.get(
        "id"
    )

    if not variant_id:
        return None

    """
    Shopify expose souvent une route de panier
    basée sur l'identifiant de variante.

    Cette URL est uniquement préparée pour
    permettre à l'utilisateur d'ouvrir le panier.
    Elle ne déclenche aucun paiement.
    """

    return (
        f"{SHOP_URL}/cart/"
        f"{variant_id}:1"
    )


# ============================================================
# INSPECTION
# ============================================================

def inspect_product(product):

    title = product.get(
        "title",
        "Produit sans nom"
    )

    handle = product.get(
        "handle",
        ""
    )

    product_id = product.get(
        "id",
        ""
    )

    url = product_url(
        product
    )

    variants = product.get(
        "variants",
        []
    )

    print()
    print(
        "🚨 PRODUIT CIBLE DÉTECTÉ"
    )

    print(
        f"👟 Nom : {title}"
    )

    print(
        f"🔑 Handle : {handle}"
    )

    print(
        f"🆔 Produit : {product_id}"
    )

    print(
        f"🔗 Produit : {url}"
    )

    print(
        f"📦 Variantes : "
        f"{len(variants)}"
    )

    target_variants = (
        find_target_variants(
            product
        )
    )

    if not target_variants:

        print(
            "⚪ EU 44,5 / US 10,5 "
            "non trouvée"
        )

        return []

    results = []

    for variant in target_variants:

        variant_id = variant.get(
            "id"
        )

        variant_title = variant.get(
            "title",
            ""
        )

        available = bool(
            variant.get(
                "available",
                False
            )
        )

        cart_url = (
            build_cart_url(
                variant
            )
        )

        print()

        print(
            f"🎯 Taille : "
            f"{variant_title}"
        )

        print(
            f"🆔 Variant ID : "
            f"{variant_id}"
        )

        print(
            f"📦 Disponible : "
            f"{available}"
        )

        if available:

            print(
                "🟢 TAILLE CIBLE DISPONIBLE"
            )

            if cart_url:

                print(
                    f"🛒 URL panier préparée : "
                    f"{cart_url}"
                )

        else:

            print(
                "🔴 Taille présente "
                "mais indisponible"
            )

        results.append(
            {
                "variant_id": variant_id,
                "variant_title": variant_title,
                "available": available,
                "product_url": url,
                "cart_url": cart_url,
            }
        )

    return results


# ============================================================
# ALERTE
# ============================================================

def notify_product(
    product,
    variant_info
):

    title = product.get(
        "title",
        "Produit"
    )

    product_url_value = (
        variant_info["product_url"]
    )

    cart_url = (
        variant_info["cart_url"]
    )

    variant_title = (
        variant_info["variant_title"]
    )

    message = (
        "🚨 AWESOME GOD RADAR 🚨\n\n"
        "🔥 BLIENTELE\n"
        "🟢 PRODUIT + TAILLE DÉTECTÉS\n\n"
        f"👟 {title}\n"
        f"🎯 Taille : {variant_title}\n\n"
        "🔗 Produit :\n"
        f"{product_url_value}\n"
    )

    if cart_url:

        message += (
            "\n🛒 Panier préparé :\n"
            f"{cart_url}\n"
            "\n⚠️ Vérifie le panier "
            "et finalise manuellement."
        )

    else:

        message += (
            "\n⚠️ Impossible de préparer "
            "une URL panier avec cette "
            "structure de variante."
        )

    send_telegram(
        message
    )


# ============================================================
# RADAR
# ============================================================

def main():

    print()
    print(
        "================================"
    )
    print(
        "🔥 BLIENTELE EARLY-DROP RADAR"
    )
    print(
        "================================"
    )

    print(
        "🎯 Tailles : EU 44,5 / US 10,5"
    )

    print(
        "🎯 Surveillance : "
        "Awesome Gods / Saucony / "
        "Grid Jazz / S71047-5"
    )

    print(
        "🛒 Mode : CART ASSISTANT"
    )

    print(
        "🕐 UTC :",
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    print()

    memory = load_memory()

    seen_products = set(
        memory.get(
            "products",
            []
        )
    )

    try:

        products = get_products()

    except Exception as error:

        print(
            f"❌ Impossible de lire "
            f"le catalogue : {error}"
        )

        return

    print()
    print(
        f"📦 Produits trouvés : "
        f"{len(products)}"
    )

    if not products:

        print()
        print(
            "⚪ Aucun produit actuellement "
            "présent dans le catalogue."
        )

        save_memory(
            memory
        )

        return

    relevant_products = [
        product
        for product in products
        if product_matches(product)
    ]

    print(
        f"🎯 Produits pertinents : "
        f"{len(relevant_products)}"
    )

    if not relevant_products:

        print()
        print(
            "⚪ Aucun produit cible détecté."
        )

        save_memory(
            memory
        )

        return

    for product in relevant_products:

        product_id = str(
            product.get(
                "id",
                product.get(
                    "handle",
                    ""
                )
            )
        )

        product_key = (
            "product:"
            + product_id
        )

        variant_results = (
            inspect_product(
                product
            )
        )

        available_variants = [
            item
            for item in variant_results
            if item.get(
                "available",
                False
            )
        ]

        # ----------------------------------------------------
        # NOUVEAU PRODUIT + TAILLE DISPONIBLE
        # ----------------------------------------------------

        if available_variants:

            for variant_info in (
                available_variants
            ):

                variant_key = (
                    product_key
                    + ":variant:"
                    + str(
                        variant_info.get(
                            "variant_id"
                        )
                    )
                )

                if variant_key in seen_products:

                    print(
                        "♻️ Signal déjà envoyé :",
                        variant_key
                    )

                    continue

                notify_product(
                    product,
                    variant_info
                )

                seen_products.add(
                    variant_key
                )

        # ----------------------------------------------------
        # MEMORISATION DU PRODUIT
        # ----------------------------------------------------

        fingerprint = make_id(
            json.dumps(
                {
                    "title": product.get(
                        "title",
                        ""
                    ),
                    "handle": product.get(
                        "handle",
                        ""
                    ),
                    "variants": product.get(
                        "variants",
                        []
                    ),
                },
                sort_keys=True,
                default=str,
            )
        )

        memory[
            "fingerprint:"
            + product_key
        ] = fingerprint

    memory["products"] = list(
        seen_products
    )

    save_memory(
        memory
    )

    print()
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    print(
        "📊 Résultat Blientele"
    )
    print(
        f"🎯 Produits cibles : "
        f"{len(relevant_products)}"
    )
    print(
        "🛒 Mode : assistance panier"
    )
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


if __name__ == "__main__":
    main()
```
