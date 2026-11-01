r"""
Lecture et vérification du fichier config.toml.

Les autres scripts font :   from config import charger_config
Pour vérifier le fichier après une modification :
    .venv\Scripts\python config.py
"""

import sys
import tomllib  # inclus dans Python depuis la version 3.11 : rien à installer
from pathlib import Path

FICHIER = Path(__file__).with_name("config.toml")

# Paliers dans l'ordre, tels que l'API Riot les nomme.
PALIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD",
           "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]


def verifier(config):
    """Renvoie la liste des problèmes trouvés (liste vide si tout va bien)."""
    problemes = []

    challenge = config.get("challenge", {})
    debut, fin = challenge.get("debut"), challenge.get("fin")
    if debut is None or fin is None:
        problemes.append("[challenge] : « debut » et « fin » sont obligatoires.")
    elif fin <= debut:
        problemes.append("[challenge] : la fin doit être après le début.")
    elif debut.tzinfo is None or fin.tzinfo is None:
        problemes.append("[challenge] : les dates doivent préciser le fuseau (ex. +01:00).")
    if not isinstance(challenge.get("parties_max"), int) or challenge["parties_max"] <= 0:
        problemes.append("[challenge] : « parties_max » doit être un entier positif.")

    for nom in config.get("bonus", {}).get("paliers", {}):
        if nom not in PALIERS:
            problemes.append(f"[bonus.paliers] : palier inconnu « {nom} » "
                             f"(attendu parmi {', '.join(PALIERS)}).")

    vus = set()
    for i, equipe in enumerate(config.get("equipes", []), start=1):
        joueurs = equipe.get("joueurs", [])
        if len(joueurs) != 2:
            problemes.append(f"Équipe {i} : il faut exactement 2 joueurs.")
        for riot_id in joueurs:
            if riot_id.count("#") != 1:
                problemes.append(f"Équipe {i} : Riot ID invalide « {riot_id} » "
                                 "(forme attendue : Pseudo#TAG).")
            if riot_id.lower() in vus:
                problemes.append(f"Équipe {i} : « {riot_id} » apparaît deux fois.")
            vus.add(riot_id.lower())
    if not config.get("equipes"):
        problemes.append("Aucune équipe définie.")

    noms = {e.get("nom") for e in config.get("equipes", [])}
    for a in config.get("ajustements", []):
        if a.get("equipe") not in noms:
            problemes.append(f"[[ajustements]] : équipe inconnue « {a.get('equipe')} ».")
        if not isinstance(a.get("points"), int):
            problemes.append("[[ajustements]] : « points » doit être un nombre entier.")

    return problemes


def charger_config():
    """Lit config.toml et arrête le programme si le fichier contient une erreur."""
    try:
        with open(FICHIER, "rb") as f:  # tomllib exige une lecture en binaire
            config = tomllib.load(f)
    except tomllib.TOMLDecodeError as erreur:
        sys.exit(f"Erreur de syntaxe dans {FICHIER.name} : {erreur}")

    problemes = verifier(config)
    if problemes:
        sys.exit("Problèmes dans config.toml :\n  - " + "\n  - ".join(problemes))
    return config


if __name__ == "__main__":
    config = charger_config()
    c = config["challenge"]
    print(f"{c['nom']} : du {c['debut']:%d/%m/%Y %H:%M} au {c['fin']:%d/%m/%Y %H:%M}, "
          f"{c['parties_max']} parties max.")
    for equipe in config["equipes"]:
        print(f"  {equipe['nom']} : {' et '.join(equipe['joueurs'])}")
    print("Configuration valide.")
    if any("A_COMPLETER" in j for e in config["equipes"] for j in e["joueurs"]):
        print("Attention : des joueurs restent à compléter.")
