# DuoQ Challenge – Décisions

## Reprendre une session (aide-mémoire)
À relire en début de session : l'utilisateur a demandé à être remis dans le bain (quoi lancer, où on en est).

**Où on en est (2 novembre 2026, 11 h 14) :** tout le système fonctionne (relevé, calcul, page, automatisation, correction manuelle du rang de départ, LP par partie, fond teinté des parties, licence MIT, icônes de champion et de poste par joueur). Les 3 équipes sont renseignées dans `config.toml` ; les 6 Riot ID sont trouvés par l'API ; la détection du duo, les LP par partie et les icônes (thèmes clair et sombre) sont vérifiés sur de vraies parties. Dernière modification (décision 33) à envoyer sur GitHub si ce n'est pas fait (`releve.py`, `classement.py`, `index.html`). Le lancement automatique est désactivé jusqu'en janvier. Il ne reste que la « Checklist avant le challenge » et d'éventuelles améliorations.

**Ouvrir l'environnement (PowerShell) :**
```powershell
cd $HOME\Documents\duoq-challenge
git pull                                     # récupérer ce que GitHub a pu enregistrer
$env:RIOT_API_KEY = "RGAPI-..."              # clé personnelle, seulement pour les tests en local
```
Puis ouvrir le dossier dans VSCodium (Fichier → Ouvrir le dossier). Ne jamais coller la vraie clé dans la conversation (remplacer par `RGAPI-...`).

**Commandes utiles :**
- Vérifier la configuration : `.venv\Scripts\python config.py`
- Explorer l'API : `.venv\Scripts\python test_api.py "Tomulus#ÀCAB" --nombre 7 [--toutes-files]`
- Relevé de test : `.venv\Scripts\python releve.py --depuis 2026-10-20 --fichier historique-test.json`
- Classement de test : `.venv\Scripts\python classement.py --fichier historique-test.json --depuis 2026-10-20 --sortie classement-test.json`
- Test des LP sur une partie : relevé avant la partie, relevé ~5 min après, puis classement (même `--fichier`, `--depuis` = date du jour). Les LP n'apparaissent qu'avec au moins deux relevés encadrant la partie.
- Voir la page en local : `.venv\Scripts\python -m http.server` puis http://localhost:8000/index.html?donnees=classement-test.json (Ctrl+C pour arrêter)
- Enregistrer : `git pull`, `git add <fichiers>`, `git commit -m "..."`, `git push`
- Relevé en ligne : onglet Actions du dépôt → « Relevé et publication » → Run workflow
- Site : https://tomuius.github.io/duoq-challenge/

**Méthode de travail souhaitée :** une question à la fois, 2-3 options avec avantages/inconvénients et une recommandation, l'utilisateur décide ; expliquer ce qui est fait ; dire ce qui n'est pas vérifié. Pour les choix visuels, montrer une comparaison en image des options.

## Contexte
- Refaire le SoloQ Challenge de début 2026 (75 parties sur 15 jours, plafond de parties par jour, suivi sur Excel), cette fois en duo.
- 6 joueurs, 3 équipes de 2. Serveur : EUW (les 6 comptes sont trouvés sur euw1).
- Équipes : Équipe 1 = WifeBuffed#WIF et WillOfortune#5090 ; Équipe 2 = Tomulus#ÀCAB (l'utilisateur) et Navybloo#EUW ; Équipe 3 = JesuisVEXée#6858 et Heltrik#Htrik.
- Le site sera surtout consulté sur PC.
- **Site en ligne : https://tomuius.github.io/duoq-challenge/** (mis en service le 2 novembre 2026).

