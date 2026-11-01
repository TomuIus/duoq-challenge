"""
Accès à l'API Riot : tout ce qui parle à Riot passe par ce module.

La clé est lue dans la variable d'environnement RIOT_API_KEY
(sur votre ordinateur : $env:RIOT_API_KEY = "..." ; sur GitHub : un « secret »).
"""

import os
import sys
import time
from urllib.parse import quote

import requests


class RiotAPI:
    def __init__(self, region, plateforme):
        # Riot sépare deux types d'adresses :
        #  - « régionale » (ex. europe) pour les comptes et les parties,
        #  - « plateforme » (ex. euw1) pour les classements.
        self.url_region = f"https://{region}.api.riotgames.com"
        self.url_plateforme = f"https://{plateforme}.api.riotgames.com"
        # .strip() retire les espaces et retours à la ligne collés par erreur autour de la clé.
        self.cle = (os.environ.get("RIOT_API_KEY") or "").strip()
        if not self.cle:
            sys.exit("Erreur : la variable d'environnement RIOT_API_KEY n'est pas définie.")
        self.nb_requetes = 0  # pour vérifier qu'on reste loin des limites

    def _get(self, url, params=None):
        """Envoie une requête et renvoie la réponse JSON (None si introuvable)."""
        for essai in range(1, 6):
            self.nb_requetes += 1
            # La clé est transmise dans un en-tête HTTP, jamais dans l'adresse.
            reponse = requests.get(url, headers={"X-Riot-Token": self.cle},
                                   params=params, timeout=10)

            if reponse.status_code == 429:
                # Trop de requêtes : Riot indique souvent combien de secondes
                # attendre dans l'en-tête « Retry-After ». Sinon : 5 s, 10 s...
                attente = int(reponse.headers.get("Retry-After", 5 * essai))
                print(f"  (limite de débit atteinte, nouvel essai dans {attente} s...)")
                time.sleep(attente)
                continue
            if reponse.status_code == 404:
                return None
            if reponse.status_code != 200:
                # 401/403 : clé absente, invalide ou expirée.
                sys.exit(f"Erreur {reponse.status_code} pour {url}\n{reponse.text}")
            return reponse.json()

        sys.exit(f"Abandon après 5 essais (limite de débit) pour {url}")

    def puuid(self, riot_id):
        """Riot ID (Pseudo#TAG) -> PUUID, l'identifiant permanent du joueur."""
        pseudo, tag = riot_id.split("#", 1)
        compte = self._get(f"{self.url_region}/riot/account/v1/accounts/by-riot-id/"
                           f"{quote(pseudo)}/{quote(tag)}")
        return compte["puuid"] if compte else None

    def rang_solo(self, puuid):
        """Rang Solo/Duo actuel, ou None si le joueur n'est pas classé dans cette file."""
        entrees = self._get(f"{self.url_plateforme}/lol/league/v4/entries/by-puuid/{puuid}")
        for e in entrees or []:
            if e.get("queueType") == "RANKED_SOLO_5x5":
                return {"palier": e["tier"], "division": e["rank"], "lp": e["leaguePoints"],
                        "victoires": e["wins"], "defaites": e["losses"]}
        return None

    def ids_parties(self, puuid, file_id, depuis_secondes):
        """Identifiants des parties d'une file, commencées après une date (en secondes)."""
        return self._get(f"{self.url_region}/lol/match/v5/matches/by-puuid/{puuid}/ids",
                         params={"queue": file_id, "startTime": depuis_secondes,
                                 "count": 100}) or []

    def partie(self, id_partie):
        """Détail complet d'une partie."""
        return self._get(f"{self.url_region}/lol/match/v5/matches/{id_partie}")
