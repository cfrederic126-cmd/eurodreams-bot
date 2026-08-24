#!/usr/bin/env python3
"""
Bot EuroDreams - Poste la combinaison des numéros les plus sortis
(statistiques officielles FDJ depuis le lancement du jeu), automatiquement, sur Telegram.
"""

import os
import re
import requests
from datetime import datetime

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

FDJ_STATS_URL = "https://www.fdj.fr/jeux-de-tirage/eurodreams/statistiques"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def fetch_stats():
    """Scrape le tableau des numéros (nombre de sorties) depuis la page stats FDJ."""
    resp = requests.get(FDJ_STATS_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    html = resp.text

    rows = re.findall(
        r"<td[^>]*>\s*(\d{1,2})\s*</td>\s*<td[^>]*>\s*(\d{1,3})\s*</td>",
        html,
    )

    stats = {}
    for num_str, count_str in rows:
        num = int(num_str)
        count = int(count_str)
        if 1 <= num <= 40:
            stats[num] = count

    return stats


def fallback_combination():
    """Combinaison de secours si le scraping échoue totalement."""
    return [4, 12, 17, 20, 22, 30], 3, []


def compute_hot_combination(stats):
    """Retourne les 6 numéros les plus sortis depuis le lancement du jeu."""
    top_numbers = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:6]
    combination = sorted(n for n, _ in top_numbers)
    return combination, top_numbers


def format_message(combination, dream_number, top_numbers):
    date_str = datetime.now().strftime("%d/%m/%Y")
    nums_str = " - ".join(f"{n:02d}" for n in combination)
    detail_str = ", ".join(f"{n} ({c}x)" for n, c in top_numbers) if top_numbers else "—"

    return (
        f"🔮 <b>Signal EuroDreams</b> — {date_str}\n\n"
        f"🎯 Combinaison : <b>{nums_str}</b>\n"
        f"✨ N°Dream : <b>{dream_number}</b>\n\n"
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
    try:
        stats = fetch_stats()
        if not stats:
            raise ValueError("Aucune statistique récupérée")
        combination, top_numbers = compute_hot_combination(stats)
        dream_number = 3
    except Exception as e:
        print(f"⚠️ Scraping échoué ({e}), utilisation de la combinaison de secours.")
        combination, dream_number, top_numbers = fallback_combination()

    message = format_message(combination, dream_number, top_numbers)
    result = send_telegram_message(message)
    print("✅ Message envoyé :", result.get("ok"))


if __name__ == "__main__":
    main()