## Règlement transmis (notes d'un participant, dates encore modifiables)
- Dates : 22 janvier – 29 janvier 2027. Soirée finale le vendredi 29 janvier, en présentiel.
- 50 parties maximum sur la semaine, à étaler.
- 1 LP gagné/perdu = 1 point ; score = différence de LP entre le début et la fin. Points cumulés entre les deux joueurs du duo.
- Bonus de palier atteint : Bronze 10, Argent 20, Or 30, Platine 40, Émeraude 50. Seuls les paliers effectivement passés pendant le challenge comptent.
- Joueur le mieux classé : +50 (supprimé pour l'instant, voir décision 9). Joueur avec la plus longue série de victoires : +50.
- Note du participant (non vérifiée) : Riot empêche le duo au-delà d'un certain écart de rang.

## Décisions prises (1er et 2 novembre 2026)
1. **Architecture : option A.** Script Python lancé par GitHub Actions (toutes les ~10 min), qui interroge l'API Riot et écrit un fichier de données. Page statique sur GitHub Pages. **Clé Riot personnelle obtenue le 1er novembre 2026** (approuvée automatiquement ; régénérée le 2 novembre après avoir été collée par erreur dans la conversation ; secret GitHub mis à jour).
2. **Règle duo :** pendant le challenge, chaque joueur joue ses parties classées uniquement avec son coéquipier.
3. **Score d'équipe :** somme des deux scores individuels (LP + bonus de paliers) + bonus de série de victoires. Les deux coéquipiers ont les mêmes résultats.
4. **Bonus de palier :** dépend du palier actuel (gagné en montant, perdu en redescendant, regagné en remontant). Le score ne dépend donc que du rang de départ et du rang actuel.
5. **Placements :** aucune partie classée entre le début de la saison et le début du challenge ; tout le monde commence le challenge par ses parties de placement.
6. **Rang de départ :** celui affiché après la première partie de placement (règle de l'an dernier). Pour le site : le premier rang qui apparaît dans l'API. Les placements suivants comptent dans les points et dans les 50 parties.
7. **Bonus de série :** 50 points pour chacun des deux coéquipiers de l'équipe ayant la plus longue série de victoires (100 pour l'équipe). En cas d'égalité, toutes les équipes à égalité reçoivent le bonus complet. Provisoire, à rediscuter. Remarque : il est attribué même si les parties de la série ont été jouées sans le coéquipier (ces parties sont signalées ; ajustement manuel au besoin).
8. **Paramètres modifiables :** toutes les valeurs du règlement (bonus, plafonds, dates) doivent être faciles à changer → regroupées dans un fichier de configuration.
9. **Bonus « mieux classé » : supprimé pour l'instant** (les paliers élevés rapportent déjà plus de points). Pourra être réactivé via la configuration.
10. **Paliers au-delà d'Émeraude :** suite logique +10 par palier (Diamant 60, Maître 70, Grand Maître 80, Challenger 90). Un joueur a déjà été proche de Diamant.
11. **Dépassement des 50 parties :** score gelé au premier relevé après la 50e partie, toute partie supplémentaire signalée, correction manuelle possible. Compteur de parties restantes affiché.
12. **Pas de plafond quotidien chiffré :** simple recommandation d'étaler les parties ; le site affiche le nombre de parties jouées par jour.
13. **Horaires (provisoires) :** du vendredi 22 janvier 2027 à 0 h au vendredi 29 janvier 2027 à 23 h 59, heure de Paris. Très probablement modifiés plus tard.
14. **Fin du challenge :** une partie compte si elle a commencé avant l'heure de fin. Interdit de lancer une partie après ; le site signale toute partie commencée après l'heure de fin. Score final relevé une fois ces parties terminées.
15. **Partie jouée sans le coéquipier :** signalée sur le site ; le groupe décide ensemble d'un éventuel ajustement de points, saisi à la main.
16. **Environnement de développement :** sur l'ordinateur de l'utilisateur (Windows), avec Python (via le Python install manager), Git et VSCodium, installés avec winget. Installés et vérifiés : Python 3.15.2, Git 2.56.0.
17. **Dépôt GitHub public** (Pages et Actions gratuits) : github.com/TomuIus/duoq-challenge. Clé Riot stockée dans les secrets GitHub (`RIOT_API_KEY`), jamais dans le code. Les Riot ID des 6 joueurs y figurent (accord à confirmer auprès de chacun).
18. **Appels HTTP :** bibliothèque `requests`, dans un environnement virtuel `.venv` (lancé via `.venv\Scripts\python`, sans activation). Dépendances : `requests`, `tzdata` (fuseaux horaires, absents de Windows).
19. **Abandon anticipé ≠ remake.** Une partie abandonnée tôt (ex. après le départ d'un joueur) est une vraie partie : elle compte dans le total, comme victoire ou défaite, avec ses LP. Un remake ne compte pas dans le total des parties, n'est ni une victoire ni une défaite (mention à part « Remake ») et ne rapporte aucun LP.
20. **Remake et séries :** un remake est ignoré ; il n'interrompt pas une série de victoires.
21. **Détection des remakes :** une partie est un remake si `gameEndedInEarlySurrender` vaut `true` dans les données du joueur. Ne pas se fier à `win` pour un remake (il vaut `false`).
22. **Configuration en TOML** (`config.toml`), lue et vérifiée par `config.py` (module `tomllib`, inclus dans Python).
23. **Données en deux fichiers JSON :** `historique.json` (données brutes, uniquement complété : relevés de rang horodatés quand ils changent, parties) et `classement.json` (résultats calculés à partir de l'historique et de la configuration, lu par la page). Permet de recalculer si une règle change.
24. **Page web en HTML, CSS et JavaScript purs** : un `index.html` qui charge `classement.json`, sans framework ni compilation. Test local via un petit serveur Python (`python -m http.server`, paramètre `?donnees=classement-test.json`).
25. **Contenu de la page :** une seule page qui défile — classement des équipes, une fiche par équipe (joueurs, rangs, détail des points, série, ajustements, alertes « À vérifier », parties repliées par défaut), règles et mention de non-affiliation à Riot. Passage à des onglets envisageable plus tard si la page est trop chargée.
26. **Thème sombre :** suit le réglage du système par défaut ; bouton « Passer en thème clair/sombre » dont le choix est mémorisé (localStorage).
27. **Mise en page PC :** les 3 fiches d'équipe côte à côte (colonnes d'au moins 21rem), repassent l'une sous l'autre sur écran étroit. En-tête, classement et pied de page centrés au-dessus des fiches (~46rem de large) ; bouton de thème en haut à droite (sous le titre sur écran étroit).
28. **Automatisation (option 3) :** `historique.json` n'est enregistré dans le dépôt que s'il a changé ; la page (`index.html` + `classement.json` frais) est publiée directement depuis Actions. L'heure du dernier relevé est écrite dans `etat.json` (non enregistré). `classement.json` et `etat.json` sont dans `.gitignore`. **Premier lancement réussi le 2 novembre 2026.**
29. **Correction manuelle du rang de départ :** section `[[rangs_depart]]` dans `config.toml` (joueur, palier, division, lp), vérifiée par `config.py`. Remplace le rang de départ calculé ; une alerte « rang de départ fixé à la main » s'affiche sur la page. Testée sur données simulées et envoyée sur GitHub (2 novembre 2026).
30. **LP de chaque partie (estimation, option 2 + « ? ») :** l'écart de rang entre deux relevés est attribué aux parties terminées entre-temps (d'après l'heure de fin réelle). Une seule partie → elle reçoit l'écart ; plusieurs → la dernière affiche le total « (sur N parties) » et les autres un « ? » expliqué au survol. Les parties restent « en attente » jusqu'au changement de rang suivant (mise à jour tardive chez Riot). Remakes exclus ; les parties avant le premier rang connu (placement) n'ont pas de LP. Testé sur données simulées, **puis vérifié sur une vraie partie le 2 novembre 2026** (voir résultats des tests).
31. **Fond teinté des parties (option B, 2 novembre 2026) :** chaque partie de la liste a un fond vert (victoire), rouge (défaite) ou gris (remake) à 10-12 % d'opacité (CSS `color-mix`), coins arrondis, sans filet entre les lignes. Classes `res-victoire`, `res-defaite`, `res-remake`. Choisi après comparaison en image avec l'actuel et une bande à gauche (option C).
32. **Licence MIT (2 novembre 2026) :** fichier `LICENSE` à la racine, titulaire « TomuIus » (pseudonyme GitHub, modifiable), année 2026.
33. **Détail des parties par joueur du duo (2 novembre 2026) :** chaque partie apparaît une fois dans la fiche de l'équipe ; en tête : date, résultat, et « Duo ±X LP » quand les LP des deux joueurs sont connus ; puis une ligne par joueur : icône du champion, icône du poste, pseudo, nom du champion, LP. `releve.py` enregistre le poste (`teamPosition`, sinon `individualPosition`) — absent des parties relevées avant ce changement. Icônes de champion : Data Dragon (version récupérée via `api/versions.json`, image `cdn/<version>/img/champion/<NomInterne>.png`) ; si échec, l'icône disparaît et le nom reste. Icônes de poste : Community Dragon, `latest/plugins/rcp-fe-lol-clash/global/default/assets/images/position-selector/positions/icon-position-<poste>.png` ; si échec, abréviation TOP/JGL/MID/ADC/SUP. Nom de champion lisible : espaces avant les majuscules, `MonkeyKing` → Wukong. **Vérifié en local sur vraies parties, en thèmes sombre et clair** : icônes de Viego et Lillia et icône jungle affichées. Non vérifié : icône du support (`utility`).

## Fichiers du projet
- `config.toml` / `config.py` : règlement, équipes (complètes), ajustements manuels (`[[ajustements]]` : équipe, points, motif), rangs de départ fixés à la main (`[[rangs_depart]]`) et vérification.
- `riot_api.py` : accès à l'API Riot (gestion du 429, 404 = introuvable ou pas encore publiée, espaces autour de la clé retirés).
- `releve.py` : relevé → `historique.json` + `etat.json` (options `--depuis` et `--fichier` pour tester). PUUID mis en cache. Récupère au plus 100 parties par joueur et par relevé. Enregistre champion et poste de chaque joueur suivi.
- `classement.py` : `historique.json` + `config.toml` (+ `etat.json`) → `classement.json` (option `--sortie`). Rangs en français, paliers des joueurs, rappel des règles, LP estimés par partie (`lp_par_partie`), champion et poste par joueur (`joueurs`) inclus.
- `index.html` : page d'affichage. Testée dans un navigateur sur données simulées, puis en ligne et en local sur vraies données.
- `.github/workflows/releve.yml` : relevé, calcul, commit de l'historique s'il a changé, publication Pages. Lancement manuel (`workflow_dispatch`) ; lancement automatique toutes les 10 min (minutes 7, 17…) **commenté, à activer juste avant le challenge**. Actions utilisées : checkout@v6, upload-pages-artifact@v4, deploy-pages@v4. Python du runner (3.12 constaté ; ubuntu-latest passe à Ubuntu 26 depuis le 19 octobre 2026).
- `test_api.py` : script d'exploration (options `--nombre`, `--toutes-files`).
- `LICENSE` : licence MIT.
- `.gitignore` : `.venv/`, `historique-test*.json`, `classement-test*.json`, `classement.json`, `etat.json`, `.env`.

## Méthode de calcul (classement.py)
- Échelle continue : Fer IV 0 LP = 0, +100 par division, +400 par palier ; Maître, Grand Maître et Challenger partagent l'échelle à partir de Maître 0 LP (= 2800).
- Rang de départ : rang fixé à la main s'il existe ; sinon dernier rang connu au début du challenge ; s'il n'y en a pas (non classé), premier rang apparu après.
- Partie exclue (51e partie ou commencée après la fin) : rang final = dernier relevé avant la fin de cette partie ; alerte si aucun relevé entre la dernière partie comptée et la partie exclue.
- Vérification du duo : les deux joueurs dans la partie, dans le même camp.
- LP par partie : voir décision 30 (affichage seulement ; le score reste calculé sur rang de départ / rang final).
- Vérifié : passage de division (Or II 96 → Or I 17 = +21, identique au jeu et à dpm.lol).
- Non vérifié : les LP attribués lors d'une rétrogradation (ex. défaite à 0 LP). L'échelle continue reflète le rang réel, ce qui peut différer légèrement des LP « perdus » affichés en jeu.

## Résultats des tests API (1er et 2 novembre 2026)
- Vérifié : Riot ID → PUUID fonctionne (account-v1, région europe), y compris avec un caractère accentué dans le pseudo ou le tag (JesuisVEXée, ÀCAB).
- Vérifié : rang par PUUID (league-v4 entries/by-puuid, plateforme euw1). Entrée Solo/Duo = `queueType: RANKED_SOLO_5x5`, champs `tier`, `rank`, `leaguePoints`, `wins`, `losses` (+ `hotStreak`, `veteran`, `inactive`, `freshBlood`). D'autres files apparaissent (RANKED_FLEX_SR, RANKED_PREMADE_5x5, JADE_RANKED_SOLO_5x5 avec palier WOOD : nature inconnue) → filtrer sur RANKED_SOLO_5x5.
- Vérifié : historique filtré sur la file 420, avec résultat (`win`), champion, horaire, numéro de file (`queueId`) et durée (`gameDuration`, en secondes) de chaque partie.
- Vérifié : filtre `startTime` (en secondes) de la liste des parties (`--depuis 2026-10-26` → 1 partie).
- Vérifié : aucun champ de LP dans les données d'un participant (seul `individualPosition` remontait, faux positif).
- Erreur 429 « server rate limit exceeded » après seulement 5 requêtes : probablement une limite côté serveur Riot (interprétation non vérifiée). Le script attend et réessaie (en-tête Retry-After) → fonctionne.
- Remake vs abandon anticipé, un seul exemple de chaque (à revoir après d'autres tests) :
  - remake (27/10 21 h 29, file 400, 1 min 07 s) : `gameEndedInEarlySurrender: true`, `teamEarlySurrendered: true`, `gameEndedInSurrender: false`, `win: false` ;
  - abandon anticipé (25/10 13 h 37, file 420, 6 min 31 s, victoire) : `gameEndedInSurrender: true`, `gameEndedInEarlySurrender: false` ;
  - parties normales : tous ces champs à `false`.
  - Champs « IGNB » (`gameEndedInIGNBSurrender`, `teamIGNBSurrendered`, `causedGameEndFromIGNBSurrender`) : signification inconnue, toujours `false` jusqu'ici.
- Premier échec Actions : clé du secret collée avec une espace devant (`InvalidHeader`) → secret corrigé + `.strip()` dans `riot_api.py`.
- 6 joueurs, depuis le 20/10 : 10 parties, 28 requêtes.
- 6 joueurs, depuis le 15/08 : 96 parties, 115 requêtes, une attente de 89 s (limite de débit), sans erreur.
- **Détection du duo vérifiée** : les 2 parties jouées ensemble par WifeBuffed et WillOfortune (Équipe 1, deux défaites confirmées) ne sont pas signalées ; toutes les parties jouées seul sont signalées « sans le coéquipier ».
- **LP par partie vérifiés sur une vraie partie (2 novembre 2026)** : relevé avant (Or II 96 LP, 18 requêtes), partie classée gagnée par Tomulus, relevé ~5 min après (Or I 17 LP, 1 nouvelle partie, 13 requêtes) → +21 LP attribués à la partie, identique au jeu et à dpm.lol ; affiché « Tomulus +21 LP » sur la page locale.
- **Icônes vérifiées (2 novembre 2026)** : sur les parties de Tomulus du 1er et du 2 novembre (Lillia, Viego, jungle), icônes de champion (Data Dragon) et de poste (Community Dragon) affichées en thèmes sombre et clair.

## Points techniques à retenir
- Les LP de chaque partie ne sont pas dans les données de partie (vérifié au niveau des participants) : on les déduit de relevés réguliers. Les relevés étant imprécis avec GitHub Actions, le total de LP est calculé à partir du rang de départ et du rang actuel (échelle continue).
- Séries de victoires, nombre de parties, vérification du duo : calculés exactement à partir de l'historique des parties.
- Volume : ~12 requêtes par relevé pour 6 joueurs sans nouvelle partie, +1 par nouvelle partie ; limite Riot 100 / 2 min.
- La saison 2026 devrait se terminer vers le 7 janvier 2027 (date non confirmée par Riot).
- Non vérifié : ce que l'API renvoie pendant les placements (rang dès la 1re partie ?). À tester en janvier.
- Si le premier relevé arrive après la 2e partie de placement, le rang de départ serait faux → corriger avec `[[rangs_depart]]`.
- **Avant le challenge : supprimer `historique.json` du dépôt** (ou le vider). Sinon, un rang relevé en 2026 (avant la remise à zéro de la saison) serait pris comme rang de départ.
- Principe général : le site gère automatiquement le cas normal et signale ce qu'il ne peut pas garantir. Ajustements manuels prévus (rang de départ, score gelé, pénalités).
- Fin à 23 h 59 : le classement définitif peut n'apparaître qu'après le dernier relevé (retard possible jusqu'à ~30 min) → lancement manuel possible (« Run workflow »).
- L'espace de travail de Claude ne peut probablement pas appeler l'API Riot ni les serveurs d'icônes : les tests réels se font sur l'ordinateur de l'utilisateur ou dans GitHub Actions.
- Dépôt public : adresse e-mail « noreply » de GitHub utilisée pour les commits (vérifié).
- Après chaque relevé automatique qui modifie l'historique, faire `git pull` en local avant de modifier le dépôt.
- Serveur local de test (`python -m http.server`) : Ctrl+C l'arrête sans effet sur le site en ligne.
- `color-mix` (fond teinté) : pris en charge par les navigateurs récents ; vérifié seulement dans le navigateur de l'espace de travail de Claude.

## Règlement : complet (version provisoire du 1er novembre 2026)

## Checklist avant le challenge (janvier 2027)
1. ~~Compléter les équipes dans `config.toml`~~ (fait le 2 novembre ; confirmer l'accord de chaque joueur pour le dépôt public).
2. ~~Vérifier que les 6 Riot ID sont trouvés~~ (fait le 2 novembre).
3. Ajuster les dates et heures dans `config.toml` si elles ont changé.
4. Supprimer `historique.json` du dépôt (après la remise à zéro de la saison, avant le début du challenge).
5. Activer le lancement automatique (retirer les « # » devant `schedule` dans `releve.yml`).
6. Pendant le challenge : surveiller l'heure du dernier relevé sur la page.

## Améliorations possibles (non décidées)
- Onglets si la page devient trop chargée.
- Vérifier une défaite avec rétrogradation (défaite à 0 LP) quand l'occasion se présente.
- Vérifier l'icône de poste du support.
