# history.md — Journal des actions

Chaque entrée : date, action, fichiers concernés, résultat, statut (fait / vérifié / non vérifié). Plus récent en bas.

## 2026-11-07

### Audit initial (lecture seule)
- Exploration de l'environnement, aucune modification.
- Constaté : installation TSC existante dans `D:\programmes\steam\steamapps\common\Train Simulator 2019` non gérée par Steam (pas de `appmanifest_24010.acf`, présence de `Cracks\Codex` et `Cracks\SmartSteamEmu`, `steam_emu.ini`). Décision : ne pas s'en servir.
- Outils détectés : Python 3.10.11 (numpy, requests seulement), Git, Blender (`D:\Programmes\Blender`, version non vérifiée), pas de QGIS. Disques : C: ~5 Go libres, D: ~209 Go, E: ~692 Go.
- Statut : fait, vérifié (lecture seule).

### Mise en place du projet
- Utilisateur : dossier de travail `E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\` fourni (vide au départ).
- Création de `CLAUDE.md` (règles, objectif, phases, environnement, méthode).
- Création de `history.md` (ce fichier).
- Statut : fait. Rien d'autre créé. Squelette de dossiers, documents de suivi, Git et bibliothèques Python : en attente de validation.
- TSC Steam officiel : en cours de téléchargement par l'utilisateur ; chemin d'installation à renseigner dans `CLAUDE.md`.

### Vérification de la connexion Blender (lecture seule)
- Outils MCP Blender appelés : `get_blendfile_summary_path_info`, `get_objects_summary`.
- Résultat : Blender répond. Fichier non enregistré, scène par défaut (Camera, Cube, Light), mode édition sur Cube. Aucune modification faite.
- Non vérifié : version de Blender, existence d'un exporteur compatible TSC (.igs).
- Statut : fait, vérifié (lecture seule).

### Vérification de l'installation Steam officielle (lecture seule)
- Dossier : `D:\Programmes\Steam\steamapps\common\RailWorks`. `appmanifest_24010.acf` présent, StateFlags 4 (installé), buildid 26461748, `version.txt` = v79.0a, 16 Go, pas de dossier `Cracks`, pas de `steam_emu.ini`.
- Outils présents : RailWorks64.exe, serz.exe, BlueprintEditor2.exe, Utilities.exe, RWAceTool.exe, ConvertToGEO.exe.
- Routes (10) : dont 00000065 (258 Mo, probablement Marseille–Avignon) et 00000082 (760 Mo, probablement LGV Rhône-Alpes & Méditerranée). Noms non lus dans RouteProperties (non vérifié). Fournisseurs d'assets (9) : Aerosoft, Castlerock, DTG, EisenbahnwerkRW, GermanRailRoadsRW, Kuju, RSC, RSDL, SAD.
- Non vérifié : liste des DLC possédés côté compte Steam, contenu exact de chaque route.
- Statut : fait (lecture seule).

### Mise à jour de la documentation
- `CLAUDE.md` : chemin de l'installation Steam renseigné.
- `ROADMAP.md` créé : méthode détaillée par couche (terrain, eau, voies, électrification, ouvrages, PN, textures, gares, signalisation, décor, tests, services) et ordre des tronçons.
- Statut : fait.

### Recherche d'assets français et de l'électrification (lecture seule)
- Install Steam : `Assets\DTG` contient `LGVMedSouth`, `LGVRhoneAlpes`, `TGVReseauPack01`, `Class801Pack01`, `Academy`. Contenu des archives `.ap` non lu : présence d'une caténaire 1 500 V ou de signaux français non vérifiée.
- Recherche web (2 requêtes) : aucune source libre confirmée pour caténaire/signaux français ; l'électrification de Chartres–Le Mans n'est confirmée par aucune source trouvée.
- Requêtes Overpass (OSM) sur `electrified`/`voltage` : échec (réponse non JSON puis timeout). Aucun résultat.
- `ROADMAP.md` (couche E) mis à jour : l'utilisateur dit « tout en 1 500 V », contradiction avec ma connaissance non vérifiée, à trancher par les données.
- Statut : partiel, rien de vérifié.

### Consultation d'OpenRailwayMap et de Carto Tchoo (navigateur intégré, lecture seule)
- OpenRailwayMap (openrailwaymap.org) : se charge, styles disponibles (infrastructure, vitesse maximale, signalisation, électrification, écartement). Seulement visuel : captures, pas de données lisibles en texte. Sur la vue testée (Nogent-le-Rotrou, zoom 16) la couche ferroviaire n'est pas apparue : non concluant.
- Carto Tchoo (carto.tchoo.net, v4.6.2) : page lisible. Sources annoncées : OpenStreetMap + SNCF Open Data (infrastructure), points kilométriques `github.com/nicolaswurtz/extras-opendata-sncf-reseau`, pictogrammes de signaux `github.com/nicolaswurtz/signalisation-rfn-svg`. Site personnel, sans garantie de fiabilité (selon la page). Rien téléchargé, détail des couches (TIV, panneaux) non inspecté.
- Conséquence : les données sources sont accessibles directement (OSM, SNCF Open Data, dépôt GitHub de PK). À privilégier plutôt que lire des cartes.
- Statut : fait (lecture seule), partiel.

### Hiérarchie des sources
- Décision utilisateur : garder les sources les plus sûres. `CLAUDE.md` : section « Hiérarchie des sources » ajoutée (officielles > OSM > sites de contrôle visuel).
- Statut : fait.

## 2026-11-07 — Phase 0 (développement lancé)

### 0.1 Squelette du projet
- Créés : dossiers (Documentation, GeographicData, Route, Scripts, Assets, Backups, Tests/Phase1-4), `PROJECT_STATUS.md`, `ASSET_INVENTORY.md`, `RAILWAY_DATA.md`, `TECHNICAL_DECISIONS.md`, `ISSUES.md`, `CHANGELOG.md`, `.gitignore`. `git init` fait, aucun commit.
- Statut : fait, vérifié (`git status`).

### 0.2 Bibliothèques Python
- `pip install --user pyproj shapely rasterio lxml` : pyproj 3.7.1, shapely 2.1.2, rasterio 1.4.4, lxml 6.1.3. Imports vérifiés.
- Statut : fait, vérifié.

### 0.4 Test de conversion serz.exe (sur copie, jeu non modifié)
- Les routes sont dans `Content\Routes\{GUID}\MainContent.ap`, une archive zip. Copie de celle de la route `00000008` (TestTraK, 5 Mo) dans `Tests/Phase1/serz_test/TestTraK_MainContent.zip`, extraite dans `extracted/`.
- Structure observée : `MixMap`, `Networks` (`Tracks.bin`, `Track Tiles`, `Road Tiles`, `Loft Tiles`, `Roads.bin`, `Lofts.bin`), `Scenery`, `Terrain`, `RouteInformation`. Tuiles nommées `±XXXXXX±YYYYYY.bin`.
- `serz tile.bin /xml:tile.xml` puis `/bin:tile_rt.bin` puis `/xml:tile_rt.xml` : XML identiques (même SHA-256). Binaire reconstruit 6415 octets contre 6421 à l'origine (différence d'encodage, contenu identique en XML).
- Le XML des voies expose des courbes (`cCurveStraight`, longueur, position de départ par tuile). Lisible et modifiable.
- Conclusion : conversion .bin ↔ XML fiable. **Non validé** : que le jeu charge une route modifiée ou générée.
- Statut : fait, vérifié (format seulement).

### 1.1 Données officielles SNCF (téléchargement de données, pas d'assets)
- Serveur Overpass inaccessible (timeouts sur 3 miroirs) ; internet OK ailleurs. Passage à l'open data SNCF (`data.sncf.com`, API Explore v2.1).
- Découverte : tout l'axe est **une seule ligne officielle, 420000 « Paris-Montparnasse à Brest »**. PK : Paris-Montparnasse-Pasteur 0+600, Versailles-Chantiers 16+562, Rambouillet 47+810, Chartres 87+137, Nogent-le-Rotrou 148+113, Le Mans 210+980.
- Téléchargé dans `GeographicData/Raw/sncf/*_420000.json` (script `Scripts/Python/sncf_download_420000.py`) : gares (102), formes des voies (357 tronçons), formes de ligne (1), électrification (4), déclivités (303), vitesses max (48), passages à niveau (117), KVB (6), cantonnement (10), ponts-route (279), traversées par le public (20), particularités des voies (98), circuits de voie (3060), ouvrages en terre (720), régime d'exploitation (1), armement des voies (231). Scripts utilitaires : `sncf_find_lines.py`, `sncf_catalog.py`, `sncf_fields.py`, `sncf_summary.py`.
- **Électrification (officiel) : 1 500 V continu de PK 0+430 à PK 213+203** (Le Mans dépassé), 25 kV alternatif ensuite. L'utilisateur avait raison, ma supposition (Chartres–Le Mans non électrifié) était fausse. Cantonnement : block automatique lumineux (BAL) dès PK 0+430 ; KVB sur 0+430–323+550.
- Vitesses max (officiel) : 60 km/h au départ de Paris, 130–160 sur la plupart de la ligne, 220 km/h entre PK 190+464 et 208+920, 160 à l'arrivée au Mans.
- Non vérifié : cohérence entre les jeux (PK/coordonnées), qualité des géométries, couverture des signaux et des panneaux (non fournis par ce lot).
- Statut : fait, vérifié (comptes). Contenu détaillé à analyser.

### 1.2 Géométrie des voies et altimétrie
- Les voies principales `420000-1-V1` et `420000-1-V2` sont chacune une seule polyligne officielle (13 283 et 12 874 sommets) couvrant PK 1+186 → 622+408. Vérification : 48 gares projetées sur V1, toutes à moins de ~25 m de la voie (la plupart à 1-10 m) ; écart entre chaînage géométrique et PK SNCF ≤ 0,12 km sur 210 km (la ligne a une longueur cohérente avec les PK officiels). Vérifié.
- Les voies de service, garages et voies de quai (VS, VPL, J00xx, quais de Paris-Montparnasse PK 0,4-1,2) sont des tronçons séparés : 207 tronçons ≤ PK 215.
- Échantillonnage de V1 et V2 tous les 20 m jusqu'au PK 214,5 (10 666 points) avec altitude IGN RGE ALTI (service `data.geopf.fr/altimetrie`, resource `ign_rge_alti_wld`) : `GeographicData/Processed/420000-1-V1_20m_alti.csv` et `...V2...csv` (script `Scripts/Python/build_centerline_alti.py`). Altitudes 41 à 218 m. Fait.
- **Problème identifié** : l'altitude IGN est celle du sol (MNT), pas de la voie. Pentes brutes aberrantes (max 748 ‰, 1 815 points sur 10 665 au-delà de 15 ‰, pente lissée sur 400 m jusqu'à 86 ‰ ponctuellement : ponts, tranchées, remblais). Le profil en long de la voie ne peut donc pas être pris tel quel sur le MNT.
- Le jeu de déclivités SNCF (`caracteristique-des-voies-et-declivite`) ne couvre que ~22 km de V1 sur l'axe (par pas de 200 m, ex. PK 5+200 → rampe 4,1 ‰) : insuffisant seul. Plan : profil de voie = MNT filtré (médiane glissante + limite de pente réaliste) avec les déclivités SNCF comme contrôle/contrainte là où elles existent.
- Statut : fait pour la géométrie (vérifié) ; profil en long : à traiter (ISSUES).

### 0.5 Système de coordonnées et analyse du format de route
- Créés : `Scripts/Python/tsc_coords.py` (projection transverse de Mercator locale, tuiles de 1024 m), `Route/Configuration/coordinate_system.json`. Test : V1 projetée = 213,38 km, 268 tuiles traversées, aller-retour exact (écart ~1e-15°). Vérifié (calcul), non validé en jeu.
- Créé : `Documentation/TSC/route_format.md` (structure de `MainContent.ap`, tuiles de voies en courbes plan, hauteurs par ruban dans `Tracks.bin`, etc.).
- Décisions ajoutées à `TECHNICAL_DECISIONS.md`.
- Non fait : génération de la route de prototype et test dans le jeu.
- Statut : fait (analyse), prototype à faire.
- Correction : `git add -A` avait indexé les copies de fichiers du jeu (Tests/Phase1/serz_test). Dossier ajouté au `.gitignore` (contenu commercial, à ne jamais versionner ni redistribuer) et index refait ; aucun commit effectué.

### 1.3 Prototype : conventions du format et ajustement des courbes
- Analyse (sur la copie TestTraK) : `Tracks.bin` = rubans (`Network-cTrackRibbon` : GUID, longueur, hauteurs, propriétés dont électrification `OverheadWires` + blueprint de caténaire, limite de vitesse, blueprint de voie) + nœuds (`Network-cTrackNode`) qui relient les extrémités de rubans par GUID et position 0/1. Les tuiles `Track Tiles` portent la géométrie en plan. `Terrain/*.bin` = `cHeightFieldTile` avec blob de 128×128 flottants 32 bits (1 échantillon / 8 m). Un GUID `a-b-...` correspond à deux entiers 64 bits = moitiés little-endian de `uuid.bytes_le`.
- Créé `Scripts/Python/tsc_tiles.py` (lecture des tuiles de voies). **Conventions validées sur données réelles** : tuile 1024 m mesurée depuis le coin, positions absolues = tuile×1024 + coordonnée ; `CurveSign = -1` ⇒ angle atan2(Z,X) croissant ; la fin de chaque courbe coïncide avec le début de la suivante à ≤ 1 mm.
- Créé `Scripts/Python/curvefit.py` : ajustement d'une polyligne en droites/arcs continus. Essais sur V1 (PK 150-152, 140-142, 204-206) : écart max à la polyligne officielle < 1 m, dérive en fin de segment < 0,1 m (45 segments pour 2 km dans une zone très courbe).
- IGN WMS-R `ELEVATION.ELEVATIONGRIDCOVERAGE` (BIL 32 bits) testé : fonctionne, adapté à la génération de tuiles de terrain.
- Statut : fait, vérifié sur le format et le calcul (pas encore dans le jeu).
- Orientation du terrain validée par les données : comparaison des hauteurs de rubans TestTraK avec le blob de terrain : `blob[ligne = Z/8][colonne = X/8]`, sans inversion ni transposition (écart moyen 0,37 m ; autres combinaisons 1,3 à 2,4 m). Aucun ruban TestTraK ne chevauche deux tuiles (un ruban = une tuile ; nœuds entre rubans). `RouteProperties.xml` a un `Origin` Lat/Long (à régler sur 48,2 / 1,1).

### 1.4 G�n�rateur de prototype et premi�re route de test
- Cr�� Scripts/Python/gen_prototype.py (usage : python gen_prototype.py <pk_debut> <pk_fin> <nom>). Il lit la voie officielle V1, ajuste droites/arcs (�cart max 0,52 m), d�coupe aux limites de tuiles (3 rubans), calcule le profil (MNT IGN WMS-R filtr� : m�diane 300 m, moyenne 200 m, pente limit�e � 15 �), applatit un couloir de voie dans le terrain, g�n�re Tracks.xml, tuiles de voies, terrain (16 tuiles), MixMap (copie du mod�le), RouteProperties.xml (origine 48,2 / 1,1), puis convertit en .bin avec serz.exe. Vitesse de chaque ruban = vitesse max officielle SNCF au PK m�dian ; propri�t�s d'�lectrification, voie et cat�naire copi�es du mod�le TestTraK (blueprints RSC/TestTraK, provisoire).
- Bug trouv� et corrig� : lxml auto-ferme les cha�nes vides (<X d:type="cDeltaString"/>), ce qui tronquait le .bin produit par serz (3 093 octets, sans erreur affich�e). Corrig� dans write_xml ; Tracks.bin = 10 830 octets et relu int�gralement.
- Relecture des .bin g�n�r�s (serz ? XML) : 3 rubans, 4 n�uds, 19 courbes, continuit� interne OK, longueur totale 2 010 m, �cart max � la voie SNCF 0,51 m, hauteurs 102,8 � 105,8 m. V�rifi�.
- Route de test g�n�r�e : Route/Exports/proto1/bc8729b7-ca09-50b7-927b-95fbf7b40a6c (GUID d�riv� de proto1, non versionn�).
- **Modification du dossier du jeu (ajout uniquement)** : la route de test a �t� copi�e dans D:\Programmes\Steam\steamapps\common\RailWorks\Content\Routes\bc8729b7-ca09-50b7-927b-95fbf7b40a6c (46 fichiers). Aucun fichier d'origine du jeu modifi�. Suppression possible en retirant ce dossier.
- Prochaine action : lancer TSC via Steam (appid 24010) et tenter de charger la route dans l'�diteur de route.

### 1.5 Premier essai dans le jeu (route proto1)
- Lancement de TSC via Steam (Computer Use : acc�s accord� � Steam, steamwebhelper, File Explorer pour la barre des t�ches, railworks64.exe). Dialogue Dovetail Live : r�ponse � Non � (aucun compte cr��).
- **Constat� dans le jeu** : la route proto1 appara�t dans le menu Construire avec Latitude 48,2 / Longitude 1,1 (lues de mon RouteProperties.xml) ; � �diter � ouvre l'�diteur sans plantage et le jeu cr�e un dossier Scenarios dans la route. Les routes DLC LGV Rh�ne-Alpes & M�diterran�e et Marseille - Avignon sont bien install�es.
- Probl�me : l'�diteur s'ouvre sur la tuile (0,-1), alors que la voie �tait � ~24 km de l'origine (tuiles -24..-22, +10..+12) : voie non vue. Le jeu a ensuite �t� arr�t� (processus tu�) et la route test supprim�e du dossier du jeu (ma propre route g�n�r�e uniquement).
- Ajout de l'option ecentre � gen_prototype.py (test seulement : d�cale la voie pr�s de la tuile (0,0), route non g�or�f�renc�e). Route r�g�n�r�e et recopi�e dans Content\Routes\bc8729b7-�.
- Statut : l'ouverture de la route est confirm�e ; la voie dans le jeu n'est pas encore v�rifi�e.
- **Crash du jeu** (16:19) : après « Éditer » sur la route `proto1` recentrée (voie près de la tuile 0,0), `RailWorks64.exe` plante : `APPCRASH`, module `ntdll.dll`, code `0xc0000374` (corruption de tas). Aucun journal du jeu trouvé (ni `Log.txt`, ni `TempDump` récent). Le premier essai (voie à 24 km de l'origine, donc non chargée) n'avait pas planté : le plantage vient donc très probablement d'un fichier généré chargé au démarrage de l'éditeur (voies, terrain ou MixMap). Cause non identifiée.
- Constat : XML → .bin via serz donne toujours un fichier de 6-7 octets plus petit que l'original du jeu (voie 6421 → 6415 octets, terrain 65689 → 65682, MixMap 98534 → 98527). Cause inconnue, peut-être bénigne, jamais testée en jeu.
- Plan : bissection en jeu (A : voies seules sans terrain ni MixMap ; B : terrain + MixMap sans voies).
- **Bissection A (voies seules, sans Terrain ni MixMap)** : l'�diteur s'ouvre sans planter (RailWorks64 r�pond). Donc Tracks.bin et les tuiles de voies g�n�r�s sont accept�s au chargement ; le plantage vient du Terrain et/ou du MixMap. Prochain essai : terrain seul.
- Bissection B (terrain seul, sans MixMap) : le jeu se fige sur l'�cran de d�marrage (RailWorks64 ne r�pond plus, CPU fig�) ; processus tu�. Non reproduit (un seul essai). Prochain essai : MixMap seul.
- **Le�on** : lancer le jeu via le bouton JOUER de Steam. steam.exe -applaunch 24010 a fig� le jeu sur l'�cran de d�marrage deux fois (RailWorks64 ne r�pond plus) ; la route n'y est pour rien.
- **Bissection C (MixMap seul, sans Terrain)** : l'�diteur s'ouvre sans planter. Avec A (voies seules) OK et C OK, le plantage vient du **Terrain** g�n�r� (terrain seul pas encore test�).
- **Cause probable du plantage trouv�e** : les .bin du jeu pour Terrain et MixMap commencent par un bloc FF 43 00 <taille LE32> juste apr�s l'en-t�te SERZ (taille du blob + 4 : 65 540 pour le terrain, 98 308 pour la MixMap) ; serz ne l'�crit pas, d'o� 7 octets de moins, et le jeu semble sous-allouer le blob puis corrompre le tas. Corrig� dans gen_prototype.py (	o_bin(..., hint=)) : les bins g�n�r�s ont d�sormais exactement la taille et l'en-t�te des originaux (65 689 et 98 534 octets). Hypoth�se � confirmer en jeu. Route r�g�n�r�e, Terrain + MixMap recopi�s dans le dossier du jeu (ma route uniquement).

### 1.6 Première route générée chargée dans le jeu
- Test final (lancement par le bouton JOUER de Steam, route `proto1` avec voies + terrain + MixMap, en-tête de taille ajouté) : l'éditeur de route s'ouvre **sans plantage** (RailWorks64 répond, aucun nouvel événement APPCRASH). Capture d'écran : le relief IGN est affiché, la voie générée apparaît sur le terrain (barre d'état : « Réseau : Longueur 105 m, rayon de courbure 10 373 m, inclinaison 1 m 493 à 292,7 m, hauteur 103,42 »). Confirme en jeu : le tracé est lu, les hauteurs de ruban sont prises en compte, la cause du plantage était bien l'en-tête de taille manquant (hypothèse validée).
- Non vérifié : conduite d'un train sur la voie, raccords entre les 3 rubans, aspect de la caténaire/voie, orientation exacte (X est / Z nord) par rapport à la réalité, textures du terrain (MixMap copiée du modèle TestTraK, donc incohérente), longueur totale vue de l'éditeur.
- Le jeu est resté ouvert dans l'éditeur sur `proto1` (aucune modification faite dedans).

### 1.7 Générateur complet (gen_route.py) et route phase 1 (Nogent-le-Rotrou ↔ Le Mans)
- Optimisations : un seul script `Scripts/Python/gen_route.py` (remplace `gen_prototype.py` et 11 scripts d'exploration supprimés) ; deux voies V1+V2 en une passe ; MNT IGN téléchargé par tuile en parallèle avec cache disque (`GeographicData/Elevation/dem_cache_<origine>`) ; terrain et MixMap écrits par patch binaire direct des modèles du jeu (sans serz, en-tête de taille conservé) ; couloir de voie aplani via arbre KD vectorisé. Origine de projection déplacée au centre de la ligne (48,45 N ; 1,48 E, Chartres) : plus de décalage de test. Variable d'environnement `TSC_ORIGIN` réservée aux routes de vérification visuelle.
- `curvefit.fit` : ajout du raffinement par écart (segment coupé tant qu'il s'écarte de plus de 0,5 m de la polyligne officielle) : écart max passé de 7,5 m à 1,15 m (moyenne 0,13 m).
- Bug corrigé : les propriétés des rubans (électrification, limite de vitesse, blueprints) ne couvraient que les 405 premiers mètres (valeurs du modèle) et la vitesse restait à 50 ; elles couvrent maintenant toute la longueur et la vitesse est la vitesse max officielle SNCF (150, 160 ou 220 km/h).
- Route `phase1` générée en 90 s (PK 148 → 211) : 163 rubans (82 V1 + 81 V2), 126 km de voies, 252 tuiles terrain + MixMap, 41 Mo, électrifiée en caténaire (`OverheadWires`) partout. Contrôle hors jeu (`validate_route.py`) : jonctions entre rubans ≤ 5 mm, aucune discontinuité interne, hauteurs de voie 47 à 113 m.
- En jeu : `phase1` se charge dans l'éditeur sans plantage (RailWorks64 répond, 933 Mo de RAM). Route `view1` (PK 148,5-151,5, origine de test sur Nogent) : l'éditeur ouvre directement la carte 2D (touche 9 = bascule 2D/3D) et affiche bien la voie, courbe comprise, à proximité de l'origine.
- Navigation dans l'éditeur : la boîte Lat/Long du bandeau supérieur ne déplace pas la caméra (ne pas s'en servir) ; la carte 2D (touche 9) fonctionne.
- Non vérifié : l'aspect 3D de la double voie, la caténaire visible, la conduite, les textures de sol (MixMap = copie du modèle). Le jeu est resté ouvert sur `view1`. Routes `phase1` et `view1` présentes dans le dossier du jeu (ajouts de ma part uniquement).

### 1.8 Retours utilisateur : voies liss�es, hauteurs, cat�naire
- Retours de l'utilisateur apr�s essai en jeu : (1) V1 et V2 pas c�te � c�te et pas � la m�me hauteur ; (2) micro-virages sur les rails, trac� trop strict ; (3) pas de poteaux de cat�naire.
- Donn�es : �cart lat�ral V2?V1 sur PK 148-211 : m�diane 3,70 m (entraxe normal), V2 toujours � droite de V1 ; �carts jusqu'� 51 m seulement dans les gares (voies de quai). Hauteurs : chaque voie avait son profil MNT liss� s�par�ment. Correction : V2 reprend la hauteur de V1 quand les voies sont � moins de 6 m, fondu jusqu'� 12 m (gares).
- Lissage : curvefit.fit lisse la polyligne (gaussienne 30 m, extr�mit�s fixes) avant ajustement, tol�rance d'�cart 1,0 m � l'originale : 884 segments par voie au lieu de 3 036 (2 104 courbes au total au lieu de 5 682), �cart max 1,34 m, moyenne 0,26 m, jonctions = 5 mm.
- Cat�naire : **elle n'existait pas** (normal : TSC la stocke en rubans de � loft � dans Networks/Loft Tiles, pas dans les voies). Analyse de la route Marseille-Avignon (DLC) : chaque trav�e = un ruban Network-cLoftRibbon avec une courbe cCurveCatenary, pos� sur l'axe de la voie, longueur 18-51 m (m�diane 37 m), deux rubans par trav�e : blueprint RailNetwork\Gantries\Catenary_Wire_01 (type eCatenary, hauteur = voie + 5,8176 m) et Catenary_Wire_02 (eWire, voie + 7,0885 m) ; les poteaux 1 500 V (Cat_Arm_1500_*) sont ajout�s par ces blueprints. _parent_id = identifiant du r�seau de loft (Lofts.bin).
- Impl�ment� dans gen_route.py (mod�les extraits par extract_templates.py depuis la copie locale du DLC, non versionn�s) : trav�es de 20 � 45 m (plus courtes en courbe), deux rubans par trav�e et par voie. Blueprint de voie remplac� par celui du DLC (DTG/LGVMedSouth : RailNetwork\Track\track01_conc.xml, traverses b�ton) ; cat�naire proc�durale du mod�le TestTraK retir�e.
- Phase 1 r�g�n�r�e (80 s) : 6 210 rubans de cat�naire, 82 tuiles de loft, route de 46 Mo. Route de v�rification iew1 : l'�diteur la charge sans plantage avec les lofts. Copie de phase1 mise � jour dans le dossier du jeu (ajout de ma part).
- Non v�rifi� : l'apparition effective des poteaux et fils en 3D (navigation cam�ra de l'�diteur trop lente pour trouver la voie), l'aspect de la voie DLC, les d�calages StartOffsetA/B laiss�s � z�ro, la conduite.

### 1.9 Rails visibles en 2D (touche 9) mais pas dans le monde 3D
- Retour utilisateur : les voies apparaissent sur la carte 2D mais pas dans la vue 3D de phase1. Avant mes derniers changements (blueprint oxfo_padd_track01 du mod�le TestTraK, sans Loft Tiles), la voie s'affichait en 3D (captures du 2026-11-07 16:4x).
- �carts avec la route DLC identifi�s : (a) blueprint de voie DLC DTG/LGVMedSouth track01_conc sans TrackRule (le DLC en d�finit un : LGVMedSouth_Track_Rule) ; (b) pr�sence de Loft Tiles (cat�naire seule). Cause non �tablie.
- Ajout de la TrackRule DLC dans gen_route.py ; variable d'environnement TRACK_BP=testtrak pour la variante de contr�le (blueprint TestTraK, sans r�gle).
- Routes de v�rification copi�es dans le jeu (origine sur Nogent, PK 148,5-151,5, cat�naire incluse) : iewA = blueprint DLC + TrackRule ; iewB = blueprint TestTraK. Lecture : A et B visibles ? corrig� ; B seul visible ? blueprint DLC en cause ; aucune ? Loft Tiles en cause.

- **Cause trouv�e** : iewA (blueprint DLC) invisible en 3D, iewB (blueprint TestTraK) visible. Le RouteProperties.xml contient RBlueprintSetPreLoad (�quivalent de l'Object Set Filter) : le mod�le TestTraK ne pr�charge que RSC/TestTraK, donc les blueprints DTG/LGVMedSouth (voie, cat�naire) ne sont pas charg�s. Correction : gen_route.py ajoute DTG/LGVMedSouth � RBlueprintSetPreLoad (liste PRELOAD). Route de v�rification iewC copi�e dans le jeu (blueprint DLC + r�gle + cat�naire + pr�chargement). R�sultat en jeu : � confirmer.
- Retour utilisateur sur `viewC` (capture) : la voie est sélectionnable (contour rouge, gizmo) donc reconnue, mais sans aucune texture, rien de rendu. Le préchargement du DLC a donc suffi à déclarer le blueprint, pas à l'afficher.
- Essais de variantes (3 s chacun, origine sur Nogent, PK 148,5-151,5, caténaire DLC incluse) : `TRACK_BP` = `academy` (DTG/Academy `track01_conc`), `hh` (RSC/HamburgHannover `HH_Track_Concrete01`), `kuju` (Kuju/RailSimulator `oxfo_padd_track01`). Routes `view_academy`, `view_hh`, `view_kuju` copiées dans le jeu. Résultat en jeu : à confirmer. Rappel : `viewB` (RSC/TestTraK) s'affichait bien.
- Demande utilisateur : tester la voie du DLC Marseille. iewA/iewC l'utilisaient d�j� (voie + r�gle DLC, avec puis sans pr�chargement) : voie s�lectionnable mais sans rendu. Nouvel essai iew_dlc : en plus, RouteProperties.xml repris du mod�le de route du DLC (ROUTE_BASE=dlc : ciel, m�t�o, terrain, carte et pr�chargement DTG/LGVMedSouth). Copi� dans le jeu (35bfadb9-0393-5834-989f-33264c577952). R�sultat en jeu : � confirmer.
- **R�sultat** : iew_dlc affiche bien les rails (confirm� par l'utilisateur). La cause : il faut reprendre le RouteProperties.xml du mod�le de route du DLC (blueprint de route, ciel, m�t�o, terrain, carte, pr�chargement), pas seulement ajouter le produit � la liste de pr�chargement. ROUTE_BASE=dlc devient le d�faut de gen_route.py (voie DLC 	rack01_conc + LGVMedSouth_Track_Rule + cat�naire DLC).
- Retour utilisateur sur `view_dlc` : rails visibles, **aucune caténaire ni poteau**. Analyse du loft DLC : les 860 travées de la tuile (0,0) sont **toutes** reliées par des nœuds `Network-cLoftNode` (2 par travée, 1 connexion chacun : GUID du ruban + position 0 ou 1, `RouteVector` = tuile) ; mes tuiles de loft n'avaient aucun nœud. Les `.bin` de loft du DLC portent aussi l'en-tête de taille `FF 43 00 <LE32>` (non reproduit : valeur inconnue pour des fichiers sans blob).
- Correctif : `gen_route.py` écrit maintenant les deux nœuds de chaque travée (modèle `loft_node.xml` extrait du DLC par `extract_templates.py`). Route `view_dlc2` (212 nœuds pour 106 rubans dans la 1re tuile) copiée dans le jeu. Résultat en jeu : à confirmer ; si toujours rien, prochaine piste = en-tête de taille des `.bin` de loft.

### 1.10 Cat�naire : fils visibles, poteaux et pendules
- Retour utilisateur sur iew_dlc2 : fils porteur et de contact visibles ; **pas de poteaux ni de pendules**. Les n�uds de loft ont donc r�gl� l'affichage des fils.
- Poteaux : dans le DLC ce sont des entit�s de Scenery (cDynamicEntity + Network-cGantryComponent), pas des lofts. Mod�les 1 500 V extraits : LGV Gantry HPost 1500 Single Pull_L / Push_L (plac�s sur l'axe de la voie, base � la hauteur de voie, axe X de l'objet � +90� du sens de la voie ; le poteau est d�cal� dans le mod�le). Impl�ment� : un poteau au d�but de chaque trav�e, Pull/Push altern�s, orientation +90� pour V1 et -90� pour V2 (poteaux � l'ext�rieur des deux voies), GUID d�riv�s de la route. extract_templates.py extrait aussi pole_Pull.xml, pole_Push.xml et le squelette de tuile Scenery.
- Pendules : hypoth�se = les d�calages StartOffsetB/EndOffsetB du fil de contact (type eCatenary), que j'avais mis � z�ro. Relev� DLC : (�0,0077 ; -0,3176 ; �0,1163), signe altern� d'un poteau � l'autre. Appliqu� au fil de contact seulement, porteur � z�ro.
- Route iew_poles (139 poteaux sur 3 km, origine Nogent) copi�e dans le jeu. R�sultat en jeu : � confirmer.
- Retour utilisateur (capture de iew_poles) : fils, pendules et poteaux apparaissent, mais les poteaux sont **sur la voie** (bases au bord des rails). Cause : le mod�le Single_L est un poteau d'axe (suspendu), le DLC le place � 0,00 m de la voie. Mesure sur les poteaux lat�raux du DLC (LGV Gantry HPost 1500 Med Pull/Push, 2,0 � 3,4 m de la voie) : l'axe +X stock� (RXAxis) pointe vers la voie (produit scalaire 1,00) et les bras sont � -X.
- Correctif : mod�les Med Pull/Push, poteau � 2,8 m de l'axe, � l'ext�rieur des deux voies (V1 � gauche, V2 � droite), RXAxis dirig� vers la voie, regroupement par tuile selon la position finale du poteau. Route iew_poles2 copi�e dans le jeu. R�sultat en jeu : � confirmer.
- Retour utilisateur : � je ne vois vraiment rien � sur iew_poles2 : � l'ouverture l'�diteur est � l'origine, la voie de test est � 268 m au SO de l'origine (PK 148,5) et s'�loigne ; l'utilisateur ne la trouvait pas. Route iew_here (PK 148,7-150,5, origine plac�e sur V1 au PK 149,0 : lat 48,32040 / long 0,80533) copi�e dans le jeu : la voie, les poteaux et les fils passent directement sous le point d'apparition.
- Retour utilisateur sur iew_here (capture) : � les poteaux sont mal plac�s � : deux poteaux se retrouvent au niveau des rails, deux autres plus loin � l'ext�rieur. Mesure sur les fichiers de iew_here : poteaux � 2,80 m de la voie la plus proche, deux voies � 3,8 m d'entraxe, et un poteau pr�s de l'origine � 2,8 m de deux **rubans** voisins (coupure de tuile de la m�me voie), donc pas de contradiction de g�om�trie dans les donn�es.
- Changements : gen_route.py place maintenant chaque poteau du c�t� oppos� � la voie voisine (V1/V2 s'inversent dans les gares) ; distance r�glable par POLE_D. Routes copi�es dans le jeu : iew_here2 (2,8 m) et iew_d7 (7,0 m, **diagnostic** : si les poteaux ne s'�loignent pas des rails, le jeu ignore le d�calage et accroche les poteaux � la voie). R�sultat en jeu : � confirmer.
- Retour utilisateur sur `view_d7` (capture) : « poteaux par blocs de deux et pas du bon côté ». Lecture de la capture : chaque entité `HPost 1500 Med` affiche **deux montants** (un à la distance demandée, un sur la voie) : « HPost Med » est un poteau **médian en H** à deux montants, fait pour se placer entre deux voies, pas un poteau latéral. Les ~2-3 m mesurés sur le DLC étaient la distance à la voie voisine d'un poteau central. Mon choix du modèle `Med` était donc faux.
- Retour au modèle `Single Pull_L / Push_L`, placé **sur l'axe de la voie** (comme dans le DLC, où il est à 0,00 m), le côté étant porté par l'orientation du modèle. `gen_route.py` : `POLE_KIND` (`single` défaut, `med`), `ORI_FLIP` (±1, inverse l'orientation), côté extérieur calculé d'après la voie voisine. Le sens exact du « L » n'étant pas connu, deux routes de comparaison copiées dans le jeu : `view_sideA` (`ORI_FLIP=1`) et `view_sideB` (`ORI_FLIP=-1`), PK 148,7-150,5, origine sur la voie au PK 149. Résultat en jeu : à confirmer (laquelle met les poteaux à l'extérieur des deux voies, bras vers les rails, sans bloc de deux).

### 1.11 Poteaux valid�s, phase 1 r�g�n�r�e, incident de copie
- Retour utilisateur : **iew_sideB est parfait** (poteaux simples Single Pull_L/Push_L sur l'axe, ORI_FLIP=-1). Devenu le d�faut de gen_route.py.
- phase1 r�g�n�r�e (83 s) : 3 105 poteaux, 6 210 trav�es de cat�naire, 163 rubans de voie (V1+V2), contr�le alidate_route.py identique (jonctions = 5 mm, �cart max 1,34 m, vitesses 150/160/220).
- **Incident (mon erreur)** : dans mon script PowerShell, \ (dossier des routes du jeu) �crasait \ (dossier de la route export�e), les variables �tant insensibles � la casse. Copy-Item a donc copi� le dossier Content\Routes du jeu **dans lui-m�me** de fa�on r�cursive (193 Go, 222 000 fichiers) jusqu'� saturer le disque D: (0,05 Go libres). V�rifi� ensuite : les routes d'origine du jeu �taient intactes (Marseille-Avignon 267 Mo/119 fichiers, LGV Rh�ne-Alpes 763 Mo/26, Hambourg 637 Mo/2). Supprim� uniquement la copie parasite Content\Routes\ee4a17ee-� (chemin litt�ral \\?\, 124 s) ; D: repasse � 189 Go libres. Corrig� ensuite en copiant avec des noms de variables distincts (\D:\Programmes\Steam\steamapps\common\RailWorks\Content\Routes, \E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\Route\Exports\phase1\ee4a17ee-10e2-540d-a40d-750281467cb5) et un contr�le de taille.
- Retir�es du jeu les 14 routes de test obsol�tes (iewA/B/C, iew_academy/hh/kuju/dlc/dlc2/poles/poles2/here/here2/d7/sideA). Restent phase1 et iew_sideB (r�f�rence visuelle).

### Sauvegarde (demande utilisateur, 20261107-1934)
- Backups/phase1_20261107-1934.zip : route phase1 export�e (51 Mo, voies V1/V2, cat�naire, poteaux, terrain, MixMap). Backups/scripts_docs_20261107-1934.zip : scripts, documentation, configuration, documents de suivi.
- Premier commit Git du projet (scripts et documents ; les donn�es brutes, les routes export�es et les copies de fichiers du jeu sont exclues par .gitignore).

### 1.12 Zigzag d'une voie (retour utilisateur en conduite)
- Retour : en se promenant avec un train, une des deux voies fait de petits zigzags, l'autre est correcte.
- Mesure sur phase1 : alternances de sens de courbure V1 = 1 041 sur 1 220 courbes (554 � zigzags � : deux courbes courtes < 60 m de sens oppos�), V2 = 580 sur 884 (89). Cause : l'ajustement par ancrage point � point de curvefit.fit force la fin de chaque segment sur la polyligne, ce qui fait osciller la courbure, plus fort sur V1.
- Correctif : curvefit.fit_ls (moindres carr�s par blocs de 40 segments, continuit� position + cap, p�nalit� sur les sauts de courbure, pas de transformation en droite) utilis� par gen_route.py. R�sultat : 1 478 courbes au lieu de 2 104 ; zigzags V1 10, V2 7 ; �cart � la voie officielle max 1,37 m, moyenne 0,118 m (avant 0,258 m) ; rayon minimum 698 m (les 60 m d'avant �taient des artefacts) ; jonctions = 3,5 mm. Poteaux 2 849, trav�es 5 698.

### 1.13 Recadrage : une phase à la fois, +1 km de chaque côté (consigne utilisateur)
- Reproche justifié : j'avais lancé la génération de toute la ligne (PK 1,3-211, `ligne_complete`) alors que l'ordre convenu est phase par phase. Export `ligne_complete` (525 Mo, local, jamais copié dans le jeu) **supprimé**. Aucune autre phase n'est générée.
- Règle ajoutée à `CLAUDE.md` et `ROADMAP.md` : pour une phase A↔B, on travaille aussi 1 km au-delà de A et de B. Phase 1 (Nogent-le-Rotrou PK 148,113 ↔ Le Mans PK 210,980) = **PK 147,1 → 212,0**.
- `phase1` régénérée sur cette plage (37 s ; 3 tuiles de relief téléchargées en plus) : 168 rubans (84 V1 + 84 V2), 129,9 km de voies, 5 876 travées de caténaire, 2 938 poteaux, 258 tuiles de terrain. Contrôle : jonctions ≤ 5 mm, écart max 1,52 m (moyenne 0,119 m), vitesses 150/160/220. Déployée dans le jeu (51 Mo, tailles identiques).

### 2.1 Gares, �tape 1 : quais (phase 1)
- Gares voyageurs de la phase 1 (SNCF, PK 147,1-212,0) : Nogent-le-Rotrou 148,113 ; Le Theil-La Rouge 158,974 ; La Fert�-Bernard 169,025 ; Sceaux-Bo�sse 178,130 ; Connerr�-Beill� 186,739 ; Montfort-le-Gesnois 193,888 ; St-Mars-la-Bri�re 197,212 ; Champagn� 199,637 ; Le Mans 210,980 (Yvr�-l'�v�que PK 204,100 : non desservie, ignor�e). Les donn�es SNCF ne donnent que V1/V2 pour les petites gares (voies annexes seulement � Nogent : 5, et au Mans : 4) : quais ext�rieurs de chaque c�t� de la paire V1/V2.
- Quai du DLC : ruban de loft Scenery\Procedural\LGV_Pltfm (DTG/LGVMedSouth), parall�le � la voie � 2,5-3,0 m de l'axe, hauteur � voie - 0,53 m. Le sens des rubans du DLC varie (voie � gauche ou � droite) : le c�t� du profil par rapport au sens du ruban est inconnu.
- Impl�ment� dans gen_route.py : quais de 200 m (300 m Nogent, La Fert�, 400 m Le Mans) centr�s sur le PK de la gare, c�t� ext�rieur de chaque voie (d�termin� d'apr�s la voie voisine), d�calage PLT_D = 2,7 m, ajustement it_ls, d�coupe en tuiles, n�uds de loft. Option PLTFM_FLIP=1 inverse le sens du ruban. Mod�les pltfm_str.xml/pltfm_arc.xml extraits du DLC.
- Routes de test copi�es dans le jeu (origine Nogent-le-Rotrou, PK 147,1-149,3) : iew_quaisA (sens normal) et iew_quaisB (invers�). R�sultat en jeu : � confirmer.

### 2.2 Quais : assets français de l'utilisateur (auteur « Armand »)
- Retour utilisateur sur `view_quaisA/B` : quais enterrés et peu réalistes ; l'utilisateur a fourni ses assets dans `Assets/Assets/Armand/` (11 produits : `MurPierre`, `QuaiAIX`, `QuaiArc`, `QuaiBourk`, `QuaiMcd`, `QuaiMetz`, `QuaiMetz2`, `QuaiMorez`, `QuaiPLM`, `QuaiRev`, `QuaisBesançon`) — lofts de quai (`Loft section blueprint1.xml`, `cLoftSectionBlueprint`, `EditorGroundOffset` 1,2). Aucune licence ni lisez-moi fournis : usage comme **dépendance externe** uniquement, dossier exclu de Git (`Assets/Assets/` dans `.gitignore`), jamais redistribué.
- Installé dans le jeu : copie de `Armand` vers `RailWorks\Assets\Armand` (11,3 Mo, ajout seulement).
- Sections en travers lues (serz) : sommet à y=0, corps jusqu'à −1,2/−1,3 m ; largeurs : AIX 3 m, Arc 4, Bourk 3, MCD 2,5, Metz 3, Morez 5, PLM 2,5, Rev 4 (centrées sur l'axe) ; Metz2 (5 m) et Besançon (BN12 / 125M / 34 / 345M) asymétriques ; l'identifiant de section de Besançon est mal encodé (`BesanÃ§on`) : non utilisé pour l'instant.
- `gen_route.py` : quais = ruban de loft Armand le long de chaque voie, côté extérieur, axe à (1,67 m + largeur/2) de la voie (bord à 1,67 m), sommet à +0,55 m au-dessus de la hauteur de voie ; produit par `PLT_PROD` (défaut `QuaiMetz`) ; les produits Armand utilisés sont ajoutés au préchargement (`RBlueprintSetPreLoad`) même avec la base DLC. Banc d'essai `PLT_TEST=1` : tous les produits symétriques l'un après l'autre (50 m + 12 m d'intervalle) le long de V1 depuis l'origine.
- Route `view_quais_test` copiée dans le jeu (origine Nogent-le-Rotrou) ; routes `view_quaisA/B` retirées. Ordre le long de la voie vers Le Mans : AIX, Arc, Bourk, Mcd, Metz, Morez, PLM, Rev. Résultat en jeu : à confirmer (rendu, hauteur, côté).
- Choix utilisateur sur le banc d'essai `view_quais_test` : **Rev** (4 m) pour Nogent-le-Rotrou et Le Mans, **PLM** (2,5 m) pour les autres gares. `gen_route.py` : `PLT_PROD` défaut `QuaiPLM`, `STATION_PROD` = {Nogent-le-Rotrou, Le Mans → `QuaiRev`}.
- `phase1` régénérée (PK 147,1-212,0) : 23 rubans de quai (9 gares × 2 voies, découpés aux limites de tuile), 5 899 travées de caténaire, 2 938 poteaux ; préchargement `LGVMedSouth`, `QuaiPLM`, `QuaiRev` ; contrôle voies inchangé (jonctions ≤ 5 mm, écart max 1,52 m). Déployée dans le jeu (51 Mo) ; route de test `view_quais_test` retirée. Rendu des quais en jeu : à confirmer (utilisateur a déjà vu le banc d'essai, hauteur et côté non signalés comme faux).

### 2.3 Gares : « tout via Blender » (consigne utilisateur) — recherche de la chaîne et première référence
- Consigne : générer les éléments de gare via Blender, d'après des photos réelles (Google/Commons), puis les modéliser.
- Blender 5.2.3 LTS connecté ; add-on **BRIAGE 4.1** (`bl_ext.user_default.briage`, licence MIT) déjà installé : export `.igs`/`.ia` opérationnel. Test : cube texturé exporté en `.igs` dans `Assets/Custom/Proto/` (une collection `TSC_Proto` ajoutée à la scène Blender par défaut non enregistrée ; scène d'origine non supprimée).
- `ConvertToGEO.exe` du jeu (testé, shaders copiés depuis `dev\Shaders` dans un dossier temporaire) ne produit que du `.GeoPs2` : la compilation PC (`.GeoPcDx`/`.TgPcDx`) passe par le Blueprint Editor. Voir `Documentation/TSC/asset_pipeline.md`.
- **Référence réelle, Nogent-le-Rotrou** (Wikipédia : Gare de Nogent-le-Rotrou ; Commons : photo « Gare de nogent le rotrou - panoramio.jpg », CC) : gare ouverte en mai 1857 ; PK 148,113 ; alt. 109 m ; **3 voies + 1 voie en impasse + voies de service ; 2 quais : 1 central + 1 latéral, changement de quai par souterrain** (rehaussement et 2 ascenseurs, travaux 2020). Bâtiment voyageurs : corps central à pavillon, toit d'ardoise en croupe, deux souches de cheminée en brique, murs en moellons (silex/calcaire) avec chaînes d'angle en pierre blanche, encadrements d'ouvertures cintrées en brique rouge, aile basse avec **marquise en fer** sur poteaux côté quai, panneau « NOGENT-LE-ROTROU » sur la façade, mobilier (bancs bleus, éclairage).
- **Conséquence** : ma pose de quais « un par voie à l'extérieur » est fausse pour Nogent (quai central + quai latéral + souterrain) ; à corriger avec la vraie configuration de chaque gare.
- **Blueprint Editor piloté (Computer Use, accord utilisateur)** : v72.4a ; « Invalid source path! » car `RailWorks\Source` n'existe pas sur l'install Steam → création de `RailWorks\Source\PCLM\Gares\Scenery\Buildings\` (mes dossiers uniquement, ajout) avec `TestBuilding.igs` + `Textures\TestTex.png`. Clic droit sur le `.igs` → « Create scenery blueprint », enregistré, Export With References : 1re tentative en échec (« Failed to find ...TestTex.ace ») car il faut des textures **ACE** ; conversion PNG→ACE avec **RWAceTool** (interface graphique, 476 o) ; **2e export réussi** : `Assets\PCLM\Gares\Scenery\Buildings\TestBuilding.{xml,bin,GeoPcDx}` + `Textures\TestTex.TgPcDx`. La sortie du Blueprint Editor révèle les commandes `ConvertToTg` / `ConvertToGeo` / `serz` (voir `Documentation/TSC/asset_pipeline.md`). `ConvertToGeo -pc` utilisable en ligne de commande ; seule la conversion PNG→ACE reste graphique.
- `gen_route.py` : pose d'objets de décor depuis `Route/Configuration/objects.json` (modèle `obj_template.xml` extrait du DLC par `extract_templates.py`). Route de vérification `view_gare` (origine sur la gare de Nogent, PK 147,5-149,5) copiée dans le jeu : une boîte « TestBuilding » (10×6×4 m, texture à damier rouge/beige 64 px) à 14 m à gauche de V1 au PK 148,113. Résultat en jeu : à confirmer.

### 2.4 Bâtiment voyageurs de Nogent-le-Rotrou (modélisé par script Blender)
- Retour utilisateur : la boîte de test `view_gare` s'affiche (rouge/rose saumon) : **chaîne Blender → jeu validée en conditions réelles** (IGS, ACE, blueprint, pose par `objects.json`).
- `Scripts/Blender/gare_nogent.py` : génère 12 textures procédurales (moellon, pierre blanche, brique, ardoise, crépi, vitrage, fer, porte, zinc, béton, panneau, noir), le maillage (159 faces, 12 matériaux `IgsMat` `TexDiff`) et l'exporte en `GareNogent.igs`. Modèle : pavillon central 11×9 m (moellons, chaînes d'angle en pierre blanche, toit d'ardoise en croupe, 2 souches de cheminée en brique, lucarnes), aile gauche 14×7 m (crépi, 4 baies cintrées + porte), aile droite 9,5×7,5 m (moellons, 2 grandes baies cintrées à encadrement de brique), panneau de nom sur la façade, marquise en fer de 25 m sur poteaux (toit en zinc), 2 bancs. Dimensions **estimées d'après la photo** (non mesurées). Repère : X le long de la voie, façade côté quai à Y=0.
- Blender s'était fermé (connexion MCP perdue) : script exécuté dans une session Blender graphique éphémère (`blender.exe --python`, minuteur + `wm.quit_blender()`), car l'export BRIAGE échoue en mode `-b` (`wm.redraw_timer`).
- Textures PNG → ACE par lot avec RWAceTool (« Multiple image conversion », 12 fichiers). Blueprint Editor : « Create scenery blueprint » sur `GareNogent.igs`, `Ctrl+S`, F7 : **Export Succeeded** → `Assets\PCLM\Gares\Scenery\Buildings\GareNogent.{xml,bin,GeoPcDx}` + textures `.TgPcDx`. Sources versionnées dans `Assets/Custom/PCLM_Gares_Source/` (créées par nous).
- Routes de vérification : `view_gare0` et `view_gare180` (origine sur la gare de Nogent, PK 147,5-149,5) : bâtiment à 10 m à gauche de V1 au PK 148,113, cap relatif 0° / 180° pour trouver l'orientation de la façade. `Route/Configuration/objects.json` : version cap 0°. `OBJECTS_FILE` permet d'indiquer un autre fichier d'objets. Résultat en jeu : à confirmer.

### 2.5 Nogent-le-Rotrou : BV remodelé d'après photos (2026-11-07)
- Emprises IGN BD TOPO projetées dans le repère de V1 (origine = point de V1 le plus proche de la gare SNCF, gauche > 0) : BV 1 niveau en 3 volumes, L -70…-6 m, latéral -52…-31 m (hauteurs 5,1-6,5 m) ; grand bâtiment L +20…34, latéral -73…-40 (7,9 m). Source : `GeographicData/Raw/bdtopo_nogent_batiment.json`. Dimensions fines des ailes **à vérifier** (modèle approximatif).
- `Scripts/Blender/gare_nogent.py` réécrit d'après les 6 photos : pavillon central 2 niveaux crépi crème (toit ardoise en croupe, fronton à horloge, 3 portes cintrées, fenêtres cintrées à volets saumon, moulures rouges, cheminées briques), ailes en moellons 1 niveau avec bandeau rouge, bâtiment 2 niveaux en brique à une extrémité, marquise métallique côté quai. Nouvelle texture `Volet`. Généré, exporté IGS (232 faces), PNG→ACE (RWAceTool, 13 textures), compilé par Blueprint Editor (F7, GeoPcDx 46 Ko). **Pas encore vu en jeu.**
- `Route/Configuration/objects.json` : pk 148,089, latéral -34,5 (côté droit de V1, façade vers les voies), cap 180° (X modèle vers Paris). Route de test `view_gare180` régénérée (origine gare) et recopiée dans `Content\Routes\8c69da3d-…` (route de test à moi, pas un fichier d'origine). Orientation et position à valider en jeu.

### 2.6 Nogent-le-Rotrou : BV v2, deux façades distinctes (2026-11-07)
- Retour utilisateur : le modèle 2.5 ne ressemblait pas aux photos. Nouvelles références : photo de façade côté place (pavillon crépi blanc 2 niveaux à horloge, ailes en moellons ocre, grandes baies cintrées à gauche, 8 petites baies à droite, toit ardoise) et deux vues Google Maps côté quai (moellons, encadrements brique, volets saumon à l'étage du pavillon, balustrades, marquise à poteaux).
- `gare_nogent.py` refait : façade côté place (Y=D, par miroir `y' = D - y`) et façade côté quai (Y=0) distinctes ; bâtiment en brique supprimé (non confirmé par les photos) ; aile longue côté Le Mans (-34…-6 m) et aile à 3 grandes baies côté Paris (6…28 m), pavillon 12 m. Faces des boîtes orientées vers l'extérieur. Textures Moellon ocre, Crepi blanc cassé, Porte gris clair, VoletGris.
- Aperçus Workbench : `Tests/Phase1/previews/gare_place.png`, `gare_quai.png` (`Scripts/Blender/preview_gare.py`). Comparés à la photo de façade : proportions et matériaux proches ; texture moellon en bandes verticales (UV) à améliorer ; quelques éléments non confirmés (côté des ailes, position exacte).
- Export IGS (254 faces), PNG→ACE (14), Blueprint Editor F7 : OK (GeoPcDx 58 Ko). **Pas encore vu en jeu.**

### 2.7 Toutes les voies Nogent ↔ Le Mans (2026-11-07)
- Décision utilisateur : les modèles 3D de gare sont mis de côté (jugés mauvais) ; `Route/Configuration/objects.json` vidé (`[]`). Priorité : poser **toutes** les voies de la phase 1 (PK 147,1 → 212,0).
- Sources de voies (hiérarchie CLAUDE.md) : (1) SNCF open data 420000 « formes des voies » : V1, V2 + 28 voies VPA (voies de gare 3/12/14/S/TI à Nogent, 6/7/1/10 au Mans, évitements, communications J####) ; (2) IGN BD TOPO `troncon_de_voie_ferree` (WFS Géoplateforme, 169 tronçons dans 600 m de V1, `GeographicData/Raw/bdtopo_voies_phase1.json`) : 21 voies de service, raccordements LGV/principales hors SNCF ; (3) OpenStreetMap (Overpass, `osm_voies_phase1.json`, 222 ways retenus) uniquement là où (1) et (2) ne couvrent pas (écart minimal 3,5 m) : voies de garage et faisceaux (Nogent, Le Theil, Connerré, Saint-Mars, Le Mans). Tramway et voies non exploitées exclus.
- Scripts : `Scripts/Python/fetch_bdtopo_voies.py`, `fetch_osm_voies.py`, `extra_tracks.py` (→ `GeographicData/Processed/extra_tracks_phase1.json`, 289 voies, ~68 km). `gen_route.py` : voies supplémentaires ajoutées après V1/V2 (hauteur alignée sur V1/V2 à moins de 12 m, vitesse 40 km/h, caténaire et poteaux seulement si électrifiées ; quais toujours sur V1/V2 uniquement). `NO_EXTRA=1` les désactive.
- Limite connue : **les voies supplémentaires ne sont pas encore reliées à V1/V2 par des aiguillages** (rubans indépendants avec nœuds d'extrémité) : visibles et circulables isolément, pas de passage d'une voie à l'autre. À faire (nœuds à 3 connexions). Quais des voies de garage non posés.
- Test Le Mans (PK 209,5-212,0) généré, contrôle hors-jeu : 162 rubans, 0 manquant, V1/V2 inchangées. Pas encore chargé dans le jeu.
- Sauvegarde de l'export précédent : `Backups/phase1_export_avant_voies_supplementaires_20261107.zip`.
- Phase 1 complète régénérée (64 s) : 527 rubans, 789 nœuds, 0 ruban manquant, 188 km de voies (V1/V2 + 289 voies supplémentaires), 7 561 travées de caténaire, 3 769 poteaux, 23 quais. Déployée dans Content\Routes\ee4a17ee-… (route phase1, mon ajout). **Chargement en jeu non testé.**

### 2.8 Aiguillages fonctionnels, sol sous les rails, saut-de-mouton LGV (2026-11-07)
Demande utilisateur : voies posées de façon ultra propre, tous les aiguillages fonctionnels, rails sur le sol (le terrain cachait certains rails), LGV de Connerré passant au-dessus des voies classiques, relief et éléments respectés. Travail de Nogent vers Le Mans.
- **Réseau** (`Scripts/Python/netbuild.py`, `gen_route.py`) : détection des raccordements entre voies (extrémité à moins de 5 m d'une autre voie, angle < 45° : aiguillage en T ou jonction bout à bout) ; voies traitées de la mère vers la branche ; position exacte de l'aiguillage sur la voie mère ajustée, voie mère coupée en deux rubans à cet endroit ; la voie déviée part tangente à la voie mère (courbe de Hermite puis `fit_ls` avec cap de départ et d'arrivée imposés, `curvefit.py`) ; hauteur de la branche raccordée exactement à celle de la voie mère (correction estompée sur 120 m).
- **Nœuds d'aiguillage** : modèle relevé dans le DLC Marseille-Avignon (`Network-cTurnoutPattern`, moteur `Automatic_Junction_Motor`, état `straightOnState`) ; ordre des connexions [tige, voie directe, voie déviée] (la tige est toujours en 1ʳᵉ position dans le DLC ; analyse de 75 aiguillages). Gabarit : `Tests/Phase1/marseille/turnout_node.xml` (non versionné).
- **Résultat phase 1 complète (hors jeu)** : 262 voies, 724 rubans, **195 aiguillages**, 70 jonctions bout à bout, 187 bouts libres (extrémités de voies de garage, butoirs). Contrôle `validate_network.py` : écart de position aux nœuds max 0,22 m (moyenne 4 mm), écart de hauteur 0,000 m, rupture de cap des jonctions max 5,3°, tige alignée avec la voie directe (0,0°), voie déviée au plus 5,8° de la tige. 15 raccords impossibles (voies de moins de 40 m dont les deux tangentes imposées sont incompatibles avec un rayon ≥ 60 m) laissés libres. 
- **Sol** : plateforme plane à (hauteur de voie − 0,30 m) sur 11,5 m autour de chaque axe (la grille terrain fait 8 m, ce qui laissait des triangles au-dessus des rails), raccordée au relief sur 14,5 m ; le sol suit la plus basse des voies voisines (à 12 m) ; remblai limité à 8 m ; sous un pont signalé par BD TOPO (`position_par_rapport_au_sol = 1`) le sol reste au relief ; hauteurs des voies parallèles à moins de 12 m alignées entre elles. Contrôle chiffré : sol au-dessus du rail − 12 cm sur 10 voies sur 262, avec au plus 4 points à quelques cm (0,02 à 0,11 m).
- **Saut-de-mouton LGV (Connerré, PK 189-191)** : les voies LGV (BD TOPO, nature LGV) gardent leur altitude photogrammétrique (pente max 3,5 %). Les croisements entre voies non raccordées sont détectés ; hauteur libre exigée 6,5 m : voies supplémentaires relevées localement (3 relevées de 2,2 à 5,0 m), ce relevé s'annule aux extrémités raccordées. Le croisement n'était pas détecté avant car le tronçon était coupé de 2,5 m de part et d'autre de V1 (`extra_tracks.py` conserve maintenant les franchissements).
- **À traiter** : 101 croisements de voies au même niveau non raccordés (traversées-jonctions dans les faisceaux, à vérifier sur photos aériennes) ; ouvrage du saut-de-mouton (tablier) non modélisé ; voies posées sur le sol sans ballast spécifique ; pas encore testé en jeu (voir ci-dessous).

### Installation omniroute sur D: (2026-11-07)
- Action : installation globale npm du paquet omniroute (v3.8.53 au registre) avec cache et préfixe sur D: (
pm install -g omniroute --cache D:\npm-cache --prefix D:\npm-global). Dossiers créés : D:\npm-cache, D:\npm-global. Motif : une première tentative sur C: avait échoué (ENOSPC, C: à 0,03 Go libres).
- Fichiers concernés : D:\npm-global\ (binaires omniroute.cmd, omniroute.ps1, omniroute-reset-password.*, 
ode_modules\omniroute), D:\npm-cache\. Aucun fichier du projet modifié.
- Résultat : installation terminée (1209 paquets, 2 min, code de sortie 0). Avertissements npm : Node v22.11.0 en dessous des versions requises par certaines dépendances (undici, chokidar), et deux paquets dépréciés.
- Vérifié : le binaire répond (omniroute --version affiche 3.8.48, ce qui diffère de la 3.8.53 vue au registre, non expliqué). Non vérifié : fonctionnement réel du routeur, configuration, et ajout de D:\npm-global au PATH (non fait).
- Constat C: : espace libre passé à 11,48 Go au moment de la vérification (cause non identifiée : pas de nettoyage volontaire de ma part). Dossier C:\Users\Florent\AppData\Roaming\npm\node_modules pèse 4,1 Go, non touché.

### PATH utilisateur : ajout de D:\npm-global (2026-11-07)
- Action : ajout de D:\npm-global à la variable d'environnement PATH de l'utilisateur (portée User, via [Environment]::SetEnvironmentVariable), en fin de liste. Demande explicite de l'utilisateur.
- Fichiers concernés : aucun fichier ; variable d'environnement utilisateur uniquement. PATH machine non modifié.
- Résultat : entrée présente dans le PATH utilisateur (relu après écriture). Les shells déjà ouverts doivent être relancés.
- Vérifié : dans un processus PowerShell neuf, rechargé depuis le registre, Get-Command omniroute résout vers D:\npm-global\omniroute.ps1 et omniroute --version répond 3.8.48.

### Diagnostic nvm install 26 : droits sur D:\Programmes (2026-11-07)
- Action : lecture seule des ACL de D:\Programmes, de l'identité Windows courante et de D:\npm-cache ; test d'écriture (création puis suppression de D:\npm-cache\acltest). Rien d'autre modifié.
- Constat : le SID de l'utilisateur courant est S-1-5-21-1691047500-3937676303-2751990884-1001. Le dossier D:\Programmes accorde le contrôle total à S-1-5-21-3597605572-2120357332-1775334742-1001 (même RID 1001, autre machine ou autre installation). Le compte courant n'y a donc pas de droit explicite d'écriture. L'écriture dans D:\npm-cache réussit.
- Résultat : 
vm install 26 échoue car il tente de créer des sous-dossiers dans D:\Programmes et de modifier son ACL. Aucun changement de droits effectué.
- Non vérifié : la cause exacte de l'échec côté nvm (le nvm utilisé dans le terminal de l'utilisateur n'est pas visible depuis ma session).

### Création de D:\nvm (2026-11-07)
- Action : création du dossier vide D:\nvm (demande de l'utilisateur, pour remplacer D:\Programmes comme racine de nvm).
- Fichiers concernés : D:\nvm\ (dossier vide). Aucun fichier existant modifié.
- Non fait : aucune variable d'environnement modifiée. La variable racine lue par le nvm de l'utilisateur est inconnue (ni NVM_HOME, NVM_DIR ni NVM_SYMLINK ne sont définies, et le profil PowerShell ne contient pas de réglage nvm visible).
- Vérifié : D:\nvm existe.

### Tentative de changement de racine nvm vers D:\nvm (2026-11-07)
- Constat : le nvm installé est C:\Users\Florent\AppData\Local\Author Software\nvm\nvm.exe (nvm-windows Community 2.0.1). Sa racine est stockée dans HKCU\Software\Author Software\Preferences\nvm (valeur InstallRoot = D:\Programmes\NVM). Les clés de config sont oot et llow_root_dir_change.
- Action : 
vm config set root=D:\nvm puis 
vm config set allow_root_dir_change=true puis de nouveau oot=D:\nvm. Les trois ont échoué (code 1) : nvm tente de durcir l'ACL de D:\Programmes avant d'écrire la config.
- Résultat : aucune modification persistante ; InstallRoot reste D:\Programmes\NVM, llow_root_dir_change reste vide. Je n'ai pas modifié le registre à la main.
- Non vérifié : 
vm install 26, et l'utilisation de D:\nvm.

### Modification puis retour du registre nvm (2026-11-07)
- Action : HKCU\Software\Author Software\Preferences\nvm, valeur InstallRoot : D:\Programmes\NVM -> D:\nvm (demande explicite de l'utilisateur), puis retour à D:\Programmes\NVM.
- Résultat : avec D:\nvm, nvm refuse toutes les commandes et tente de durcir l'ACL de D:\ (could not harden directory ACL for D:\: Access is denied). Le retour à l'ancienne valeur rétablit l'état d'origine ; 
vm list affiche de nouveau les mêmes erreurs qu'avant.
- Non fait : 
vm install 26 non lancé, car nvm bloque sur les droits de dossier quelle que soit la racine choisie.
- Vérifié : la valeur est bien revenue à D:\Programmes\NVM. Aucun fichier de Node n'a été installé.

### Droits sur D:\Programmes et installation de Node 26 via nvm (2026-11-07)
- Action : console élevée (UAC validée par l'utilisateur) : icacls "D:\Programmes" /grant "DESKTOP-3BSAI5E\Florent:(OI)(CI)F". Ajout d'un droit de contrôle total pour le compte courant sur ce dossier seul, avec héritage ; pas de récursion. Aucune autre ACL modifiée.
- Action : 
vm install 26 avec la racine d'origine D:\Programmes\NVM (valeur de registre remise à l'identique après le test sur D:\nvm).
- Résultat : icacls terminé sans erreur. nvm installe Node.js 26.13.0, code de sortie 0, et le signale comme version par défaut.
- Vérifié : la nouvelle entrée apparaît dans l'ACL de D:\Programmes. Installation de Node 26.13.0 confirmée par nvm. Non vérifié : 
ode --version dans un nouveau terminal, et le comportement des autres dossiers de D:\Programmes.

### PATH utilisateur : dossier de nvm (2026-11-07)
- Action : ajout de C:\Users\Florent\AppData\Local\Author Software\nvm au PATH utilisateur (fin de liste), pour que 
vm soit reconnu dans un nouveau terminal. Demande de l'utilisateur (nvm absent des nouveaux terminaux). PATH machine non modifié.
- Constat : D:\Programmes\.nodejs figurait déjà dans le PATH utilisateur (ajouté par nvm lors de l'installation).
- Vérifié : dans un PowerShell neuf rechargé depuis le registre, 
vm est résolu vers 
vm.exe ; 
vm list indique 26.13.0 par défaut ; 
ode --version affiche v26.13.0.
- Non vérifié : comportement après redémarrage de la session Windows.

### nvm reshim et réinstallation d'omniroute (2026-11-07)
- Action : 
vm reshim (réponse : shims à jour). Puis 
pm install -g omniroute --cache D:\npm-cache --prefix D:\npm-global avec npm géré par nvm (Node 26.13.0).
- Résultat : installation terminée, code de sortie 0 (183 ajoutés, 65 retirés, 1144 modifiés, 7 min). Le blocage NVM4306 n'est plus signalé.
- Non exécutés : les scripts d'installation des paquets (postinstall d'omniroute, keytar, esbuild, etc.), que npm signale comme non autorisés. Non lancés, car ce sont des scripts de paquet tiers.
- Vérifié : D:\npm-global\omniroute.cmd --version est lancé (voir version ci-dessus). Non vérifié : le fonctionnement du routeur.

- Correction (même date) : la vérification de version a été faite après coup, dans un PATH neuf : omniroute --version affiche 3.8.53, identique au registre. L'ancienne valeur 3.8.48 venait de l'installation précédente, désormais remplacée. Le lancement initial de D:\npm-global\omniroute.cmd avait échoué faute de node dans le PATH de ce shell, ce qui ne reflète pas l'installation.
- Test en jeu : non fait (lancement Steam par Computer Use refusé par l'utilisateur). Route phase1 déployée dans Content\Routes\ee4a17ee-… ; à charger par l'utilisateur (bouton JOUER > Construire > phase1).

### 2.9 Gares définies pour les scénarios (2026-11-08)
- Retour utilisateur : le réseau de la phase 1 testé en jeu est « pas mal ». Demande : définir les gares et leurs voies (« Gare voie 1, 2… ») pour qu'elles apparaissent dans l'interface et servent aux scénarios, sans attendre la fin du décor.
- Modèle relevé dans le réseau du DLC Marseille-Avignon : `Network-cTrackMarkerProperty` (blueprint `Kuju/RailSimulatorCore`, `RailNetwork\Markers\Platform marker.xml` pour l'arrêt en gare, `Destination marker.xml` pour les destinations de scénario). Gabarits : `Tests/Phase1/marseille/marker_platform.xml`, `marker_destination.xml` (non versionnés).
- `gen_route.py` : 25 voies à quai reçoivent un repère Platform (longueur de quai de la gare : ±100 m, ±150 m Nogent, ±200 m Le Mans) et un repère Destination de 20 m au centre. Nom `<gare> Voie <n>`. n = numéro SNCF de la voie quand il existe (Nogent 12, 14 ; Le Mans 1, 6, 7, 10 ; Connerré 6) ; V1 et V2 prennent les deux plus petits numéros libres de la gare. **Numérotation réelle des voies SNCF à confirmer** (aucune source ouverte trouvée pour V1/V2).
- Gares : Nogent-le-Rotrou (1, 2, 12, 14), Le Theil-La Rouge (1, 2), La Ferté-Bernard (1, 2), Sceaux-Boësse (1, 2), Connerré-Beillé (1, 2, 6), Montfort-le-Gesnois (1, 2), Saint-Mars-la-Brière (1, 2), Champagné (1, 2), Le Mans (1, 2, 3, 6, 7, 10). Lus après serz : 25 noms, accents corrects.
- Limite : un repère par voie tient dans un seul ruban (le plus long chevauchement avec le quai) ; il peut donc être plus court que le quai si la voie change de tuile. Pas encore vu en jeu.

- 2.9 bis (2026-11-08) : retour utilisateur : chaque quai apparaissait en double (repères Platform et Destination de même nom) et 12/14 de Nogent sont des voies de service. Repères Destination supprimés ; voies à quai = V1/V2 + voies numérotées du Mans + voie SNCF « S » de Nogent nommée « Voie SP » (à confirmer) ; 23 repères, chaque nom une seule fois.

### 2.10 Échangeur LGV de Connerré (2026-11-08)
- Retour utilisateur : l'échangeur LGV faisait des aiguilles au lieu de passer par-dessus. Cause : le raccord de deux voies ne tenait compte que de la distance en plan ; aux PK 190,1-190,3 les voies LGV (altitude BD TOPO 75,8-76,6 m) passent à 7 m au-dessus de V1/V2 (68,6-69,1 m) mais étaient raccordées. Règle ajoutée dans gen_route.py : raccord refusé si les altitudes BD TOPO des deux voies diffèrent de plus de 2 m (1 raccord refusé en phase 1). Restent les vrais aiguillages de raccordement du secteur (PK 189,05, 190,95, 191,74). Résultat : 194 aiguillages, écarts nœuds inchangés. Export régénéré ; **non déployé** (jeu ouvert), à copier après fermeture du jeu.

### 2.11 Signalisation BAL (2026-11-08)
- Demande utilisateur : poser les signaux. Sources : OSM (niveau 2) pour les signaux cartographiés (35 principaux/violets entre Connerré et Le Mans, 58 butoirs) ; SNCF « liste des circuits de voie » (niveau 1) pour les feux de cantonnement : en BAL un circuit = un canton, les limites de circuits entre gares donnent les emplacements des feux (positions **déduites, à vérifier**, aucune source ouverte des signaux réels trouvée pour le tronçon Nogent-Connerré). Mode de cantonnement SNCF : Block automatique lumineux sur toute la phase 1.
- Modèles du DLC Marseille-Avignon (`Network-cSignalProperty`, `RailNetwork\Signals\*`) : `BAL_FE_0` (poteau, plaque F) pour les feux de cantonnement en pleine voie ; `BAL_NfB_0` (plaque Nf, non franchissable) pour les carrés aux entrées/sorties de gare ; `BAL_Nf2_1` (cible de manœuvre) pour les carrés violets ; `EndOfTrack` pour les butoirs. Gabarits : `Tests/Phase1/marseille/sig_*.xml` (non versionnés).
- Convention relevée sur 114 signaux du DLC : l'axe Z de l'objet pointe dans le sens servi (`_direction` forwards = sens du ruban), signal à gauche du sens de marche (3 m de l'axe). Sens des voies calé sur les signaux OSM : V1 = sens Paris, V2 = sens Le Mans.
- Résultat : 206 signaux (123 BAL_NfB_0, 25 BAL_FE_0, 58 EndOfTrack). Pas de KVB/crocodiles/panneaux TIV (non posés), pas de signaux de manœuvre dans les gares secondaires. **Non testé en jeu** ; fonctionnement du script `Main` du DLC (aspects automatiques) à vérifier.
- Scripts : `fetch_osm_signaux.py` ; l'e-mail a été retiré du User-Agent des scripts Overpass.
