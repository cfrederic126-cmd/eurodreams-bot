#!/usr/bin/env python3
"""
Bot EuroDreams - Poste la combinaison des numéros les plus sortis
sur les 3 derniers mois, automatiquement, sur Telegram.
Source : CSV public de l'historique complet des tirages (mes-resultats-fdj.fr).
"""

import os
import csv
import io
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

CSV_URL = "https://www.mes-resultats-fdj.fr/api/telecharger/eurodreams"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def fetch_recent_draws():
    resp = requests.get(CSV_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8-sig"

    raw_text = resp.text
    print("Apercu de la reponse (300 premiers caracteres):")
    print(raw_text[:300])

    reader = csv.DictReader(io.StringIO(raw_text), delimiter=";")
    print("Colonnes detectees:")
    print(reader.fieldnames)

    cutoff = datetime.now() - timedelta(days=93)
    draws = []

    for row in reader:
        try:
            draw_date = datetime.strptime(row["date"], "%d/%m/%Y")
        except (ValueError, KeyError):
            continue

        if draw_date < cutoff:
            continue

        try:
            main_nums = [int(row["boule_" + str(i)]) for i in range(1, 7)]
            dream = int(row["numero_dream"])
        except (ValueError, KeyError):
            continue

        if all(1 <= n <= 40 for n in main_nums) and 1 <= dream <= 5:
            draws.append((main_nums, dream))

    return draws


def compute_hot_combination(draws):
    number_counts = {}
    dream_counts = {}

    for main_nums, dream in draws:
        for n in main_nums:
            number_counts[n] = number_counts.get(n, 0) + 1
        dream_counts[dream] = dream_counts.get(dream, 0) + 1

    top_numbers = sorted(number_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    combination = sorted(n for n, _ in top_numbers)

    top_dream = 1
    if dream_counts:
        top_dream = max(dream_counts.items(), key=lambda x: x[1])[0]

    return combination, top_dream, top_numbers


def fallback_combination():
    return [4, 12, 17, 20, 22, 30], 3, []


def format_message(combination, dream_number, top_numbers, nb_draws):
    date_str = datetime.now().strftime("%d/%m/%Y")
    nums_str = " - ".join(str(n).zfill(2) for n in combination)

    parts = []
    for n, c in top_numbers:
        parts.append(str(n) + " (" + str(c) + "x)")
    detail_str = ", ".join(parts) if top_numbers else "-"

    message = "Signal EuroDreams - " + date_str + "\n\n"
    message += "Combinaison: " + nums_str + "\n"
    message += "N Dream: " + str(dream_number) + "\n\n"
    message += "Base sur " + str(nb_draws) + " tirages des 3 derniers mois\n"
    message += "Detail: " + detail_str + "\n\n"
    message += "Le hasard reste le seul maitre du jeu"

    return message


def send_telegram_message(text):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    resp = requests.post(url, data=payload, timeout=20)
    resp.raise_for_status()
    return resp.json()


def main():
    try:
        draws = fetch_recent_draws()
        if not draws:
            raise ValueError("Aucun tirage recupere dans le CSV")
        combination, dream_number, top_numbers = compute_hot_combination(draws)
        nb_draws = len(draws)
    except Exception as e:
        print("Recuperation CSV echouee, utilisation de la combinaison de secours.")
        print(str(e))
        combination, dream_number, top_numbers = fallback_combination()
        nb_draws = 0

    message = format_message(combination, dream_number, top_numbers, nb_draws)
    result = send_telegram_message(message)
    print("Message envoye:")
    print(result.get("ok"))


if __name__ == "__main__":
    main()
