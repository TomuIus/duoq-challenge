r"""
Relevé : interroge l'API Riot et ajoute les nouvelles données à historique.json.

Utilisation :
    $env:RIOT_API_KEY = "RGAPI-..."
    .venv\Scripts\python releve.py
    .venv\Scripts\python releve.py --depuis 2026-10-20 --fichier historique-test.json

Options (utiles pour tester avant le challenge) :
    --depuis AAAA-MM-JJ   récupérer les parties depuis cette date au lieu du début du challenge
    --fichier NOM         écrire dans un autre fichier que historique.json

Principe : on ne fait qu'AJOUTER à l'historique, on ne modifie jamais ce qui y est.
  - « releves » : un rang Solo/Duo par joueur, noté seulement quand il a changé
                  depuis le relevé précédent (ou la première fois), avec l'heure.
  - « parties » : chaque partie Solo/Duo d'un joueur, enregistrée une seule fois.
Le classement est calculé ailleurs (classement.py), à partir de ce fichier.

L'heure du relevé est écrite à part, dans etat.json : ainsi historique.json ne
change que s'il y a du nouveau, et GitHub Actions ne crée un commit que dans ce cas.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from config import charger_config
from riot_api import RiotAPI


def maintenant():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def charger_historique(chemin):
    if chemin.exists():
        return json.loads(chemin.read_text(encoding="utf-8"))
    return {"puuids": {}, "releves": [], "parties": {}}


def enregistrer_historique(chemin, historique):
    # indent=1 et sort_keys : un fichier lisible, et des différences claires dans Git.
    texte = json.dumps(historique, ensure_ascii=False, indent=1, sort_keys=True)
    chemin.write_text(texte + "\n", encoding="utf-8")


def dernier_rang(historique, riot_id):
    """Dernier rang enregistré pour ce joueur (None s'il n'y en a pas)."""
    for releve in reversed(historique["releves"]):
        if releve["joueur"] == riot_id:
            return releve["rang"]
    return None


def resumer_partie(partie, joueurs_suivis):
    """Ne garde d'une partie que ce dont on a besoin, pour nos joueurs seulement."""
    info = partie["info"]
    debut = info["gameStartTimestamp"]
    # gameEndTimestamp peut manquer dans d'anciennes données : on le recalcule.
    fin = info.get("gameEndTimestamp", debut + info["gameDuration"] * 1000)
    participants = {}
    for p in info["participants"]:
        if p["puuid"] in joueurs_suivis:
            participants[joueurs_suivis[p["puuid"]]] = {
                "camp": p["teamId"],              # 100 = bleu, 200 = rouge
                "victoire": p["win"],
                # Critère vérifié sur un exemple (à revoir) : voir decisions.md.
                "remake": p.get("gameEndedInEarlySurrender", False),
                "champion": p["championName"],
                # Poste joué (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY) ; vide si inconnu.
                "poste": p.get("teamPosition") or p.get("individualPosition") or "",
            }
    return {"debut_ms": debut, "fin_ms": fin, "duree_s": info["gameDuration"],
            "file": info["queueId"], "joueurs": participants}


def main():
    parseur = argparse.ArgumentParser(description="Relevé des rangs et des parties.")
    parseur.add_argument("--depuis", help="date de début des parties (AAAA-MM-JJ), pour tester")
    parseur.add_argument("--fichier", default="historique.json", help="fichier d'historique")
    args = parseur.parse_args()

    config = charger_config()
    riot = RiotAPI(config["riot"]["region"], config["riot"]["plateforme"])
    chemin = Path(__file__).parent / args.fichier  # fichier rangé à côté du script
    historique = charger_historique(chemin)

    if args.depuis:
        depuis = datetime.fromisoformat(args.depuis).replace(tzinfo=timezone.utc)
    else:
        depuis = config["challenge"]["debut"]
    depuis_s = int(depuis.timestamp())

    joueurs = [j for e in config["equipes"] for j in e["joueurs"]]
    joueurs_suivis = {}  # PUUID -> Riot ID

    for riot_id in joueurs:
        if "A_COMPLETER" in riot_id:
            continue  # joueur pas encore renseigné dans config.toml
        # Le PUUID ne change jamais : on le garde pour éviter une requête à chaque relevé.
        puuid = historique["puuids"].get(riot_id) or riot.puuid(riot_id)
        if puuid is None:
            print(f"  ! Riot ID introuvable : {riot_id} (vérifiez config.toml)")
            continue
        historique["puuids"][riot_id] = puuid
        joueurs_suivis[puuid] = riot_id

        rang = riot.rang_solo(puuid)
        deja_releve = any(r["joueur"] == riot_id for r in historique["releves"])
        # On note le rang la première fois, puis seulement quand il change.
        if not deja_releve or rang != dernier_rang(historique, riot_id):
            historique["releves"].append({"joueur": riot_id, "heure": maintenant(), "rang": rang})
            print(f"  {riot_id} : nouveau rang {rang}")
        else:
            print(f"  {riot_id} : rang inchangé")

    # Parties : un duo joue les mêmes parties, on ne télécharge chacune qu'une fois.
    nouvelles = 0
    for puuid, riot_id in joueurs_suivis.items():
        for id_partie in riot.ids_parties(puuid, config["riot"]["file_id"], depuis_s):
            if id_partie in historique["parties"]:
                continue
            partie = riot.partie(id_partie)
            if partie is None:
                continue  # pas encore publiée par Riot : on réessaiera au prochain relevé
            historique["parties"][id_partie] = resumer_partie(partie, joueurs_suivis)
            nouvelles += 1

    historique.pop("dernier_releve", None)  # ancien emplacement, désormais dans etat.json
    enregistrer_historique(chemin, historique)
    etat = Path(__file__).parent / "etat.json"
    etat.write_text(json.dumps({"dernier_releve": maintenant()}) + "\n", encoding="utf-8")
    print(f"{nouvelles} nouvelle(s) partie(s), {riot.nb_requetes} requête(s) envoyée(s). "
          f"Historique enregistré dans {chemin.name}.")


if __name__ == "__main__":
    main()
