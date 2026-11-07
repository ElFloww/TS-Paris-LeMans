# CLAUDE.md — Ligne Paris-Montparnasse ↔ Chartres ↔ Nogent-le-Rotrou ↔ Le Mans (Train Simulator Classic)

Ce fichier est lu au début de chaque session. Il prime sur les habitudes par défaut.

## Objectif
Reproduire à l'identique, dans Train Simulator Classic (TSC, version Steam officielle), une seule route continue :
Paris-Montparnasse – Versailles-Chantiers – Chartres – Nogent-le-Rotrou – Le Mans.
Fidélité visée : tracé, courbes, pentes/rampes, ponts, tunnels, passages à niveau, gares, quais, signalisation, électrification, relief, décor.
La fidélité géographique et ferroviaire prime sur la vitesse. Ne jamais construire « à l'œil ».

## Règles absolues
1. **Journal obligatoire** : chaque action qui crée, modifie ou supprime un fichier, installe un logiciel, télécharge quelque chose ou lance le jeu est consignée dans `history.md` (date, action, fichiers concernés, résultat, vérifié ou non). Écrire l'entrée dans la même session, juste après l'action.
2. **Rien de destructif sans accord** : pas de suppression, d'écrasement ou de modification des fichiers d'origine du jeu ni des assets commerciaux. Toujours travailler sur des copies ou dans `Route/`. Sauvegarde dans `Backups/` avant toute modification d'une route existante.
3. **Honnêteté** : ne jamais affirmer qu'une action est faite ou vérifiée si elle ne l'a pas été. Distinguer « généré », « converti », « chargé dans le jeu », « testé en conduite ».
4. **Installation du jeu** : seule l'installation Steam officielle de l'utilisateur sert de base. La copie existante dans `D:\programmes\steam\steamapps\common\Train Simulator 2019` (cracks Codex/SmartSteamEmu) ne doit être ni utilisée, ni modifiée, ni lue pour en extraire des fichiers.
5. **Assets** : les assets commerciaux restent des dépendances externes (Object Set Filter). Aucune copie ni redistribution. Les assets communautaires ne sont téléchargés que si l'auteur autorise l'usage ; demander confirmation à l'utilisateur avant chaque téléchargement (nom, source, taille) et noter la licence dans `ASSET_INVENTORY.md`.
6. **Sources de données** : IGN (RGE ALTI, BD TOPO, Géoportail), OpenStreetMap, SNCF Réseau open data, photos aériennes et au sol. Citer la source de chaque jeu de données dans `RAILWAY_DATA.md`. Ne jamais inventer une valeur : écrire « inconnu » ou « à vérifier ».
7. **Ne pas passer à la phase suivante** tant que la phase en cours a un problème majeur de géométrie, de raccordement ou de stabilité.

## Ordre de construction (phases d'une seule route)
1. Nogent-le-Rotrou ↔ Le Mans
2. Nogent-le-Rotrou ↔ Chartres
3. Chartres ↔ Versailles-Chantiers
4. Versailles-Chantiers ↔ Paris-Montparnasse

Une seule route finale : système de coordonnées, origine, limites de route et raccords sont fixés dès le départ (voir `TECHNICAL_DECISIONS.md`) et ne changent plus sans décision explicite.

## Hiérarchie des sources (décision utilisateur du 2026-11-07 : garder les plus sûres)
1. **Officielles** : SNCF Réseau / SNCF Open Data (lignes, PK, vitesses, gares), IGN (RGE ALTI, BD TOPO, Géoportail, photos aériennes).
2. **Collaboratives** : OpenStreetMap, à recouper avec le niveau 1 dès que les deux existent.
3. **Contrôle visuel seulement** : OpenRailwayMap, Carto Tchoo, photos et vidéos. Jamais une source de données unique ; en cas de désaccord, le niveau 1 gagne et l'écart est noté dans `ISSUES.md`.
Chaque valeur retenue indique sa source dans `RAILWAY_DATA.md`.

## Distinctions à respecter dans les données
Gares desservies / gares et haltes fermées / installations techniques et voies de service / embranchements et raccordements. Une liste d'arrêts TER n'est pas un inventaire exhaustif.

## Environnement
- Dossier de travail : `E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\`
- Windows 11, PowerShell. Python 3.10.11 (bibliothèques géographiques à installer : pyproj, shapely, rasterio, lxml). Git installé. Blender dans `D:\Programmes\Blender` (version à vérifier). QGIS absent.
- TSC Steam officiel (v79.0a, StateFlags 4 = installé, sans cracks) : `D:\Programmes\Steam\steamapps\common\RailWorks` (appid 24010). C'est la seule installation de référence.
- Outils TSC attendus dans le dossier du jeu : `serz.exe`, `BlueprintEditor2.exe`, `RWAceTool.exe`, `ConvertToGEO.exe`, `ConvertToTG.exe`, `luac.exe`, `Utilities.exe`.
- Disque C: presque plein (≈5 Go libres) : rien de volumineux dessus.

## Méthode technique (hypothèse à valider par prototype)
Édition de la route par code : fichiers `.bin` ↔ XML via `serz.exe`, générés/modifiés par Python à partir des données OSM/IGN (voies `Networks\Tracks.bin`, tuiles `Scenery`, relief `Terrain`). Non validé tant qu'un prototype de ~2 km n'a pas été chargé dans le jeu : ne pas présenter comme acquis. L'éditeur du jeu et Computer Use ne servent qu'en repli ou pour contrôler visuellement.

## Structure du dossier
```
CLAUDE.md  history.md
PROJECT_STATUS.md  ROADMAP.md  ASSET_INVENTORY.md  RAILWAY_DATA.md
TECHNICAL_DECISIONS.md  ISSUES.md  CHANGELOG.md
GeographicData/ (Raw, Processed, Elevation, QGIS)
Route/ (Configuration, Exports)
Scripts/ (Python, XML, PowerShell)
Assets/ (Inventory, Custom)
Documentation/ (Architecture, TSC, Railway, Reports)
Backups/   Tests/ (Phase1..Phase4)
```
Les données brutes lourdes et les fichiers de route générés ne sont pas versionnés dans Git (voir `.gitignore`) ; scripts et documents textuels le sont.

## Conventions
- Réponses à l'utilisateur en français, courtes, avec ce qui est fait, vérifié, et ce qui reste.
- Coordonnées sources en WGS84 / Lambert-93 (EPSG:2154) ; coordonnées TSC dérivées d'une origine unique, formule documentée.
- Scripts reproductibles et idempotents ; chaque script écrit dans `history.md` ou renvoie un résumé à y consigner.
- Mettre à jour les documents de suivi après chaque session. Ne jamais perdre d'information validée.
