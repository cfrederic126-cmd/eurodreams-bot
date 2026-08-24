#!/usr/bin/env python3
"""
Bot EuroDreams - Poste la combinaison des numéros les plus sortis
sur les 3 derniers mois, automatiquement, sur Telegram.
"""

import os
import re
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

HISTORY_URL = "https://www.tirage-euromillions.net/eurodreams/historique/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def fetch_recent_draws():
    """
    Scrape la page d'historique et retourne la liste des tirages
    (6 numéros + N°Dream) des tirages datés, en filtrant sur les 3
    derniers mois.
    """
    resp = requests.get(HISTORY_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    html = resp.text

    dates = re.findall(r"(\d{2}/\d{2}/\d{4})", html)
    number_rows = re.findall(r"(\d{1,2}(?:\s+\d{1,2}){6})", html)

    cutoff = datetime.now() - timedelta(days=93)  # ~3 mois

    draws = []
    for date_str, row in zip(dates, number_rows):
        try:
            draw_date = datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            continue
        if draw_date < cutoff:
            continue
        nums = [int(n) for n in row.split()]
        if len(nums) == 7:
            main_nums = nums[:6]
            dream = nums[6]
            if all(1 <= n <= 40 for n in main_nums) and 1 <= dream <= 5:
                draws.append((main_nums, dream))

    return draws


def compute_hot_combination(draws):
    """Compte la fréquence des numéros et du N°Dream sur les tirages fournis,
    puis retourne les 6 numéros et le N°Dream les plus fréquents."""
    number_counts = {}
    dream_counts = {}

    for main_nums, dream in draws:
        for n in main_nums:
            number_counts[n] = number_counts.get(n, 0) + 1
        dream_counts[dream] = dream_counts.get(dream, 0) + 1

    top_numbers = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    combination = sorted(n for n, _ in top_numbers)

    if dream_counts:
        top_dream = max(dream_counts.items(), key=lambda x: x[1])[0]
    else:
        top_dream = 1

    return combination, top_dream, top_numbers


def fallback_combination():
    """Combinaison de secours si le scraping échoue totalement."""
    return [4, 12, 17, 20, 22, 30], 3, []


def format_message(combination, dream_number, top_numbers, nb_draws):
    date_str = datetime.now().strftime("%d/%m/%Y")
    nums_str = " - ".join(f"{n:02d}" for n in combination)
    detail_str = ", ".join(f"{n} ({c}x)" for n, c in top_numbers) if top_numbers else "—"

    return (
        f"🔮 <b>Signal EuroDreams</b> — {date_str}\n\n"
        f"🎯 Combinaison : <b>{nums_str}</b>\n"
        f"✨ N°Dream : <b>{dream_number}</b>\n\n"
        f"📊 Basé sur {nb_draws} tirages des 3 derniers mois\n"
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
        draws = fetch_recent_draws()
        if not draws:
            raise ValueError("Aucun tirage récupéré")
        combination, dream_number, top_numbers = compute_hot_combination(draws)
        nb_draws = len(draws)
    except Exception as e:
        print(f"⚠️ Scraping échoué ({e}), utilisation de la combinaison de secours.")
        combination, dream_number, top_numbers = fallback_combination()
        nb_draws = 0

    message = format_message(combination, dream_number, top_numbers, nb_draws)
    result = send_telegram_message(message)
    print("✅ Message envoyé :", result.get("ok"))


if __name__ == "__main__":
    main()
