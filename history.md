# history.md â€” Journal des actions

Chaque entrÃ©e : date, action, fichiers concernÃ©s, rÃ©sultat, statut (fait / vÃ©rifiÃ© / non vÃ©rifiÃ©). Plus rÃ©cent en bas.

## 2026-11-07

### Audit initial (lecture seule)
- Exploration de l'environnement, aucune modification.
- ConstatÃ© : installation TSC existante dans `D:\programmes\steam\steamapps\common\Train Simulator 2019` non gÃ©rÃ©e par Steam (pas de `appmanifest_24010.acf`, prÃ©sence de `Cracks\Codex` et `Cracks\SmartSteamEmu`, `steam_emu.ini`). DÃ©cision : ne pas s'en servir.
- Outils dÃ©tectÃ©s : Python 3.10.11 (numpy, requests seulement), Git, Blender (`D:\Programmes\Blender`, version non vÃ©rifiÃ©e), pas de QGIS. Disques : C: ~5 Go libres, D: ~209 Go, E: ~692 Go.
- Statut : fait, vÃ©rifiÃ© (lecture seule).

### Mise en place du projet
- Utilisateur : dossier de travail `E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\` fourni (vide au dÃ©part).
- CrÃ©ation de `CLAUDE.md` (rÃ¨gles, objectif, phases, environnement, mÃ©thode).
- CrÃ©ation de `history.md` (ce fichier).
- Statut : fait. Rien d'autre crÃ©Ã©. Squelette de dossiers, documents de suivi, Git et bibliothÃ¨ques Python : en attente de validation.
- TSC Steam officiel : en cours de tÃ©lÃ©chargement par l'utilisateur ; chemin d'installation Ã  renseigner dans `CLAUDE.md`.

### VÃ©rification de la connexion Blender (lecture seule)
- Outils MCP Blender appelÃ©s : `get_blendfile_summary_path_info`, `get_objects_summary`.
- RÃ©sultat : Blender rÃ©pond. Fichier non enregistrÃ©, scÃ¨ne par dÃ©faut (Camera, Cube, Light), mode Ã©dition sur Cube. Aucune modification faite.
- Non vÃ©rifiÃ© : version de Blender, existence d'un exporteur compatible TSC (.igs).
- Statut : fait, vÃ©rifiÃ© (lecture seule).

### VÃ©rification de l'installation Steam officielle (lecture seule)
- Dossier : `D:\Programmes\Steam\steamapps\common\RailWorks`. `appmanifest_24010.acf` prÃ©sent, StateFlags 4 (installÃ©), buildid 26461748, `version.txt` = v79.0a, 16 Go, pas de dossier `Cracks`, pas de `steam_emu.ini`.
- Outils prÃ©sents : RailWorks64.exe, serz.exe, BlueprintEditor2.exe, Utilities.exe, RWAceTool.exe, ConvertToGEO.exe.
- Routes (10) : dont 00000065 (258 Mo, probablement Marseilleâ€“Avignon) et 00000082 (760 Mo, probablement LGV RhÃ´ne-Alpes & MÃ©diterranÃ©e). Noms non lus dans RouteProperties (non vÃ©rifiÃ©). Fournisseurs d'assets (9) : Aerosoft, Castlerock, DTG, EisenbahnwerkRW, GermanRailRoadsRW, Kuju, RSC, RSDL, SAD.
- Non vÃ©rifiÃ© : liste des DLC possÃ©dÃ©s cÃ´tÃ© compte Steam, contenu exact de chaque route.
- Statut : fait (lecture seule).

### Mise Ã  jour de la documentation
- `CLAUDE.md` : chemin de l'installation Steam renseignÃ©.
- `ROADMAP.md` crÃ©Ã© : mÃ©thode dÃ©taillÃ©e par couche (terrain, eau, voies, Ã©lectrification, ouvrages, PN, textures, gares, signalisation, dÃ©cor, tests, services) et ordre des tronÃ§ons.
- Statut : fait.

### Recherche d'assets franÃ§ais et de l'Ã©lectrification (lecture seule)
- Install Steam : `Assets\DTG` contient `LGVMedSouth`, `LGVRhoneAlpes`, `TGVReseauPack01`, `Class801Pack01`, `Academy`. Contenu des archives `.ap` non lu : prÃ©sence d'une catÃ©naire 1 500 V ou de signaux franÃ§ais non vÃ©rifiÃ©e.
- Recherche web (2 requÃªtes) : aucune source libre confirmÃ©e pour catÃ©naire/signaux franÃ§ais ; l'Ã©lectrification de Chartresâ€“Le Mans n'est confirmÃ©e par aucune source trouvÃ©e.
- RequÃªtes Overpass (OSM) sur `electrified`/`voltage` : Ã©chec (rÃ©ponse non JSON puis timeout). Aucun rÃ©sultat.
- `ROADMAP.md` (couche E) mis Ã  jour : l'utilisateur dit Â« tout en 1 500 V Â», contradiction avec ma connaissance non vÃ©rifiÃ©e, Ã  trancher par les donnÃ©es.
- Statut : partiel, rien de vÃ©rifiÃ©.

### Consultation d'OpenRailwayMap et de Carto Tchoo (navigateur intÃ©grÃ©, lecture seule)
- OpenRailwayMap (openrailwaymap.org) : se charge, styles disponibles (infrastructure, vitesse maximale, signalisation, Ã©lectrification, Ã©cartement). Seulement visuel : captures, pas de donnÃ©es lisibles en texte. Sur la vue testÃ©e (Nogent-le-Rotrou, zoom 16) la couche ferroviaire n'est pas apparue : non concluant.
- Carto Tchoo (carto.tchoo.net, v4.6.2) : page lisible. Sources annoncÃ©es : OpenStreetMap + SNCF Open Data (infrastructure), points kilomÃ©triques `github.com/nicolaswurtz/extras-opendata-sncf-reseau`, pictogrammes de signaux `github.com/nicolaswurtz/signalisation-rfn-svg`. Site personnel, sans garantie de fiabilitÃ© (selon la page). Rien tÃ©lÃ©chargÃ©, dÃ©tail des couches (TIV, panneaux) non inspectÃ©.
- ConsÃ©quence : les donnÃ©es sources sont accessibles directement (OSM, SNCF Open Data, dÃ©pÃ´t GitHub de PK). Ã€ privilÃ©gier plutÃ´t que lire des cartes.
- Statut : fait (lecture seule), partiel.

### HiÃ©rarchie des sources
- DÃ©cision utilisateur : garder les sources les plus sÃ»res. `CLAUDE.md` : section Â« HiÃ©rarchie des sources Â» ajoutÃ©e (officielles > OSM > sites de contrÃ´le visuel).
- Statut : fait.

## 2026-11-07 â€” Phase 0 (dÃ©veloppement lancÃ©)

### 0.1 Squelette du projet
- CrÃ©Ã©s : dossiers (Documentation, GeographicData, Route, Scripts, Assets, Backups, Tests/Phase1-4), `PROJECT_STATUS.md`, `ASSET_INVENTORY.md`, `RAILWAY_DATA.md`, `TECHNICAL_DECISIONS.md`, `ISSUES.md`, `CHANGELOG.md`, `.gitignore`. `git init` fait, aucun commit.
- Statut : fait, vÃ©rifiÃ© (`git status`).

### 0.2 BibliothÃ¨ques Python
- `pip install --user pyproj shapely rasterio lxml` : pyproj 3.7.1, shapely 2.1.2, rasterio 1.4.4, lxml 6.1.3. Imports vÃ©rifiÃ©s.
- Statut : fait, vÃ©rifiÃ©.

### 0.4 Test de conversion serz.exe (sur copie, jeu non modifiÃ©)
- Les routes sont dans `Content\Routes\{GUID}\MainContent.ap`, une archive zip. Copie de celle de la route `00000008` (TestTraK, 5 Mo) dans `Tests/Phase1/serz_test/TestTraK_MainContent.zip`, extraite dans `extracted/`.
- Structure observÃ©e : `MixMap`, `Networks` (`Tracks.bin`, `Track Tiles`, `Road Tiles`, `Loft Tiles`, `Roads.bin`, `Lofts.bin`), `Scenery`, `Terrain`, `RouteInformation`. Tuiles nommÃ©es `Â±XXXXXXÂ±YYYYYY.bin`.
- `serz tile.bin /xml:tile.xml` puis `/bin:tile_rt.bin` puis `/xml:tile_rt.xml` : XML identiques (mÃªme SHA-256). Binaire reconstruit 6415 octets contre 6421 Ã  l'origine (diffÃ©rence d'encodage, contenu identique en XML).
- Le XML des voies expose des courbes (`cCurveStraight`, longueur, position de dÃ©part par tuile). Lisible et modifiable.
- Conclusion : conversion .bin â†” XML fiable. **Non validÃ©** : que le jeu charge une route modifiÃ©e ou gÃ©nÃ©rÃ©e.
- Statut : fait, vÃ©rifiÃ© (format seulement).

### 1.1 DonnÃ©es officielles SNCF (tÃ©lÃ©chargement de donnÃ©es, pas d'assets)
- Serveur Overpass inaccessible (timeouts sur 3 miroirs) ; internet OK ailleurs. Passage Ã  l'open data SNCF (`data.sncf.com`, API Explore v2.1).
- DÃ©couverte : tout l'axe est **une seule ligne officielle, 420000 Â« Paris-Montparnasse Ã  Brest Â»**. PK : Paris-Montparnasse-Pasteur 0+600, Versailles-Chantiers 16+562, Rambouillet 47+810, Chartres 87+137, Nogent-le-Rotrou 148+113, Le Mans 210+980.
- TÃ©lÃ©chargÃ© dans `GeographicData/Raw/sncf/*_420000.json` (script `Scripts/Python/sncf_download_420000.py`) : gares (102), formes des voies (357 tronÃ§ons), formes de ligne (1), Ã©lectrification (4), dÃ©clivitÃ©s (303), vitesses max (48), passages Ã  niveau (117), KVB (6), cantonnement (10), ponts-route (279), traversÃ©es par le public (20), particularitÃ©s des voies (98), circuits de voie (3060), ouvrages en terre (720), rÃ©gime d'exploitation (1), armement des voies (231). Scripts utilitaires : `sncf_find_lines.py`, `sncf_catalog.py`, `sncf_fields.py`, `sncf_summary.py`.
- **Ã‰lectrification (officiel) : 1 500 V continu de PK 0+430 Ã  PK 213+203** (Le Mans dÃ©passÃ©), 25 kV alternatif ensuite. L'utilisateur avait raison, ma supposition (Chartresâ€“Le Mans non Ã©lectrifiÃ©) Ã©tait fausse. Cantonnement : block automatique lumineux (BAL) dÃ¨s PK 0+430 ; KVB sur 0+430â€“323+550.
- Vitesses max (officiel) : 60 km/h au dÃ©part de Paris, 130â€“160 sur la plupart de la ligne, 220 km/h entre PK 190+464 et 208+920, 160 Ã  l'arrivÃ©e au Mans.
- Non vÃ©rifiÃ© : cohÃ©rence entre les jeux (PK/coordonnÃ©es), qualitÃ© des gÃ©omÃ©tries, couverture des signaux et des panneaux (non fournis par ce lot).
- Statut : fait, vÃ©rifiÃ© (comptes). Contenu dÃ©taillÃ© Ã  analyser.

### 1.2 GÃ©omÃ©trie des voies et altimÃ©trie
- Les voies principales `420000-1-V1` et `420000-1-V2` sont chacune une seule polyligne officielle (13 283 et 12 874 sommets) couvrant PK 1+186 â†’ 622+408. VÃ©rification : 48 gares projetÃ©es sur V1, toutes Ã  moins de ~25 m de la voie (la plupart Ã  1-10 m) ; Ã©cart entre chaÃ®nage gÃ©omÃ©trique et PK SNCF â‰¤ 0,12 km sur 210 km (la ligne a une longueur cohÃ©rente avec les PK officiels). VÃ©rifiÃ©.
- Les voies de service, garages et voies de quai (VS, VPL, J00xx, quais de Paris-Montparnasse PK 0,4-1,2) sont des tronÃ§ons sÃ©parÃ©s : 207 tronÃ§ons â‰¤ PK 215.
- Ã‰chantillonnage de V1 et V2 tous les 20 m jusqu'au PK 214,5 (10 666 points) avec altitude IGN RGE ALTI (service `data.geopf.fr/altimetrie`, resource `ign_rge_alti_wld`) : `GeographicData/Processed/420000-1-V1_20m_alti.csv` et `...V2...csv` (script `Scripts/Python/build_centerline_alti.py`). Altitudes 41 Ã  218 m. Fait.
- **ProblÃ¨me identifiÃ©** : l'altitude IGN est celle du sol (MNT), pas de la voie. Pentes brutes aberrantes (max 748 â€°, 1 815 points sur 10 665 au-delÃ  de 15 â€°, pente lissÃ©e sur 400 m jusqu'Ã  86 â€° ponctuellement : ponts, tranchÃ©es, remblais). Le profil en long de la voie ne peut donc pas Ãªtre pris tel quel sur le MNT.
- Le jeu de dÃ©clivitÃ©s SNCF (`caracteristique-des-voies-et-declivite`) ne couvre que ~22 km de V1 sur l'axe (par pas de 200 m, ex. PK 5+200 â†’ rampe 4,1 â€°) : insuffisant seul. Plan : profil de voie = MNT filtrÃ© (mÃ©diane glissante + limite de pente rÃ©aliste) avec les dÃ©clivitÃ©s SNCF comme contrÃ´le/contrainte lÃ  oÃ¹ elles existent.
- Statut : fait pour la gÃ©omÃ©trie (vÃ©rifiÃ©) ; profil en long : Ã  traiter (ISSUES).

### 0.5 SystÃ¨me de coordonnÃ©es et analyse du format de route
- CrÃ©Ã©s : `Scripts/Python/tsc_coords.py` (projection transverse de Mercator locale, tuiles de 1024 m), `Route/Configuration/coordinate_system.json`. Test : V1 projetÃ©e = 213,38 km, 268 tuiles traversÃ©es, aller-retour exact (Ã©cart ~1e-15Â°). VÃ©rifiÃ© (calcul), non validÃ© en jeu.
- CrÃ©Ã© : `Documentation/TSC/route_format.md` (structure de `MainContent.ap`, tuiles de voies en courbes plan, hauteurs par ruban dans `Tracks.bin`, etc.).
- DÃ©cisions ajoutÃ©es Ã  `TECHNICAL_DECISIONS.md`.
- Non fait : gÃ©nÃ©ration de la route de prototype et test dans le jeu.
- Statut : fait (analyse), prototype Ã  faire.
- Correction : `git add -A` avait indexÃ© les copies de fichiers du jeu (Tests/Phase1/serz_test). Dossier ajoutÃ© au `.gitignore` (contenu commercial, Ã  ne jamais versionner ni redistribuer) et index refait ; aucun commit effectuÃ©.

### 1.3 Prototype : conventions du format et ajustement des courbes
- Analyse (sur la copie TestTraK) : `Tracks.bin` = rubans (`Network-cTrackRibbon` : GUID, longueur, hauteurs, propriÃ©tÃ©s dont Ã©lectrification `OverheadWires` + blueprint de catÃ©naire, limite de vitesse, blueprint de voie) + nÅ“uds (`Network-cTrackNode`) qui relient les extrÃ©mitÃ©s de rubans par GUID et position 0/1. Les tuiles `Track Tiles` portent la gÃ©omÃ©trie en plan. `Terrain/*.bin` = `cHeightFieldTile` avec blob de 128Ã—128 flottants 32 bits (1 Ã©chantillon / 8 m). Un GUID `a-b-...` correspond Ã  deux entiers 64 bits = moitiÃ©s little-endian de `uuid.bytes_le`.
- CrÃ©Ã© `Scripts/Python/tsc_tiles.py` (lecture des tuiles de voies). **Conventions validÃ©es sur donnÃ©es rÃ©elles** : tuile 1024 m mesurÃ©e depuis le coin, positions absolues = tuileÃ—1024 + coordonnÃ©e ; `CurveSign = -1` â‡’ angle atan2(Z,X) croissant ; la fin de chaque courbe coÃ¯ncide avec le dÃ©but de la suivante Ã  â‰¤ 1 mm.
- CrÃ©Ã© `Scripts/Python/curvefit.py` : ajustement d'une polyligne en droites/arcs continus. Essais sur V1 (PK 150-152, 140-142, 204-206) : Ã©cart max Ã  la polyligne officielle < 1 m, dÃ©rive en fin de segment < 0,1 m (45 segments pour 2 km dans une zone trÃ¨s courbe).
- IGN WMS-R `ELEVATION.ELEVATIONGRIDCOVERAGE` (BIL 32 bits) testÃ© : fonctionne, adaptÃ© Ã  la gÃ©nÃ©ration de tuiles de terrain.
- Statut : fait, vÃ©rifiÃ© sur le format et le calcul (pas encore dans le jeu).
- Orientation du terrain validÃ©e par les donnÃ©es : comparaison des hauteurs de rubans TestTraK avec le blob de terrain : `blob[ligne = Z/8][colonne = X/8]`, sans inversion ni transposition (Ã©cart moyen 0,37 m ; autres combinaisons 1,3 Ã  2,4 m). Aucun ruban TestTraK ne chevauche deux tuiles (un ruban = une tuile ; nÅ“uds entre rubans). `RouteProperties.xml` a un `Origin` Lat/Long (Ã  rÃ©gler sur 48,2 / 1,1).

### 1.4 Générateur de prototype et première route de test
- Créé Scripts/Python/gen_prototype.py (usage : python gen_prototype.py <pk_debut> <pk_fin> <nom>). Il lit la voie officielle V1, ajuste droites/arcs (écart max 0,52 m), découpe aux limites de tuiles (3 rubans), calcule le profil (MNT IGN WMS-R filtré : médiane 300 m, moyenne 200 m, pente limitée à 15 ‰), applatit un couloir de voie dans le terrain, génère Tracks.xml, tuiles de voies, terrain (16 tuiles), MixMap (copie du modèle), RouteProperties.xml (origine 48,2 / 1,1), puis convertit en .bin avec serz.exe. Vitesse de chaque ruban = vitesse max officielle SNCF au PK médian ; propriétés d'électrification, voie et caténaire copiées du modèle TestTraK (blueprints RSC/TestTraK, provisoire).
- Bug trouvé et corrigé : lxml auto-ferme les chaînes vides (<X d:type="cDeltaString"/>), ce qui tronquait le .bin produit par serz (3 093 octets, sans erreur affichée). Corrigé dans write_xml ; Tracks.bin = 10 830 octets et relu intégralement.
- Relecture des .bin générés (serz ? XML) : 3 rubans, 4 nœuds, 19 courbes, continuité interne OK, longueur totale 2 010 m, écart max à la voie SNCF 0,51 m, hauteurs 102,8 à 105,8 m. Vérifié.
- Route de test générée : Route/Exports/proto1/bc8729b7-ca09-50b7-927b-95fbf7b40a6c (GUID dérivé de proto1, non versionné).
- **Modification du dossier du jeu (ajout uniquement)** : la route de test a été copiée dans D:\Programmes\Steam\steamapps\common\RailWorks\Content\Routes\bc8729b7-ca09-50b7-927b-95fbf7b40a6c (46 fichiers). Aucun fichier d'origine du jeu modifié. Suppression possible en retirant ce dossier.
- Prochaine action : lancer TSC via Steam (appid 24010) et tenter de charger la route dans l'éditeur de route.

### 1.5 Premier essai dans le jeu (route proto1)
- Lancement de TSC via Steam (Computer Use : accès accordé à Steam, steamwebhelper, File Explorer pour la barre des tâches, railworks64.exe). Dialogue Dovetail Live : réponse « Non » (aucun compte créé).
- **Constaté dans le jeu** : la route proto1 apparaît dans le menu Construire avec Latitude 48,2 / Longitude 1,1 (lues de mon RouteProperties.xml) ; « Éditer » ouvre l'éditeur sans plantage et le jeu crée un dossier Scenarios dans la route. Les routes DLC LGV Rhône-Alpes & Méditerranée et Marseille - Avignon sont bien installées.
- Problème : l'éditeur s'ouvre sur la tuile (0,-1), alors que la voie était à ~24 km de l'origine (tuiles -24..-22, +10..+12) : voie non vue. Le jeu a ensuite été arrêté (processus tué) et la route test supprimée du dossier du jeu (ma propre route générée uniquement).
- Ajout de l'option ecentre à gen_prototype.py (test seulement : décale la voie près de la tuile (0,0), route non géoréférencée). Route régénérée et recopiée dans Content\Routes\bc8729b7-….
- Statut : l'ouverture de la route est confirmée ; la voie dans le jeu n'est pas encore vérifiée.
- **Crash du jeu** (16:19) : aprÃ¨s Â« Ã‰diter Â» sur la route `proto1` recentrÃ©e (voie prÃ¨s de la tuile 0,0), `RailWorks64.exe` plante : `APPCRASH`, module `ntdll.dll`, code `0xc0000374` (corruption de tas). Aucun journal du jeu trouvÃ© (ni `Log.txt`, ni `TempDump` rÃ©cent). Le premier essai (voie Ã  24 km de l'origine, donc non chargÃ©e) n'avait pas plantÃ© : le plantage vient donc trÃ¨s probablement d'un fichier gÃ©nÃ©rÃ© chargÃ© au dÃ©marrage de l'Ã©diteur (voies, terrain ou MixMap). Cause non identifiÃ©e.
- Constat : XML â†’ .bin via serz donne toujours un fichier de 6-7 octets plus petit que l'original du jeu (voie 6421 â†’ 6415 octets, terrain 65689 â†’ 65682, MixMap 98534 â†’ 98527). Cause inconnue, peut-Ãªtre bÃ©nigne, jamais testÃ©e en jeu.
- Plan : bissection en jeu (A : voies seules sans terrain ni MixMap ; B : terrain + MixMap sans voies).
- **Bissection A (voies seules, sans Terrain ni MixMap)** : l'éditeur s'ouvre sans planter (RailWorks64 répond). Donc Tracks.bin et les tuiles de voies générés sont acceptés au chargement ; le plantage vient du Terrain et/ou du MixMap. Prochain essai : terrain seul.
- Bissection B (terrain seul, sans MixMap) : le jeu se fige sur l'écran de démarrage (RailWorks64 ne répond plus, CPU figé) ; processus tué. Non reproduit (un seul essai). Prochain essai : MixMap seul.
- **Leçon** : lancer le jeu via le bouton JOUER de Steam. steam.exe -applaunch 24010 a figé le jeu sur l'écran de démarrage deux fois (RailWorks64 ne répond plus) ; la route n'y est pour rien.
- **Bissection C (MixMap seul, sans Terrain)** : l'éditeur s'ouvre sans planter. Avec A (voies seules) OK et C OK, le plantage vient du **Terrain** généré (terrain seul pas encore testé).
- **Cause probable du plantage trouvée** : les .bin du jeu pour Terrain et MixMap commencent par un bloc FF 43 00 <taille LE32> juste après l'en-tête SERZ (taille du blob + 4 : 65 540 pour le terrain, 98 308 pour la MixMap) ; serz ne l'écrit pas, d'où 7 octets de moins, et le jeu semble sous-allouer le blob puis corrompre le tas. Corrigé dans gen_prototype.py (	o_bin(..., hint=)) : les bins générés ont désormais exactement la taille et l'en-tête des originaux (65 689 et 98 534 octets). Hypothèse à confirmer en jeu. Route régénérée, Terrain + MixMap recopiés dans le dossier du jeu (ma route uniquement).

### 1.6 PremiÃ¨re route gÃ©nÃ©rÃ©e chargÃ©e dans le jeu
- Test final (lancement par le bouton JOUER de Steam, route `proto1` avec voies + terrain + MixMap, en-tÃªte de taille ajoutÃ©) : l'Ã©diteur de route s'ouvre **sans plantage** (RailWorks64 rÃ©pond, aucun nouvel Ã©vÃ©nement APPCRASH). Capture d'Ã©cran : le relief IGN est affichÃ©, la voie gÃ©nÃ©rÃ©e apparaÃ®t sur le terrain (barre d'Ã©tat : Â« RÃ©seau : Longueur 105 m, rayon de courbure 10 373 m, inclinaison 1 m 493 Ã  292,7 m, hauteur 103,42 Â»). Confirme en jeu : le tracÃ© est lu, les hauteurs de ruban sont prises en compte, la cause du plantage Ã©tait bien l'en-tÃªte de taille manquant (hypothÃ¨se validÃ©e).
- Non vÃ©rifiÃ© : conduite d'un train sur la voie, raccords entre les 3 rubans, aspect de la catÃ©naire/voie, orientation exacte (X est / Z nord) par rapport Ã  la rÃ©alitÃ©, textures du terrain (MixMap copiÃ©e du modÃ¨le TestTraK, donc incohÃ©rente), longueur totale vue de l'Ã©diteur.
- Le jeu est restÃ© ouvert dans l'Ã©diteur sur `proto1` (aucune modification faite dedans).

### 1.7 GÃ©nÃ©rateur complet (gen_route.py) et route phase 1 (Nogent-le-Rotrou â†” Le Mans)
- Optimisations : un seul script `Scripts/Python/gen_route.py` (remplace `gen_prototype.py` et 11 scripts d'exploration supprimÃ©s) ; deux voies V1+V2 en une passe ; MNT IGN tÃ©lÃ©chargÃ© par tuile en parallÃ¨le avec cache disque (`GeographicData/Elevation/dem_cache_<origine>`) ; terrain et MixMap Ã©crits par patch binaire direct des modÃ¨les du jeu (sans serz, en-tÃªte de taille conservÃ©) ; couloir de voie aplani via arbre KD vectorisÃ©. Origine de projection dÃ©placÃ©e au centre de la ligne (48,45 N ; 1,48 E, Chartres) : plus de dÃ©calage de test. Variable d'environnement `TSC_ORIGIN` rÃ©servÃ©e aux routes de vÃ©rification visuelle.
- `curvefit.fit` : ajout du raffinement par Ã©cart (segment coupÃ© tant qu'il s'Ã©carte de plus de 0,5 m de la polyligne officielle) : Ã©cart max passÃ© de 7,5 m Ã  1,15 m (moyenne 0,13 m).
- Bug corrigÃ© : les propriÃ©tÃ©s des rubans (Ã©lectrification, limite de vitesse, blueprints) ne couvraient que les 405 premiers mÃ¨tres (valeurs du modÃ¨le) et la vitesse restait Ã  50 ; elles couvrent maintenant toute la longueur et la vitesse est la vitesse max officielle SNCF (150, 160 ou 220 km/h).
- Route `phase1` gÃ©nÃ©rÃ©e en 90 s (PK 148 â†’ 211) : 163 rubans (82 V1 + 81 V2), 126 km de voies, 252 tuiles terrain + MixMap, 41 Mo, Ã©lectrifiÃ©e en catÃ©naire (`OverheadWires`) partout. ContrÃ´le hors jeu (`validate_route.py`) : jonctions entre rubans â‰¤ 5 mm, aucune discontinuitÃ© interne, hauteurs de voie 47 Ã  113 m.
- En jeu : `phase1` se charge dans l'Ã©diteur sans plantage (RailWorks64 rÃ©pond, 933 Mo de RAM). Route `view1` (PK 148,5-151,5, origine de test sur Nogent) : l'Ã©diteur ouvre directement la carte 2D (touche 9 = bascule 2D/3D) et affiche bien la voie, courbe comprise, Ã  proximitÃ© de l'origine.
- Navigation dans l'Ã©diteur : la boÃ®te Lat/Long du bandeau supÃ©rieur ne dÃ©place pas la camÃ©ra (ne pas s'en servir) ; la carte 2D (touche 9) fonctionne.
- Non vÃ©rifiÃ© : l'aspect 3D de la double voie, la catÃ©naire visible, la conduite, les textures de sol (MixMap = copie du modÃ¨le). Le jeu est restÃ© ouvert sur `view1`. Routes `phase1` et `view1` prÃ©sentes dans le dossier du jeu (ajouts de ma part uniquement).

### 1.8 Retours utilisateur : voies lissées, hauteurs, caténaire
- Retours de l'utilisateur après essai en jeu : (1) V1 et V2 pas côte à côte et pas à la même hauteur ; (2) micro-virages sur les rails, tracé trop strict ; (3) pas de poteaux de caténaire.
- Données : écart latéral V2?V1 sur PK 148-211 : médiane 3,70 m (entraxe normal), V2 toujours à droite de V1 ; écarts jusqu'à 51 m seulement dans les gares (voies de quai). Hauteurs : chaque voie avait son profil MNT lissé séparément. Correction : V2 reprend la hauteur de V1 quand les voies sont à moins de 6 m, fondu jusqu'à 12 m (gares).
- Lissage : curvefit.fit lisse la polyligne (gaussienne 30 m, extrémités fixes) avant ajustement, tolérance d'écart 1,0 m à l'originale : 884 segments par voie au lieu de 3 036 (2 104 courbes au total au lieu de 5 682), écart max 1,34 m, moyenne 0,26 m, jonctions = 5 mm.
- Caténaire : **elle n'existait pas** (normal : TSC la stocke en rubans de « loft » dans Networks/Loft Tiles, pas dans les voies). Analyse de la route Marseille-Avignon (DLC) : chaque travée = un ruban Network-cLoftRibbon avec une courbe cCurveCatenary, posé sur l'axe de la voie, longueur 18-51 m (médiane 37 m), deux rubans par travée : blueprint RailNetwork\Gantries\Catenary_Wire_01 (type eCatenary, hauteur = voie + 5,8176 m) et Catenary_Wire_02 (eWire, voie + 7,0885 m) ; les poteaux 1 500 V (Cat_Arm_1500_*) sont ajoutés par ces blueprints. _parent_id = identifiant du réseau de loft (Lofts.bin).
- Implémenté dans gen_route.py (modèles extraits par extract_templates.py depuis la copie locale du DLC, non versionnés) : travées de 20 à 45 m (plus courtes en courbe), deux rubans par travée et par voie. Blueprint de voie remplacé par celui du DLC (DTG/LGVMedSouth : RailNetwork\Track\track01_conc.xml, traverses béton) ; caténaire procédurale du modèle TestTraK retirée.
- Phase 1 régénérée (80 s) : 6 210 rubans de caténaire, 82 tuiles de loft, route de 46 Mo. Route de vérification iew1 : l'éditeur la charge sans plantage avec les lofts. Copie de phase1 mise à jour dans le dossier du jeu (ajout de ma part).
- Non vérifié : l'apparition effective des poteaux et fils en 3D (navigation caméra de l'éditeur trop lente pour trouver la voie), l'aspect de la voie DLC, les décalages StartOffsetA/B laissés à zéro, la conduite.

### 1.9 Rails visibles en 2D (touche 9) mais pas dans le monde 3D
- Retour utilisateur : les voies apparaissent sur la carte 2D mais pas dans la vue 3D de phase1. Avant mes derniers changements (blueprint oxfo_padd_track01 du modèle TestTraK, sans Loft Tiles), la voie s'affichait en 3D (captures du 2026-11-07 16:4x).
- Écarts avec la route DLC identifiés : (a) blueprint de voie DLC DTG/LGVMedSouth track01_conc sans TrackRule (le DLC en définit un : LGVMedSouth_Track_Rule) ; (b) présence de Loft Tiles (caténaire seule). Cause non établie.
- Ajout de la TrackRule DLC dans gen_route.py ; variable d'environnement TRACK_BP=testtrak pour la variante de contrôle (blueprint TestTraK, sans règle).
- Routes de vérification copiées dans le jeu (origine sur Nogent, PK 148,5-151,5, caténaire incluse) : iewA = blueprint DLC + TrackRule ; iewB = blueprint TestTraK. Lecture : A et B visibles ? corrigé ; B seul visible ? blueprint DLC en cause ; aucune ? Loft Tiles en cause.

- **Cause trouvée** : iewA (blueprint DLC) invisible en 3D, iewB (blueprint TestTraK) visible. Le RouteProperties.xml contient RBlueprintSetPreLoad (équivalent de l'Object Set Filter) : le modèle TestTraK ne précharge que RSC/TestTraK, donc les blueprints DTG/LGVMedSouth (voie, caténaire) ne sont pas chargés. Correction : gen_route.py ajoute DTG/LGVMedSouth à RBlueprintSetPreLoad (liste PRELOAD). Route de vérification iewC copiée dans le jeu (blueprint DLC + règle + caténaire + préchargement). Résultat en jeu : à confirmer.
- Retour utilisateur sur `viewC` (capture) : la voie est sÃ©lectionnable (contour rouge, gizmo) donc reconnue, mais sans aucune texture, rien de rendu. Le prÃ©chargement du DLC a donc suffi Ã  dÃ©clarer le blueprint, pas Ã  l'afficher.
- Essais de variantes (3 s chacun, origine sur Nogent, PK 148,5-151,5, catÃ©naire DLC incluse) : `TRACK_BP` = `academy` (DTG/Academy `track01_conc`), `hh` (RSC/HamburgHannover `HH_Track_Concrete01`), `kuju` (Kuju/RailSimulator `oxfo_padd_track01`). Routes `view_academy`, `view_hh`, `view_kuju` copiÃ©es dans le jeu. RÃ©sultat en jeu : Ã  confirmer. Rappel : `viewB` (RSC/TestTraK) s'affichait bien.
- Demande utilisateur : tester la voie du DLC Marseille. iewA/iewC l'utilisaient déjà (voie + règle DLC, avec puis sans préchargement) : voie sélectionnable mais sans rendu. Nouvel essai iew_dlc : en plus, RouteProperties.xml repris du modèle de route du DLC (ROUTE_BASE=dlc : ciel, météo, terrain, carte et préchargement DTG/LGVMedSouth). Copié dans le jeu (35bfadb9-0393-5834-989f-33264c577952). Résultat en jeu : à confirmer.
- **Résultat** : iew_dlc affiche bien les rails (confirmé par l'utilisateur). La cause : il faut reprendre le RouteProperties.xml du modèle de route du DLC (blueprint de route, ciel, météo, terrain, carte, préchargement), pas seulement ajouter le produit à la liste de préchargement. ROUTE_BASE=dlc devient le défaut de gen_route.py (voie DLC 	rack01_conc + LGVMedSouth_Track_Rule + caténaire DLC).
- Retour utilisateur sur `view_dlc` : rails visibles, **aucune catÃ©naire ni poteau**. Analyse du loft DLC : les 860 travÃ©es de la tuile (0,0) sont **toutes** reliÃ©es par des nÅ“uds `Network-cLoftNode` (2 par travÃ©e, 1 connexion chacun : GUID du ruban + position 0 ou 1, `RouteVector` = tuile) ; mes tuiles de loft n'avaient aucun nÅ“ud. Les `.bin` de loft du DLC portent aussi l'en-tÃªte de taille `FF 43 00 <LE32>` (non reproduit : valeur inconnue pour des fichiers sans blob).
- Correctif : `gen_route.py` Ã©crit maintenant les deux nÅ“uds de chaque travÃ©e (modÃ¨le `loft_node.xml` extrait du DLC par `extract_templates.py`). Route `view_dlc2` (212 nÅ“uds pour 106 rubans dans la 1re tuile) copiÃ©e dans le jeu. RÃ©sultat en jeu : Ã  confirmer ; si toujours rien, prochaine piste = en-tÃªte de taille des `.bin` de loft.

### 1.10 Caténaire : fils visibles, poteaux et pendules
- Retour utilisateur sur iew_dlc2 : fils porteur et de contact visibles ; **pas de poteaux ni de pendules**. Les nœuds de loft ont donc réglé l'affichage des fils.
- Poteaux : dans le DLC ce sont des entités de Scenery (cDynamicEntity + Network-cGantryComponent), pas des lofts. Modèles 1 500 V extraits : LGV Gantry HPost 1500 Single Pull_L / Push_L (placés sur l'axe de la voie, base à la hauteur de voie, axe X de l'objet à +90° du sens de la voie ; le poteau est décalé dans le modèle). Implémenté : un poteau au début de chaque travée, Pull/Push alternés, orientation +90° pour V1 et -90° pour V2 (poteaux à l'extérieur des deux voies), GUID dérivés de la route. extract_templates.py extrait aussi pole_Pull.xml, pole_Push.xml et le squelette de tuile Scenery.
- Pendules : hypothèse = les décalages StartOffsetB/EndOffsetB du fil de contact (type eCatenary), que j'avais mis à zéro. Relevé DLC : (±0,0077 ; -0,3176 ; ±0,1163), signe alterné d'un poteau à l'autre. Appliqué au fil de contact seulement, porteur à zéro.
- Route iew_poles (139 poteaux sur 3 km, origine Nogent) copiée dans le jeu. Résultat en jeu : à confirmer.
- Retour utilisateur (capture de iew_poles) : fils, pendules et poteaux apparaissent, mais les poteaux sont **sur la voie** (bases au bord des rails). Cause : le modèle Single_L est un poteau d'axe (suspendu), le DLC le place à 0,00 m de la voie. Mesure sur les poteaux latéraux du DLC (LGV Gantry HPost 1500 Med Pull/Push, 2,0 à 3,4 m de la voie) : l'axe +X stocké (RXAxis) pointe vers la voie (produit scalaire 1,00) et les bras sont à -X.
- Correctif : modèles Med Pull/Push, poteau à 2,8 m de l'axe, à l'extérieur des deux voies (V1 à gauche, V2 à droite), RXAxis dirigé vers la voie, regroupement par tuile selon la position finale du poteau. Route iew_poles2 copiée dans le jeu. Résultat en jeu : à confirmer.
- Retour utilisateur : « je ne vois vraiment rien » sur iew_poles2 : à l'ouverture l'éditeur est à l'origine, la voie de test est à 268 m au SO de l'origine (PK 148,5) et s'éloigne ; l'utilisateur ne la trouvait pas. Route iew_here (PK 148,7-150,5, origine placée sur V1 au PK 149,0 : lat 48,32040 / long 0,80533) copiée dans le jeu : la voie, les poteaux et les fils passent directement sous le point d'apparition.
- Retour utilisateur sur iew_here (capture) : « les poteaux sont mal placés » : deux poteaux se retrouvent au niveau des rails, deux autres plus loin à l'extérieur. Mesure sur les fichiers de iew_here : poteaux à 2,80 m de la voie la plus proche, deux voies à 3,8 m d'entraxe, et un poteau près de l'origine à 2,8 m de deux **rubans** voisins (coupure de tuile de la même voie), donc pas de contradiction de géométrie dans les données.
- Changements : gen_route.py place maintenant chaque poteau du côté opposé à la voie voisine (V1/V2 s'inversent dans les gares) ; distance réglable par POLE_D. Routes copiées dans le jeu : iew_here2 (2,8 m) et iew_d7 (7,0 m, **diagnostic** : si les poteaux ne s'éloignent pas des rails, le jeu ignore le décalage et accroche les poteaux à la voie). Résultat en jeu : à confirmer.
- Retour utilisateur sur `view_d7` (capture) : Â« poteaux par blocs de deux et pas du bon cÃ´tÃ© Â». Lecture de la capture : chaque entitÃ© `HPost 1500 Med` affiche **deux montants** (un Ã  la distance demandÃ©e, un sur la voie) : Â« HPost Med Â» est un poteau **mÃ©dian en H** Ã  deux montants, fait pour se placer entre deux voies, pas un poteau latÃ©ral. Les ~2-3 m mesurÃ©s sur le DLC Ã©taient la distance Ã  la voie voisine d'un poteau central. Mon choix du modÃ¨le `Med` Ã©tait donc faux.
- Retour au modÃ¨le `Single Pull_L / Push_L`, placÃ© **sur l'axe de la voie** (comme dans le DLC, oÃ¹ il est Ã  0,00 m), le cÃ´tÃ© Ã©tant portÃ© par l'orientation du modÃ¨le. `gen_route.py` : `POLE_KIND` (`single` dÃ©faut, `med`), `ORI_FLIP` (Â±1, inverse l'orientation), cÃ´tÃ© extÃ©rieur calculÃ© d'aprÃ¨s la voie voisine. Le sens exact du Â« L Â» n'Ã©tant pas connu, deux routes de comparaison copiÃ©es dans le jeu : `view_sideA` (`ORI_FLIP=1`) et `view_sideB` (`ORI_FLIP=-1`), PK 148,7-150,5, origine sur la voie au PK 149. RÃ©sultat en jeu : Ã  confirmer (laquelle met les poteaux Ã  l'extÃ©rieur des deux voies, bras vers les rails, sans bloc de deux).

### 1.11 Poteaux validés, phase 1 régénérée, incident de copie
- Retour utilisateur : **iew_sideB est parfait** (poteaux simples Single Pull_L/Push_L sur l'axe, ORI_FLIP=-1). Devenu le défaut de gen_route.py.
- phase1 régénérée (83 s) : 3 105 poteaux, 6 210 travées de caténaire, 163 rubans de voie (V1+V2), contrôle alidate_route.py identique (jonctions = 5 mm, écart max 1,34 m, vitesses 150/160/220).
- **Incident (mon erreur)** : dans mon script PowerShell, \ (dossier des routes du jeu) écrasait \ (dossier de la route exportée), les variables étant insensibles à la casse. Copy-Item a donc copié le dossier Content\Routes du jeu **dans lui-même** de façon récursive (193 Go, 222 000 fichiers) jusqu'à saturer le disque D: (0,05 Go libres). Vérifié ensuite : les routes d'origine du jeu étaient intactes (Marseille-Avignon 267 Mo/119 fichiers, LGV Rhône-Alpes 763 Mo/26, Hambourg 637 Mo/2). Supprimé uniquement la copie parasite Content\Routes\ee4a17ee-… (chemin littéral \\?\, 124 s) ; D: repasse à 189 Go libres. Corrigé ensuite en copiant avec des noms de variables distincts (\D:\Programmes\Steam\steamapps\common\RailWorks\Content\Routes, \E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\Route\Exports\phase1\ee4a17ee-10e2-540d-a40d-750281467cb5) et un contrôle de taille.
- Retirées du jeu les 14 routes de test obsolètes (iewA/B/C, iew_academy/hh/kuju/dlc/dlc2/poles/poles2/here/here2/d7/sideA). Restent phase1 et iew_sideB (référence visuelle).

### Sauvegarde (demande utilisateur, 20261107-1934)
- Backups/phase1_20261107-1934.zip : route phase1 exportée (51 Mo, voies V1/V2, caténaire, poteaux, terrain, MixMap). Backups/scripts_docs_20261107-1934.zip : scripts, documentation, configuration, documents de suivi.
- Premier commit Git du projet (scripts et documents ; les données brutes, les routes exportées et les copies de fichiers du jeu sont exclues par .gitignore).

### 1.12 Zigzag d'une voie (retour utilisateur en conduite)
- Retour : en se promenant avec un train, une des deux voies fait de petits zigzags, l'autre est correcte.
- Mesure sur phase1 : alternances de sens de courbure V1 = 1 041 sur 1 220 courbes (554 « zigzags » : deux courbes courtes < 60 m de sens opposé), V2 = 580 sur 884 (89). Cause : l'ajustement par ancrage point à point de curvefit.fit force la fin de chaque segment sur la polyligne, ce qui fait osciller la courbure, plus fort sur V1.
- Correctif : curvefit.fit_ls (moindres carrés par blocs de 40 segments, continuité position + cap, pénalité sur les sauts de courbure, pas de transformation en droite) utilisé par gen_route.py. Résultat : 1 478 courbes au lieu de 2 104 ; zigzags V1 10, V2 7 ; écart à la voie officielle max 1,37 m, moyenne 0,118 m (avant 0,258 m) ; rayon minimum 698 m (les 60 m d'avant étaient des artefacts) ; jonctions = 3,5 mm. Poteaux 2 849, travées 5 698.

### 1.13 Recadrage : une phase Ã  la fois, +1 km de chaque cÃ´tÃ© (consigne utilisateur)
- Reproche justifiÃ© : j'avais lancÃ© la gÃ©nÃ©ration de toute la ligne (PK 1,3-211, `ligne_complete`) alors que l'ordre convenu est phase par phase. Export `ligne_complete` (525 Mo, local, jamais copiÃ© dans le jeu) **supprimÃ©**. Aucune autre phase n'est gÃ©nÃ©rÃ©e.
- RÃ¨gle ajoutÃ©e Ã  `CLAUDE.md` et `ROADMAP.md` : pour une phase Aâ†”B, on travaille aussi 1 km au-delÃ  de A et de B. Phase 1 (Nogent-le-Rotrou PK 148,113 â†” Le Mans PK 210,980) = **PK 147,1 â†’ 212,0**.
- `phase1` rÃ©gÃ©nÃ©rÃ©e sur cette plage (37 s ; 3 tuiles de relief tÃ©lÃ©chargÃ©es en plus) : 168 rubans (84 V1 + 84 V2), 129,9 km de voies, 5 876 travÃ©es de catÃ©naire, 2 938 poteaux, 258 tuiles de terrain. ContrÃ´le : jonctions â‰¤ 5 mm, Ã©cart max 1,52 m (moyenne 0,119 m), vitesses 150/160/220. DÃ©ployÃ©e dans le jeu (51 Mo, tailles identiques).

### 2.1 Gares, étape 1 : quais (phase 1)
- Gares voyageurs de la phase 1 (SNCF, PK 147,1-212,0) : Nogent-le-Rotrou 148,113 ; Le Theil-La Rouge 158,974 ; La Ferté-Bernard 169,025 ; Sceaux-Boësse 178,130 ; Connerré-Beillé 186,739 ; Montfort-le-Gesnois 193,888 ; St-Mars-la-Brière 197,212 ; Champagné 199,637 ; Le Mans 210,980 (Yvré-l'Évêque PK 204,100 : non desservie, ignorée). Les données SNCF ne donnent que V1/V2 pour les petites gares (voies annexes seulement à Nogent : 5, et au Mans : 4) : quais extérieurs de chaque côté de la paire V1/V2.
- Quai du DLC : ruban de loft Scenery\Procedural\LGV_Pltfm (DTG/LGVMedSouth), parallèle à la voie à 2,5-3,0 m de l'axe, hauteur ˜ voie - 0,53 m. Le sens des rubans du DLC varie (voie à gauche ou à droite) : le côté du profil par rapport au sens du ruban est inconnu.
- Implémenté dans gen_route.py : quais de 200 m (300 m Nogent, La Ferté, 400 m Le Mans) centrés sur le PK de la gare, côté extérieur de chaque voie (déterminé d'après la voie voisine), décalage PLT_D = 2,7 m, ajustement it_ls, découpe en tuiles, nœuds de loft. Option PLTFM_FLIP=1 inverse le sens du ruban. Modèles pltfm_str.xml/pltfm_arc.xml extraits du DLC.
- Routes de test copiées dans le jeu (origine Nogent-le-Rotrou, PK 147,1-149,3) : iew_quaisA (sens normal) et iew_quaisB (inversé). Résultat en jeu : à confirmer.

### 2.2 Quais : assets franÃ§ais de l'utilisateur (auteur Â« Armand Â»)
- Retour utilisateur sur `view_quaisA/B` : quais enterrÃ©s et peu rÃ©alistes ; l'utilisateur a fourni ses assets dans `Assets/Assets/Armand/` (11 produits : `MurPierre`, `QuaiAIX`, `QuaiArc`, `QuaiBourk`, `QuaiMcd`, `QuaiMetz`, `QuaiMetz2`, `QuaiMorez`, `QuaiPLM`, `QuaiRev`, `QuaisBesanÃ§on`) â€” lofts de quai (`Loft section blueprint1.xml`, `cLoftSectionBlueprint`, `EditorGroundOffset` 1,2). Aucune licence ni lisez-moi fournis : usage comme **dÃ©pendance externe** uniquement, dossier exclu de Git (`Assets/Assets/` dans `.gitignore`), jamais redistribuÃ©.
- InstallÃ© dans le jeu : copie de `Armand` vers `RailWorks\Assets\Armand` (11,3 Mo, ajout seulement).
- Sections en travers lues (serz) : sommet Ã  y=0, corps jusqu'Ã  âˆ’1,2/âˆ’1,3 m ; largeurs : AIX 3 m, Arc 4, Bourk 3, MCD 2,5, Metz 3, Morez 5, PLM 2,5, Rev 4 (centrÃ©es sur l'axe) ; Metz2 (5 m) et BesanÃ§on (BN12 / 125M / 34 / 345M) asymÃ©triques ; l'identifiant de section de BesanÃ§on est mal encodÃ© (`BesanÃƒÂ§on`) : non utilisÃ© pour l'instant.
- `gen_route.py` : quais = ruban de loft Armand le long de chaque voie, cÃ´tÃ© extÃ©rieur, axe Ã  (1,67 m + largeur/2) de la voie (bord Ã  1,67 m), sommet Ã  +0,55 m au-dessus de la hauteur de voie ; produit par `PLT_PROD` (dÃ©faut `QuaiMetz`) ; les produits Armand utilisÃ©s sont ajoutÃ©s au prÃ©chargement (`RBlueprintSetPreLoad`) mÃªme avec la base DLC. Banc d'essai `PLT_TEST=1` : tous les produits symÃ©triques l'un aprÃ¨s l'autre (50 m + 12 m d'intervalle) le long de V1 depuis l'origine.
- Route `view_quais_test` copiÃ©e dans le jeu (origine Nogent-le-Rotrou) ; routes `view_quaisA/B` retirÃ©es. Ordre le long de la voie vers Le Mans : AIX, Arc, Bourk, Mcd, Metz, Morez, PLM, Rev. RÃ©sultat en jeu : Ã  confirmer (rendu, hauteur, cÃ´tÃ©).
- Choix utilisateur sur le banc d'essai `view_quais_test` : **Rev** (4 m) pour Nogent-le-Rotrou et Le Mans, **PLM** (2,5 m) pour les autres gares. `gen_route.py` : `PLT_PROD` dÃ©faut `QuaiPLM`, `STATION_PROD` = {Nogent-le-Rotrou, Le Mans â†’ `QuaiRev`}.
- `phase1` rÃ©gÃ©nÃ©rÃ©e (PK 147,1-212,0) : 23 rubans de quai (9 gares Ã— 2 voies, dÃ©coupÃ©s aux limites de tuile), 5 899 travÃ©es de catÃ©naire, 2 938 poteaux ; prÃ©chargement `LGVMedSouth`, `QuaiPLM`, `QuaiRev` ; contrÃ´le voies inchangÃ© (jonctions â‰¤ 5 mm, Ã©cart max 1,52 m). DÃ©ployÃ©e dans le jeu (51 Mo) ; route de test `view_quais_test` retirÃ©e. Rendu des quais en jeu : Ã  confirmer (utilisateur a dÃ©jÃ  vu le banc d'essai, hauteur et cÃ´tÃ© non signalÃ©s comme faux).

### 2.3 Gares : Â« tout via Blender Â» (consigne utilisateur) â€” recherche de la chaÃ®ne et premiÃ¨re rÃ©fÃ©rence
- Consigne : gÃ©nÃ©rer les Ã©lÃ©ments de gare via Blender, d'aprÃ¨s des photos rÃ©elles (Google/Commons), puis les modÃ©liser.
- Blender 5.2.3 LTS connectÃ© ; add-on **BRIAGE 4.1** (`bl_ext.user_default.briage`, licence MIT) dÃ©jÃ  installÃ© : export `.igs`/`.ia` opÃ©rationnel. Test : cube texturÃ© exportÃ© en `.igs` dans `Assets/Custom/Proto/` (une collection `TSC_Proto` ajoutÃ©e Ã  la scÃ¨ne Blender par dÃ©faut non enregistrÃ©e ; scÃ¨ne d'origine non supprimÃ©e).
- `ConvertToGEO.exe` du jeu (testÃ©, shaders copiÃ©s depuis `dev\Shaders` dans un dossier temporaire) ne produit que du `.GeoPs2` : la compilation PC (`.GeoPcDx`/`.TgPcDx`) passe par le Blueprint Editor. Voir `Documentation/TSC/asset_pipeline.md`.
- **RÃ©fÃ©rence rÃ©elle, Nogent-le-Rotrou** (WikipÃ©dia : Gare de Nogent-le-Rotrou ; Commons : photo Â« Gare de nogent le rotrou - panoramio.jpg Â», CC) : gare ouverte en mai 1857 ; PK 148,113 ; alt. 109 m ; **3 voies + 1 voie en impasse + voies de service ; 2 quais : 1 central + 1 latÃ©ral, changement de quai par souterrain** (rehaussement et 2 ascenseurs, travaux 2020). BÃ¢timent voyageurs : corps central Ã  pavillon, toit d'ardoise en croupe, deux souches de cheminÃ©e en brique, murs en moellons (silex/calcaire) avec chaÃ®nes d'angle en pierre blanche, encadrements d'ouvertures cintrÃ©es en brique rouge, aile basse avec **marquise en fer** sur poteaux cÃ´tÃ© quai, panneau Â« NOGENT-LE-ROTROU Â» sur la faÃ§ade, mobilier (bancs bleus, Ã©clairage).
- **ConsÃ©quence** : ma pose de quais Â« un par voie Ã  l'extÃ©rieur Â» est fausse pour Nogent (quai central + quai latÃ©ral + souterrain) ; Ã  corriger avec la vraie configuration de chaque gare.
- **Blueprint Editor pilotÃ© (Computer Use, accord utilisateur)** : v72.4a ; Â« Invalid source path! Â» car `RailWorks\Source` n'existe pas sur l'install Steam â†’ crÃ©ation de `RailWorks\Source\PCLM\Gares\Scenery\Buildings\` (mes dossiers uniquement, ajout) avec `TestBuilding.igs` + `Textures\TestTex.png`. Clic droit sur le `.igs` â†’ Â« Create scenery blueprint Â», enregistrÃ©, Export With References : 1re tentative en Ã©chec (Â« Failed to find ...TestTex.ace Â») car il faut des textures **ACE** ; conversion PNGâ†’ACE avec **RWAceTool** (interface graphique, 476 o) ; **2e export rÃ©ussi** : `Assets\PCLM\Gares\Scenery\Buildings\TestBuilding.{xml,bin,GeoPcDx}` + `Textures\TestTex.TgPcDx`. La sortie du Blueprint Editor rÃ©vÃ¨le les commandes `ConvertToTg` / `ConvertToGeo` / `serz` (voir `Documentation/TSC/asset_pipeline.md`). `ConvertToGeo -pc` utilisable en ligne de commande ; seule la conversion PNGâ†’ACE reste graphique.
- `gen_route.py` : pose d'objets de dÃ©cor depuis `Route/Configuration/objects.json` (modÃ¨le `obj_template.xml` extrait du DLC par `extract_templates.py`). Route de vÃ©rification `view_gare` (origine sur la gare de Nogent, PK 147,5-149,5) copiÃ©e dans le jeu : une boÃ®te Â« TestBuilding Â» (10Ã—6Ã—4 m, texture Ã  damier rouge/beige 64 px) Ã  14 m Ã  gauche de V1 au PK 148,113. RÃ©sultat en jeu : Ã  confirmer.

### 2.4 BÃ¢timent voyageurs de Nogent-le-Rotrou (modÃ©lisÃ© par script Blender)
- Retour utilisateur : la boÃ®te de test `view_gare` s'affiche (rouge/rose saumon) : **chaÃ®ne Blender â†’ jeu validÃ©e en conditions rÃ©elles** (IGS, ACE, blueprint, pose par `objects.json`).
- `Scripts/Blender/gare_nogent.py` : gÃ©nÃ¨re 12 textures procÃ©durales (moellon, pierre blanche, brique, ardoise, crÃ©pi, vitrage, fer, porte, zinc, bÃ©ton, panneau, noir), le maillage (159 faces, 12 matÃ©riaux `IgsMat` `TexDiff`) et l'exporte en `GareNogent.igs`. ModÃ¨le : pavillon central 11Ã—9 m (moellons, chaÃ®nes d'angle en pierre blanche, toit d'ardoise en croupe, 2 souches de cheminÃ©e en brique, lucarnes), aile gauche 14Ã—7 m (crÃ©pi, 4 baies cintrÃ©es + porte), aile droite 9,5Ã—7,5 m (moellons, 2 grandes baies cintrÃ©es Ã  encadrement de brique), panneau de nom sur la faÃ§ade, marquise en fer de 25 m sur poteaux (toit en zinc), 2 bancs. Dimensions **estimÃ©es d'aprÃ¨s la photo** (non mesurÃ©es). RepÃ¨re : X le long de la voie, faÃ§ade cÃ´tÃ© quai Ã  Y=0.
- Blender s'Ã©tait fermÃ© (connexion MCP perdue) : script exÃ©cutÃ© dans une session Blender graphique Ã©phÃ©mÃ¨re (`blender.exe --python`, minuteur + `wm.quit_blender()`), car l'export BRIAGE Ã©choue en mode `-b` (`wm.redraw_timer`).
- Textures PNG â†’ ACE par lot avec RWAceTool (Â« Multiple image conversion Â», 12 fichiers). Blueprint Editor : Â« Create scenery blueprint Â» sur `GareNogent.igs`, `Ctrl+S`, F7 : **Export Succeeded** â†’ `Assets\PCLM\Gares\Scenery\Buildings\GareNogent.{xml,bin,GeoPcDx}` + textures `.TgPcDx`. Sources versionnÃ©es dans `Assets/Custom/PCLM_Gares_Source/` (crÃ©Ã©es par nous).
- Routes de vÃ©rification : `view_gare0` et `view_gare180` (origine sur la gare de Nogent, PK 147,5-149,5) : bÃ¢timent Ã  10 m Ã  gauche de V1 au PK 148,113, cap relatif 0Â° / 180Â° pour trouver l'orientation de la faÃ§ade. `Route/Configuration/objects.json` : version cap 0Â°. `OBJECTS_FILE` permet d'indiquer un autre fichier d'objets. RÃ©sultat en jeu : Ã  confirmer.

### 2.5 Nogent-le-Rotrou : BV remodelÃ© d'aprÃ¨s photos (2026-11-07)
- Emprises IGN BD TOPO projetÃ©es dans le repÃ¨re de V1 (origine = point de V1 le plus proche de la gare SNCF, gauche > 0) : BV 1 niveau en 3 volumes, L -70â€¦-6 m, latÃ©ral -52â€¦-31 m (hauteurs 5,1-6,5 m) ; grand bÃ¢timent L +20â€¦34, latÃ©ral -73â€¦-40 (7,9 m). Source : `GeographicData/Raw/bdtopo_nogent_batiment.json`. Dimensions fines des ailes **Ã  vÃ©rifier** (modÃ¨le approximatif).
- `Scripts/Blender/gare_nogent.py` rÃ©Ã©crit d'aprÃ¨s les 6 photos : pavillon central 2 niveaux crÃ©pi crÃ¨me (toit ardoise en croupe, fronton Ã  horloge, 3 portes cintrÃ©es, fenÃªtres cintrÃ©es Ã  volets saumon, moulures rouges, cheminÃ©es briques), ailes en moellons 1 niveau avec bandeau rouge, bÃ¢timent 2 niveaux en brique Ã  une extrÃ©mitÃ©, marquise mÃ©tallique cÃ´tÃ© quai. Nouvelle texture `Volet`. GÃ©nÃ©rÃ©, exportÃ© IGS (232 faces), PNGâ†’ACE (RWAceTool, 13 textures), compilÃ© par Blueprint Editor (F7, GeoPcDx 46 Ko). **Pas encore vu en jeu.**
- `Route/Configuration/objects.json` : pk 148,089, latÃ©ral -34,5 (cÃ´tÃ© droit de V1, faÃ§ade vers les voies), cap 180Â° (X modÃ¨le vers Paris). Route de test `view_gare180` rÃ©gÃ©nÃ©rÃ©e (origine gare) et recopiÃ©e dans `Content\Routes\8c69da3d-â€¦` (route de test Ã  moi, pas un fichier d'origine). Orientation et position Ã  valider en jeu.
