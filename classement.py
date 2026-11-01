r"""
Classement : calcule les scores à partir de historique.json et config.toml,
puis écrit classement.json (le fichier que la page web affichera).

Utilisation :
    .venv\Scripts\python classement.py
    .venv\Scripts\python classement.py --fichier historique-test.json --depuis 2026-10-20

Ce script n'appelle pas l'API Riot : il ne fait que des calculs. On peut donc le
relancer autant de fois qu'on veut, par exemple après avoir modifié un bonus.

Règles appliquées (voir decisions.md) :
  - points LP = rang final - rang de départ, sur une échelle continue ;
  - bonus de palier selon le palier final (paliers au-dessus du palier de départ) ;
  - bonus de série à chaque joueur de l'équipe ayant la plus longue série de victoires ;
  - remakes ignorés (ni partie, ni victoire, ni défaite, ni série cassée) ;
  - au-delà de 50 parties ou après l'heure de fin : score gelé, partie signalée.
"""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from config import PALIERS, charger_config

PARIS = ZoneInfo("Europe/Paris")
DIVISIONS = {"IV": 0, "III": 100, "II": 200, "I": 300}
PALIERS_SANS_DIVISION = {"MASTER", "GRANDMASTER", "CHALLENGER"}


# --- Échelle continue des rangs ------------------------------------------------

def lp_absolus(rang):
    """Convertit un rang en nombre de LP depuis Fer IV 0 LP.

    Fer IV 0 LP = 0, Fer III 0 LP = 100, ..., Bronze IV 0 LP = 400, etc.
    Maître, Grand Maître et Challenger n'ont pas de division : leurs LP
    continuent à partir de Maître 0 LP (= 2800, juste après Diamant I 100 LP).
    """
    if rang["palier"] in PALIERS_SANS_DIVISION:
        return PALIERS.index("MASTER") * 400 + rang["lp"]
    return PALIERS.index(rang["palier"]) * 400 + DIVISIONS[rang["division"]] + rang["lp"]


def bonus_paliers(depart, final, bonus):
    """Somme des bonus des paliers au-dessus du palier de départ, jusqu'au palier final."""
    i_depart, i_final = PALIERS.index(depart["palier"]), PALIERS.index(final["palier"])
    return sum(bonus.get(p, 0) for p in PALIERS[i_depart + 1:i_final + 1])


NOMS_PALIERS = {"IRON": "Fer", "BRONZE": "Bronze", "SILVER": "Argent", "GOLD": "Or",
                "PLATINUM": "Platine", "EMERALD": "Émeraude", "DIAMOND": "Diamant",
                "MASTER": "Maître", "GRANDMASTER": "Grand Maître", "CHALLENGER": "Challenger"}


def texte_rang(rang):
    """Rang lisible en français, par exemple « Or II 75 LP »."""
    if rang is None:
        return "non classé"
    nom = NOMS_PALIERS[rang["palier"]]
    if rang["palier"] in PALIERS_SANS_DIVISION:
        return f"{nom} {rang['lp']} LP"
    return f"{nom} {rang['division']} {rang['lp']} LP"


# --- Lecture de l'historique ----------------------------------------------------

def releves_du_joueur(historique, riot_id):
    """Relevés d'un joueur, du plus ancien au plus récent, avec l'heure en datetime."""
    return [(datetime.fromisoformat(r["heure"]), r["rang"])
            for r in historique["releves"] if r["joueur"] == riot_id]


def rang_de_depart(releves, debut):
    """Dernier rang connu au début du challenge ; sinon, premier rang apparu après.

    Avec la règle des placements, personne n'est classé au début : c'est donc le
    rang affiché après la première partie de placement qui sert de départ.
    """
    avant = [rang for heure, rang in releves if heure <= debut]
    if avant and avant[-1] is not None:
        return avant[-1]
    for heure, rang in releves:
        if heure > debut and rang is not None:
            return rang
    return None


