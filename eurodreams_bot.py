#!/usr/bin/env python3
"""
Bot EuroDreams - Poste automatiquement sur Telegram la combinaison des
numéros les plus sortis depuis le lancement du jeu (statistiques FDJ).

Ces numéros sont mis à jour manuellement de temps en temps (le scraping
automatique du site FDJ n'est pas fiable). Pour rafraîchir : demande à
Claude de vérifier https://www.fdj.fr/jeux-de-tirage/eurodreams/statistiques
et de mettre à jour TOP_NUMBERS ci-dessous.
"""

import os
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

TOP_NUMBERS = [
    (21, 57), (23, 56), (22, 55), (19, 54), (24, 54), (8, 52),
]
DREAM_NUMBER = 3


def format_message():
    date_str = datetime.now().strftime("%d/%m/%Y")
    combination = sorted(n for n, _ in TOP_NUMBERS)
    nums_str = " - ".join(f"{n:02d}" for n in combination)
    detail_str = ", ".join(f"{n} ({c}x)" for n, c in TOP_NUMBERS)

    return (
        f"🔮 <b>Signal EuroDreams</b> — {date_str}\n\n"
        f"🎯 Combinaison : <b>{nums_str}</b>\n"
        f"✨ N°Dream : <b>{DREAM_NUMBER}</b>\n\n"
        f"📊 Numéros les plus sortis depuis le lancement du jeu\n"
        f"🔥 Détail : {detail_str}\n\n"
        f"<i>Le hasard reste le seul maître du jeu 🎲</i>"
    )


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    resp = requests.post(url, data=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def main():
    message = format_message()
    result = send_telegram_message(message)
    print("✅ Message envoyé :", result.get("ok"))


if __name__ == "__main__":
    main()
