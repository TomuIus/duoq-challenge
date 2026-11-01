r"""
Premier script de test : vérifier ce que l'API Riot renvoie pour un joueur.

Utilisation (dans PowerShell, depuis le dossier du projet) :
    $env:RIOT_API_KEY = "RGAPI-..."          # la clé, uniquement pour cette fenêtre
    .venv\Scripts\python test_api.py "Pseudo#TAG"

Le script fait trois choses :
  1. Riot ID (Pseudo#TAG)  ->  PUUID (identifiant unique et permanent du joueur)
  2. PUUID  ->  rang actuel en Solo/Duo (palier, division, LP)
  3. PUUID  ->  5 dernières parties classées Solo/Duo, avec le résultat de chacune
"""

import os
import sys
import time
from datetime import datetime
from urllib.parse import quote

import requests

# --- Adresses de l'API -------------------------------------------------------
# Riot sépare deux types d'adresses :
#  - « régionale » (europe) pour les comptes et les parties,
#  - « plateforme » (euw1) pour les classements.
# Hypothèse : tous les joueurs sont sur EUW.
REGION = "https://europe.api.riotgames.com"
PLATEFORME = "https://euw1.api.riotgames.com"

FILE_SOLO_DUO = 420  # identifiant de la file « Classée Solo/Duo » dans les parties


def appeler_api(url, params=None):
    """Envoie une requête à l'API Riot et renvoie la réponse décodée (JSON)."""
    cle = os.environ.get("RIOT_API_KEY")
    if not cle:
        sys.exit("Erreur : la variable d'environnement RIOT_API_KEY n'est pas définie.")

    for essai in range(1, 6):
        # La clé est transmise dans un en-tête HTTP, jamais dans l'adresse.
        reponse = requests.get(url, headers={"X-Riot-Token": cle}, params=params, timeout=10)

        if reponse.status_code == 429:
            # Trop de requêtes : Riot indique souvent combien de secondes attendre
            # dans l'en-tête « Retry-After ». Sinon, on attend 5 s, puis 10 s, etc.
            attente = int(reponse.headers.get("Retry-After", 5 * essai))
            print(f"  (limite de débit atteinte, nouvel essai dans {attente} s...)")
            time.sleep(attente)
            continue

        if reponse.status_code != 200:
            # 401/403 : clé absente, invalide ou expirée ; 404 : introuvable.
            sys.exit(f"Erreur {reponse.status_code} pour {url}\n{reponse.text}")
        return reponse.json()

    sys.exit(f"Abandon après 5 essais (limite de débit) pour {url}")


def main():
    if len(sys.argv) != 2 or "#" not in sys.argv[1]:
        sys.exit('Utilisation : python test_api.py "Pseudo#TAG"')

    pseudo, tag = sys.argv[1].split("#", 1)

    # 1. Riot ID -> PUUID
    compte = appeler_api(
        f"{REGION}/riot/account/v1/accounts/by-riot-id/{quote(pseudo)}/{quote(tag)}"
    )
    puuid = compte["puuid"]
    print(f"Joueur : {compte['gameName']}#{compte['tagLine']}")
    print(f"PUUID  : {puuid[:12]}...  (tronqué à l'affichage)\n")

    # 2. Rang actuel. La réponse est une liste : une entrée par file classée
    #    (Solo/Duo, Flex...). Elle peut être vide si le joueur n'est pas classé.
    entrees = appeler_api(f"{PLATEFORME}/lol/league/v4/entries/by-puuid/{puuid}")
    print("Réponse brute du classement :", entrees, "\n")
    solo = [e for e in entrees if e.get("queueType") == "RANKED_SOLO_5x5"]
    if solo:
        e = solo[0]
        print(f"Rang Solo/Duo : {e['tier']} {e['rank']} - {e['leaguePoints']} LP "
              f"({e['wins']} V / {e['losses']} D)\n")
    else:
        print("Aucun rang Solo/Duo (joueur non classé dans cette file).\n")

    # 3. Dernières parties classées Solo/Duo
    ids = appeler_api(
        f"{REGION}/lol/match/v5/matches/by-puuid/{puuid}/ids",
        params={"queue": FILE_SOLO_DUO, "count": 5},
    )
    print(f"{len(ids)} dernière(s) partie(s) Solo/Duo :")
    for id_partie in ids:
        partie = appeler_api(f"{REGION}/lol/match/v5/matches/{id_partie}")
        info = partie["info"]
        # On retrouve notre joueur parmi les 10 participants.
        moi = next(p for p in info["participants"] if p["puuid"] == puuid)
        debut = datetime.fromtimestamp(info["gameStartTimestamp"] / 1000)
        resultat = "Victoire" if moi["win"] else "Défaite"
        print(f"  {debut:%d/%m %H:%M}  {resultat:8}  {moi['championName']}")

        # Vérification : existe-t-il un champ lié aux LP dans les données du joueur ?
        suspects = [cle for cle in moi
                    if any(mot in cle.lower() for mot in ("lp", "league", "rank", "tier"))]
        print(f"      champs évoquant des LP ou un rang : {suspects or 'aucun'}")


if __name__ == "__main__":
    main()