def rang_final(releves, partie_exclue, alertes, riot_id):
    """Rang à retenir pour le score.

    Sans partie exclue : le dernier rang connu.
    Avec une partie exclue (51e partie, ou partie commencée après la fin) :
    le dernier rang relevé AVANT la fin de cette partie, c'est-à-dire avant
    qu'elle ne modifie les LP. Si aucun relevé ne tombe entre la dernière
    partie comptée et la partie exclue, le score gelé n'est pas garanti.
    """
    if not releves:
        return None
    if partie_exclue is None:
        return releves[-1][1]
    limite = datetime.fromtimestamp(partie_exclue["fin_ms"] / 1000, timezone.utc)
    avant = [(heure, rang) for heure, rang in releves if heure < limite]
    if not avant:
        return None
    dernier_compte = partie_exclue.get("fin_derniere_comptee")
    if dernier_compte and avant[-1][0] < dernier_compte:
        alertes.append(f"{riot_id} : aucun relevé entre la dernière partie comptée et la "
                       "partie exclue. Score gelé approximatif, à corriger à la main.")
    return avant[-1][1]


# --- Calcul pour une équipe -------------------------------------------------------

def analyser_equipe(equipe, historique, config, debut, fin):
    joueurs = equipe["joueurs"]
    parties_max = config["challenge"]["parties_max"]
    alertes, liste = [], []

    # Parties de l'équipe (au moins un des deux joueurs), dans l'ordre chronologique.
    parties = sorted(
        (p for p in historique["parties"].values()
         if p["debut_ms"] >= debut.timestamp() * 1000
         and any(j in p["joueurs"] for j in joueurs)),
        key=lambda p: p["debut_ms"])

    comptees, partie_exclue = [], None
    for p in parties:
        presents = {j: p["joueurs"][j] for j in joueurs if j in p["joueurs"]}
        un_joueur = next(iter(presents.values()))
        debut_partie = datetime.fromtimestamp(p["debut_ms"] / 1000, PARIS)
        ligne = {"date": debut_partie.isoformat(timespec="minutes"),
                 "champions": {j: d["champion"] for j, d in presents.items()},
                 "signalements": []}

        if any(d["remake"] for d in presents.values()):
            ligne["resultat"] = "Remake"
            liste.append(ligne)
            continue  # un remake ne compte pour rien
        ligne["resultat"] = "Victoire" if un_joueur["victoire"] else "Défaite"

        # Règle du duo : les deux joueurs doivent être dans la partie, dans le même camp.
        if len(presents) < 2 or len({d["camp"] for d in presents.values()}) > 1:
            ligne["signalements"].append("jouée sans le coéquipier")
            alertes.append(f"Partie du {debut_partie:%d/%m %H:%M} jouée sans le coéquipier.")

        if debut_partie >= fin:
            ligne["signalements"].append("commencée après la fin du challenge")
        elif len(comptees) >= parties_max:
            ligne["signalements"].append(f"au-delà de {parties_max} parties")
        else:
            comptees.append(p)
            ligne["comptee"] = True

        if not ligne.get("comptee"):
            alertes.append(f"Partie du {debut_partie:%d/%m %H:%M} non comptée "
                           f"({', '.join(ligne['signalements'])}).")
            if partie_exclue is None:
                partie_exclue = dict(p)
                if comptees:
                    partie_exclue["fin_derniere_comptee"] = datetime.fromtimestamp(
                        comptees[-1]["fin_ms"] / 1000, timezone.utc)
        liste.append(ligne)

    # Plus longue série de victoires (les remakes ont déjà été écartés).
    serie = meilleure = 0
    for p in comptees:
        victoire = next(p["joueurs"][j]["victoire"] for j in joueurs if j in p["joueurs"])
        serie = serie + 1 if victoire else 0
        meilleure = max(meilleure, serie)

    # Score de chaque joueur.
    details, total = [], 0
    for riot_id in joueurs:
        releves = releves_du_joueur(historique, riot_id)
        depart = rang_de_depart(releves, debut)
        final = rang_final(releves, partie_exclue, alertes, riot_id)
        if depart is None or final is None:
            points_lp = points_paliers = 0
        else:
            points_lp = lp_absolus(final) - lp_absolus(depart)
            points_paliers = bonus_paliers(depart, final, config["bonus"]["paliers"])
        total += points_lp + points_paliers
        details.append({"joueur": riot_id, "rang_depart": texte_rang(depart),
                        "rang_actuel": texte_rang(final),
                        "palier_depart": depart["palier"] if depart else None,
                        "palier_actuel": final["palier"] if final else None,
                        "points_lp": points_lp, "bonus_paliers": points_paliers})

    # Ajustements manuels saisis dans config.toml (pénalités, corrections).
    ajustements = [a for a in config.get("ajustements", []) if a["equipe"] == equipe["nom"]]
    total += sum(a["points"] for a in ajustements)

    par_jour = Counter(datetime.fromtimestamp(p["debut_ms"] / 1000, PARIS).strftime("%Y-%m-%d")
                       for p in comptees)
    return {"nom": equipe["nom"], "joueurs": details, "score_sans_serie": total,
            "parties_jouees": len(comptees), "parties_restantes": max(0, parties_max - len(comptees)),
            "parties_par_jour": dict(sorted(par_jour.items())), "meilleure_serie": meilleure,
            "ajustements": ajustements, "parties": liste, "alertes": alertes}


