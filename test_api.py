r"""
Script de test : vérifier ce que l'API Riot renvoie pour un joueur.

Utilisation (dans PowerShell, depuis le dossier du projet) :
    $env:RIOT_API_KEY = "RGAPI-..."          # la clé, uniquement pour cette fenêtre
    .venv\Scripts\python test_api.py "Pseudo#TAG"
    .venv\Scripts\python test_api.py "Pseudo#TAG" --nombre 10 --toutes-files

Options :
    --nombre N       nombre de parties à afficher (5 par défaut)
    --toutes-files   toutes les files (normales, ARAM...) et pas seulement la Solo/Duo

Le script fait trois choses :
  1. Riot ID (Pseudo#TAG)  ->  PUUID (identifiant unique et permanent du joueur)
  2. PUUID  ->  rang actuel en Solo/Duo (palier, division, LP)
  3. PUUID  ->  dernières parties, avec le résultat et des informations de vérification
"""

import argparse
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


def lire_arguments():
    """Lit les options passées en ligne de commande."""
    parseur = argparse.ArgumentParser(description="Test de l'API Riot pour un joueur.")
    parseur.add_argument("riot_id", help='Riot ID du joueur, par exemple "Pseudo#TAG"')
    parseur.add_argument("--nombre", type=int, default=5,
                         help="nombre de parties à afficher (5 par défaut)")
    parseur.add_argument("--toutes-files", action="store_true",
                         help="inclure toutes les files, pas seulement la Solo/Duo")
    args = parseur.parse_args()
    if "#" not in args.riot_id:
        parseur.error('le Riot ID doit être de la forme "Pseudo#TAG"')
    return args


def main():
    args = lire_arguments()
    pseudo, tag = args.riot_id.split("#", 1)

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
    solo = [e for e in entrees if e.get("queueType") == "RANKED_SOLO_5x5"]
    if solo:
        e = solo[0]
        print(f"Rang Solo/Duo : {e['tier']} {e['rank']} - {e['leaguePoints']} LP "
              f"({e['wins']} V / {e['losses']} D)\n")
    else:
        print("Aucun rang Solo/Duo (joueur non classé dans cette file).\n")

    # 3. Dernières parties (Solo/Duo seulement, sauf avec --toutes-files)
    params = {"count": args.nombre}
    if not args.toutes_files:
        params["queue"] = FILE_SOLO_DUO
    ids = appeler_api(f"{REGION}/lol/match/v5/matches/by-puuid/{puuid}/ids", params=params)

    portee = "toutes files" if args.toutes_files else "Solo/Duo"
    print(f"{len(ids)} dernière(s) partie(s) ({portee}) :")
    for id_partie in ids:
        partie = appeler_api(f"{REGION}/lol/match/v5/matches/{id_partie}")
        info = partie["info"]
        # On retrouve notre joueur parmi les 10 participants.
        moi = next(p for p in info["participants"] if p["puuid"] == puuid)
        debut = datetime.fromtimestamp(info["gameStartTimestamp"] / 1000)
        resultat = "Victoire" if moi["win"] else "Défaite"
        print(f"  {debut:%d/%m %H:%M}  file {info.get('queueId')}  "
              f"{resultat:8}  {moi['championName']}")

        # Vérification : comment repérer un remake ? On affiche la durée et
        # tous les champs du joueur dont le nom évoque une fin anticipée.
        duree = info.get("gameDuration", 0)
        fins = {cle: valeur for cle, valeur in moi.items()
                if "surrender" in cle.lower() or "remake" in cle.lower()}
        print(f"      durée : {duree // 60} min {duree % 60:02d} s ; champs de fin : {fins}")


if __name__ == "__main__":
    main()
