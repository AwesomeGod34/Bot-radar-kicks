import json
import os
from pathlib import Path

import requests


# ============================================================
# CONFIGURATION
# ============================================================

SHOP_URL = "https://www.blientele.com"
PRODUCTS_URL = f"{SHOP_URL}/products.json?limit=250"
CART_ADD_URL = f"{SHOP_URL}/cart/add.js"
CART_URL = f"{SHOP_URL}/cart.js"

SEARCH_TERMS = [
    "awesome gods",
    "awesome god",
    "s71047-5",
    "grid jazz",
    "saucony",
]

# Tailles recherchées.
TARGET_SIZES = {
    "44.5",
    "10.5",
}

STATE_FILE = Path("blientele_cart_seen.json")

TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.environ.get(
    "TELEGRAM_CHAT_ID"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept-Language": (
        "fr-FR,fr;q=0.9,en;q=0.8"
    ),
}


# ============================================================
# MEMOIRE
# ============================================================

def load_state():
    if not STATE_FILE.exists():
        return {
            "carted_variants": []
        }

    try:
        data = json.loads(
            STATE_FILE.read_text(
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
        "carted_variants": []
    }


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


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
        "https://api.telegram.org/"
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

        print(
            "📲 Telegram envoyé"
        )

        return True

    except requests.RequestException as error:

        print(
            f"❌ Erreur Telegram : {error}"
        )

        return False


# ============================================================
# HTTP
# ============================================================

def create_session():

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    return session


def get_products(session):

    print(
        f"🌐 Catalogue : {PRODUCTS_URL}"
    )

    response = session.get(
        PRODUCTS_URL,
        params={
            "_radar": str(
                int(
                    __import__(
                        "time"
                    ).time()
                )
            )
        },
        timeout=20,
    )

    print(
        f"📡 HTTP catalogue : "
        f"{response.status_code}"
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "products",
        []
    )


# ============================================================
# RECHERCHE PRODUIT
# ============================================================

def product_matches(product):

    searchable = {
        "title": product.get(
            "title",
            ""
        ),
        "handle": product.get(
            "handle",
            ""
        ),
        "vendor": product.get(
            "vendor",
            ""
        ),
        "product_type": product.get(
            "product_type",
            ""
        ),
        "body_html": product.get(
            "body_html",
            ""
        ),
        "tags": product.get(
            "tags",
            ""
        ),
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


# ============================================================
# NORMALISATION DES TAILLES
# ============================================================

def normalize_size(value):

    value = str(
        value or ""
    ).strip().lower()

    value = value.replace(
        ",",
        "."
    )

    value = value.replace(
        "–",
        "-"
    )

    value = value.replace(
        "—",
        "-"
    )

    value = value.replace(
        "eu",
        ""
    )

    value = value.replace(
        "us",
        ""
    )

    value = value.replace(
        "size",
        ""
    )

    value = value.strip()

    return value


def detect_size(variant):

    title = normalize_size(
        variant.get(
            "title",
            ""
        )
    )

    option1 = normalize_size(
        variant.get(
            "option1",
            ""
        )
    )

    option2 = normalize_size(
        variant.get(
            "option2",
            ""
        )
    )

    option3 = normalize_size(
        variant.get(
            "option3",
            ""
        )
    )

    candidates = [
        title,
        option1,
        option2,
        option3,
    ]

    for value in candidates:

        if value in TARGET_SIZES:

            return value

        # Cas par exemple :
        # "44.5 EU"
        # "US 10.5"
        # "10.5 US"
        for target in TARGET_SIZES:

            if target in value.split():

                return target

    return None


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
# DETECTION DES VARIANTES
# ============================================================

def find_target_variants(product):

    matches = []

    variants = product.get(
        "variants",
        []
    )

    for variant in variants:

        size = detect_size(
            variant
        )

        if not size:
            continue

        variant_id = variant.get(
            "id"
        )

        available = bool(
            variant.get(
                "available",
                False
            )
        )

        matches.append(
            {
                "variant": variant,
                "size": size,
                "variant_id": variant_id,
                "available": available,
            }
        )

    return matches


# ============================================================
# AJOUT AU PANIER
# ============================================================

def add_to_cart(
    session,
    variant_id,
    product_title,
    size,
    url
):

    print()
    print(
        "🛒 TENTATIVE D'AJOUT AU PANIER"
    )

    print(
        f"Produit : {product_title}"
    )

    print(
        f"Taille détectée : {size}"
    )

    print(
        f"Variant ID : {variant_id}"
    )

    if not variant_id:

        print(
            "❌ Variant ID absent"
        )

        return False

    payload = {
        "id": int(variant_id),
        "quantity": 1,
    }

    try:

        response = session.post(
            CART_ADD_URL,
            data=payload,
            headers={
                "Accept": (
                    "application/json"
                ),
                "X-Requested-With": (
                    "XMLHttpRequest"
                ),
            },
            timeout=20,
        )

        print(
            f"📡 HTTP ajout panier : "
            f"{response.status_code}"
        )

        if response.status_code >= 400:

            print(
                "❌ Ajout au panier refusé"
            )

            print(
                response.text[:500]
            )

            return False

        print(
            "🟢 Réponse positive du panier"
        )

    except requests.RequestException as error:

        print(
            f"❌ Erreur ajout panier : "
            f"{error}"
        )

        return False

    # --------------------------------------------------------
    # Vérification réelle du panier
    # --------------------------------------------------------

    try:

        cart_response = session.get(
            CART_URL,
            timeout=20,
        )

        print(
            f"📡 HTTP vérification panier : "
            f"{cart_response.status_code}"
        )

        cart_response.raise_for_status()

        cart = cart_response.json()

        items = cart.get(
            "items",
            []
        )

        for item in items:

            item_variant_id = str(
                item.get(
                    "variant_id",
                    ""
                )
            )

            if item_variant_id == str(
                variant_id
            ):

                quantity = item.get(
                    "quantity",
                    0
                )

                print()
                print(
                    "✅ PRODUIT CONFIRMÉ "
                    "DANS LE PANIER"
                )

                print(
                    f"📦 Quantité : {quantity}"
                )

                message = (
                    "🚨 AWESOME GOD RADAR 🚨\n\n"
                    "🛒 BLIENTELE — PANIER\n\n"
                    f"👟 {product_title}\n"
                    f"📏 Taille : {size}\n"
                    f"🆔 Variant : {variant_id}\n"
                    f"📦 Quantité : {quantity}\n\n"
                    "🟢 Produit ajouté au panier "
                    "avec succès.\n\n"
                    f"🔗 Produit : {url}\n"
                    f"🛒 Panier : {CART_URL}"
                )

                send_telegram(
                    message
                )

                return True

        print(
            "⚠️ Réponse positive mais "
            "produit non retrouvé dans /cart.js"
        )

        return False

    except requests.RequestException as error:

        print(
            f"⚠️ Impossible de vérifier "
            f"le panier : {error}"
        )

        return False

    except ValueError:

        print(
            "⚠️ Réponse panier non JSON"
        )

        return False


# ============================================================
# INSPECTION PRODUIT
# ============================================================

def inspect_product(
    session,
    product,
    state
):

    title = product.get(
        "title",
        ""
    )

    url = product_url(
        product
    )

    print()
    print(
        "🚨 PRODUIT POTENTIEL DÉTECTÉ"
    )

    print(
        f"Nom : {title}"
    )

    print(
        f"Handle : "
        f"{product.get('handle', '')}"
    )

    print(
        f"ID produit : "
        f"{product.get('id', '')}"
    )

    print(
        f"🔗 {url}"
    )

    targets = find_target_variants(
        product
    )

    if not targets:

        print(
            "⚪ Aucune taille cible "
            "44,5 / US 10,5 trouvée"
        )

        return 0

    carted_variants = set(
        str(value)
        for value in state.get(
            "carted_variants",
            []
        )
    )

    actions = 0

    for target in targets:

        variant = target[
            "variant"
        ]

        size = target[
            "size"
        ]

        variant_id = target[
            "variant_id"
        ]

        available = target[
            "available"
        ]

        print()
        print(
            f"👟 Taille : {size}"
        )

        print(
            f"🆔 Variant : "
            f"{variant_id}"
        )

        print(
            f"📦 Disponible : "
            f"{available}"
        )

        if not available:

            print(
                "🔴 Taille cible "
                "indisponible"
            )

            continue

        print(
            "🟢 TAILLE CIBLE DISPONIBLE"
        )

        if str(variant_id) in carted_variants:

            print(
                "♻️ Variant déjà traité"
            )

            continue

        success = add_to_cart(
            session=session,
            variant_id=variant_id,
            product_title=title,
            size=size,
            url=url,
        )

        if success:

            carted_variants.add(
                str(variant_id)
            )

            state[
                "carted_variants"
            ] = list(
                carted_variants
            )

            save_state(
                state
            )

            actions += 1

        else:

            print(
                "⚠️ Ajout panier non confirmé"
            )

    return actions


# ============================================================
# PROGRAMME PRINCIPAL
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
        f"🌐 {PRODUCTS_URL}"
    )

    print()

    state = load_state()

    session = create_session()

    try:

        products = get_products(
            session
        )

    except requests.RequestException as error:

        print(
            f"❌ Erreur catalogue Blientele : "
            f"{error}"
        )

        return

    except ValueError as error:

        print(
            f"❌ Réponse catalogue invalide : "
            f"{error}"
        )

        return

    print()
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

        print()
        print(
            "⚪ Aucun produit correspondant"
        )

        print()
        print(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        print(
            "📊 Résultat Blientele"
        )
        print(
            "Aucun produit cible"
        )
        print(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        return

    print()
    print(
        f"🎯 Produits pertinents : "
        f"{len(matches)}"
    )

    total_actions = 0

    for product in matches:

        total_actions += inspect_product(
            session=session,
            product=product,
            state=state,
        )

    print()
    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "📊 Résultat Blientele"
    )

    print(
        f"Produits pertinents : "
        f"{len(matches)}"
    )

    print(
        f"🛒 Ajouts panier confirmés : "
        f"{total_actions}"
    )

    if total_actions:

        print(
            "🚨 PANIER PRÊT"
        )

    else:

        print(
            "✅ Aucun nouvel ajout "
            "au panier"
        )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


if __name__ == "__main__":
    main()