def main():
    parseur = argparse.ArgumentParser(description="Calcul du classement.")
    parseur.add_argument("--fichier", default="historique.json", help="fichier d'historique")
    parseur.add_argument("--depuis", help="date de début (AAAA-MM-JJ), pour tester")
    parseur.add_argument("--sortie", default="classement.json", help="fichier de résultats")
    args = parseur.parse_args()

    config = charger_config()
    dossier = Path(__file__).parent
    historique = json.loads((dossier / args.fichier).read_text(encoding="utf-8"))
    debut = (datetime.fromisoformat(args.depuis).replace(tzinfo=PARIS) if args.depuis
             else config["challenge"]["debut"])
    fin = config["challenge"]["fin"]

    # Heure du dernier relevé : dans etat.json (écrit par releve.py), s'il existe.
    fichier_etat = dossier / "etat.json"
    dernier_releve = (json.loads(fichier_etat.read_text(encoding="utf-8"))["dernier_releve"]
                      if fichier_etat.exists() else historique.get("dernier_releve"))

    equipes = [analyser_equipe(e, historique, config, debut, fin) for e in config["equipes"]]

    # Bonus de série : à chaque joueur de la (ou des) équipe(s) ayant la plus longue série.
    record = max((e["meilleure_serie"] for e in equipes), default=0)
    for e in equipes:
        gagne = record > 0 and e["meilleure_serie"] == record
        e["bonus_serie"] = config["bonus"]["serie_par_joueur"] * len(e["joueurs"]) if gagne else 0
        e["score"] = e.pop("score_sans_serie") + e["bonus_serie"]

    equipes.sort(key=lambda e: e["score"], reverse=True)
    resultat = {"challenge": config["challenge"]["nom"],
                "calcule_le": datetime.now(PARIS).isoformat(timespec="seconds"),
                "dernier_releve": dernier_releve,
                "debut": debut.isoformat(), "fin": fin.isoformat(),
                "record_serie": record,
                # Rappel des règles, pour que la page les affiche sans lire config.toml.
                "regles": {"parties_max": config["challenge"]["parties_max"],
                           "serie_par_joueur": config["bonus"]["serie_par_joueur"],
                           "paliers": config["bonus"]["paliers"]},
                "equipes": equipes}
    (dossier / args.sortie).write_text(
        json.dumps(resultat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for rang, e in enumerate(equipes, start=1):
        print(f"{rang}. {e['nom']} : {e['score']} pts "
              f"({e['parties_jouees']} parties, série max {e['meilleure_serie']})")
        for j in e["joueurs"]:
            print(f"     {j['joueur']} : {j['rang_depart']} -> {j['rang_actuel']} "
                  f"({j['points_lp']:+} LP, +{j['bonus_paliers']} paliers)")
        for a in e["alertes"]:
            print(f"     ! {a}")
    print(f"Résultats enregistrés dans {args.sortie}.")


if __name__ == "__main__":
    main()
