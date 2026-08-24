#!/usr/bin/env python3
"""
Bot EuroDreams - Poste un signal (numéros) sur Telegram automatiquement.
Scrape les statistiques officielles FDJ à chaque exécution.
"""

import os
import random
import re
import requests
from datetime import datetime

# --- Config (via variables d'environnement / GitHub Secrets) ---
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


def fallback_stats():
    """Valeurs de secours si le scraping échoue (dernier relevé connu)."""
    return {
        21: 57, 23: 56, 22: 55, 19: 54, 24: 54, 8: 52, 37: 52,
        3: 51, 4: 51, 15: 50, 30: 50, 33: 48, 28: 45, 38: 45,
    }


def build_signal(stats):
    """Construit une combinaison 'signal' : mélange de numéros chauds + tirage aléatoire."""
    sorted_nums = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    hot_numbers = [n for n, _ in sorted_nums[:10]]

    chosen_hot = random.sample(hot_numbers, k=min(3, len(hot_numbers)))
    remaining = [n for n in range(1, 41) if n not in chosen_hot]
    chosen_random = random.sample(remaining, k=6 - len(chosen_hot))

    combination = sorted(chosen_hot + chosen_random)
    dream_number = random.randint(1, 5)

    return combination, dream_number, hot_numbers[:5]


def format_message(combination, dream_number, top5):
    date_str = datetime.now().strftime("%d/%m/%Y")
    nums_str = " - ".join(f"{n:02d}" for n in combination)
    top5_str = ", ".join(str(n) for n in top5)

    return (
        f"🔮 <b>Signal EuroDreams</b> — {date_str}\n\n"
        f"🎯 Combinaison : <b>{nums_str}</b>\n"
        f"✨ N°Dream : <b>{dream_number}</b>\n\n"
        f"📊 Numéros chauds du moment : {top5_str}\n\n"
        f"<i>Basé sur les statistiques officielles FDJ. "
        f"Le hasard reste le seul maître du jeu 🎲</i>"
    )


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    resp = requests.post(url, data=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def main():
    try:
        stats = fetch_stats()
        if not stats:
            raise ValueError("Aucune donnée extraite du scraping")
    except Exception as e:
        print(f"⚠️ Scraping échoué ({e}), utilisation des valeurs de secours.")
        stats = fallback_stats()

    combination, dream_number, top5 = build_signal(stats)
    message = format_message(combination, dream_number, top5)

    result = send_telegram_message(message)
    print("✅ Message envoyé :", result.get("ok"))


if __name__ == "__main__":
    main()
