```python
import os
import json
from pathlib import Path

import requests


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

WESTSIDE_ALERTS_FILE = Path(
    "westside_alerts.json"
)


def send_telegram(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )

    response.raise_for_status()


def load_westside_alerts():

    if not WESTSIDE_ALERTS_FILE.exists():
        return []

    try:

        data = json.loads(
            WESTSIDE_ALERTS_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except Exception as error:

        print(
            "⚠️ Erreur lecture "
            "westside_alerts.json :",
            error
        )

    return []


def save_westside_alerts(alerts):

    WESTSIDE_ALERTS_FILE.write_text(
        json.dumps(
            alerts,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


def send_westside_alerts():

    alerts = load_westside_alerts()

    if not alerts:

        print(
            "👤 WESTSIDE GUNN : "
            "aucun nouveau signal Telegram."
        )

        return

    print(
        "👤 WESTSIDE GUNN :",
        len(alerts),
        "signal(s) en attente."
    )

    remaining = []

    for alert in alerts:

        try:

            priority = alert.get(
                "priority",
                "🟡 À SURVEILLER"
            )

            terms = alert.get(
                "terms",
                []
            )

            excerpt = alert.get(
                "excerpt",
                ""
            )

            url = alert.get(
                "url",
                "https://x.com/WESTSIDEGUNN"
            )

            post_id = alert.get(
                "post_id",
                ""
            )

            detected_at = alert.get(
                "detected_at",
                ""
            )

            terms_text = ", ".join(
                terms
            )

            message = (
                "🚨 AWESOME GOD RADAR 🚨\n\n"
                "👤 WESTSIDE GUNN\n"
                f"{priority}\n\n"
                "🎯 Référence : S71047-5\n"
                "👟 Sujet : Awesome Gods / Saucony\n\n"
            )

            if terms_text:

                message += (
                    "🔎 Détection : "
                    f"{terms_text}\n\n"
                )

            if excerpt:

                message += (
                    "📝 Contenu détecté :\n"
                    f"{excerpt[:900]}\n\n"
                )

            if post_id:

                message += (
                    f"🆔 Post X : {post_id}\n"
                )

            if detected_at:

                message += (
                    "🕐 Détection : "
                    f"{detected_at}\n"
                )

            message += (
                "\n🔗 Source :\n"
                f"{url}"
            )

            send_telegram(message)

            print(
                "📲 Alerte Westside envoyée :",
                post_id or url
            )

        except Exception as error:

            print(
                "❌ Erreur envoi Westside :",
                error
            )

            # On conserve l'alerte si Telegram
            # échoue afin de la retenter.
            remaining.append(alert)

    save_westside_alerts(
        remaining
    )

    if remaining:

        print(
            "⚠️ Alertes Westside conservées :",
            len(remaining)
        )

    else:

        print(
            "✅ File Westside vidée."
        )


def main():

    print(
        "📲 AWESOME GOD RADAR — "
        "TELEGRAM DISPATCHER"
    )

    print(
        "📡 Lecture des alertes en attente..."
    )

    send_westside_alerts()

    print(
        "✅ Dispatcher terminé."
    )


if __name__ == "__main__":
    main()
```
