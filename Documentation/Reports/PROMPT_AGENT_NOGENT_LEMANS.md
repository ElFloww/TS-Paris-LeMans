# PROMPT — Agent de finition « Nogent-le-Rotrou ↔ Le Mans » (Train Simulator Classic)

> À coller tel quel comme premier message de l'agent. Rédigé le 2026-11-08. Tout ce qui est écrit « vérifié » a été contrôlé par script ; « non vérifié » veut dire qu'aucun test en jeu n'a eu lieu. L'agent doit appliquer la même discipline.

## 0. Ta mission en une phrase
Terminer la route Train Simulator Classic (TSC, version Steam officielle) **Nogent-le-Rotrou (PK 148,113) ↔ Le Mans (PK 210,980)** (phase 1, PK 147,1 à 212,0, ligne SNCF 420000 Paris-Montparnasse–Brest) pour qu'elle **ressemble le plus possible à la réalité** : tracé, voies de gare, aiguillages, quais, signaux, pancartes, passages à niveau, routes, ponts, eau, relief, champs, végétation, maisons. **Les assets 3D (modélisation Blender) viennent TOUT À LA FIN**, une fois tout le reste validé en jeu par l'utilisateur.

## 1. Règles non négociables (elles priment sur tes habitudes)
1. Lis d'abord `CLAUDE.md`, `PROJECT_STATUS.md`, `TECHNICAL_DECISIONS.md`, `ISSUES.md`, `history.md` (1ʳᵉ à dernière ligne), `Documentation/TSC/route_format.md`, `Documentation/TSC/asset_pipeline.md`.
2. **Journal obligatoire** : chaque action qui crée/modifie/supprime un fichier, télécharge ou lance le jeu est consignée dans `history.md` (date, action, fichiers, résultat, vérifié ou non), dans la même session.
3. **Honnêteté** : distingue « généré » / « converti » / « chargé dans le jeu » / « testé en conduite ». Ne jamais écrire « fait » sans preuve (commande + sortie, ou capture de l'utilisateur). Si une mesure contredit une impression, donne la mesure.
4. **Rien de destructif** : ne modifie ni ne supprime aucun fichier d'origine du jeu ni asset commercial. Sauvegarde avant toute modification d'une route existante (`Backups/`, gitignoré). Déploie les essais dans **de nouvelles routes de test** (nouveau nom → nouveau GUID) ; ne remplace `phase1` qu'après validation.
5. **Seule installation de référence** : `D:\Programmes\Steam\steamapps\common\RailWorks` (TSC Steam officiel). La copie `D:\programmes\steam\steamapps\common\Train Simulator 2019` (crack) ne doit être ni lue, ni utilisée, ni modifiée.
6. **Assets** : les assets commerciaux/DLC restent des dépendances externes (Object Set Filter), jamais copiés ni redistribués. Aucun téléchargement d'asset communautaire sans l'accord explicite de l'utilisateur (nom, source, taille, licence), puis note dans `ASSET_INVENTORY.md`.
7. **Sources** : hiérarchie officielle SNCF/IGN > OSM > sites de contrôle visuel (Carto Tchoo, OpenRailwayMap, photos). Chaque valeur retenue cite sa source dans `RAILWAY_DATA.md`. Ne jamais inventer une valeur (« inconnu » ou « à vérifier »). Pas de Google Maps comme source de données (conditions d'usage) : orthophotos IGN BD ORTHO (licence ouverte).
8. **Une phase à la fois** (phase 1 uniquement). 1 km de marge au-delà de chaque extrémité.
9. L'utilisateur est le **seul juge du rendu en jeu** : il teste dans l'éditeur (bouton JOUER de Steam, puis Construire) et envoie des captures. Ne lance pas le jeu par automatisation d'écran sans son accord. Ne dis jamais que quelque chose « rend bien » sans retour de sa part.
10. Réponses à l'utilisateur en français, courtes : ce qui est fait, ce qui est vérifié, ce qui reste. Ne jamais faire apparaître son adresse e-mail dans un User-Agent, une URL ou une requête.
11. Économie : confie les tâches mécaniques (téléchargements, comptages, tracés de contrôle, copie/déploiement) à des sous-agents peu coûteux si ton environnement le permet ; garde la conception et la vérification.

## 2. État du projet au 2026-11-08 (point de départ)
Sauvegarde faite avant ce prompt : étiquette Git `sauvegarde-2026-11-08` + archives dans `Backups/sauvegarde_20261108_*.zip` (manifeste `Backups/sauvegarde_20261108_manifest.txt`).

| Couche | État | Preuve |
|---|---|---|
| Voies V1/V2 (SNCF « formes des voies ») | généré, ajusté (droites/arcs, moindres carrés), **chargé en jeu** (testé par l'utilisateur) | utilisateur : « pas mal » |
| Voies de gare/garage/service (SNCF VPA + BD TOPO + OSM) : 262 voies, ~188 km | généré, **chargé en jeu** ; **Nogent jugé « posé n'importe comment »** (voir §3) | `validate_network.py` OK hors jeu |
| Aiguillages : ~188-194, nœuds `cTurnoutPattern` du DLC | généré, chargé en jeu (« pas mal ») ; bascule et circulation **non vérifiées** | écarts ≤ 22 cm, hauteurs identiques (hors jeu) |
| Saut-de-mouton LGV de Connerré (PK 189-191) | altitudes BD TOPO, voies relevées à 6,5 m de hauteur libre ; **tablier non modélisé** | utilisateur a demandé la correction, dernier retour : non revu |
| Terrain (relief IGN RGE ALTI, 8 m), plateforme sous les rails | `phase1` déployée avec relief sur 1 tuile ; le code génère maintenant 3 tuiles (`TERRAIN_RING`) mais **seule `view_decor` l'a été** | utilisateur : « topographie bien plate » |
| MixMap (textures de sol) | **copie du gabarit** : aucune peinture par occupation du sol | — |
| Caténaire (fils, pendules) + poteaux | posés ; poteaux côté libre, 281 omis dans les faisceaux ; **jamais validé que la caténaire des voies de garage est correcte** | — |
| Quais : lofts Armand (QuaiRev à Nogent/Le Mans, QuaiPLM ailleurs) d'après tracés OSM `railway=platform` | 38-39 rubans ; **utilisateur : quais obliques et décalés** sur une capture de Nogent | — |
| Repères de gare (marqueurs Platform) : 23 « <gare> Voie n » | générés ; **jamais revus dans l'éditeur de scénarios** ; numérotation V1=1, V2=2 confirmée par OSM sauf Le Mans | — |
| Signaux : 130 signaux SNCF réels (CARRE, S, CV, portiques) + 58 butoirs | générés et déployés ; **aspects/fonctionnement non vérifiés** ; le sens (conduite à gauche, V1 = sens Le Mans, V2 = sens Paris) est confirmé par les données SNCF | — |
| Pancartes (203, hors signaux : TIV, chevrons, Z, ID…) | **données prêtes, non posées** ; signification des codes `type_if` **inconnue** | `Processed/layers/pancartes.json` |
| Passages à niveau (18 en phase 1, SNCF) | **données prêtes, non posés** ; détection par croisement route/voie échouée (1/18) car les routes BD TOPO s'arrêtent à ~25 m du PN | `pn_phase1.json` |
| Routes (BD TOPO, 2 630 à ≤ 150 m), ponts-route/passages inférieurs (192 croisements) | **données prêtes, rien posé** (aucun réseau routier dans le jeu) | `routes_150m.json`, `croisements_routes.json` |
| Eau (296 tronçons, 299 surfaces, 44 franchissements) | **données prêtes, rien posé** | `eau.json` |
| Champs (RPG 2024, 574 parcelles) / zones urbaines | **données prêtes, rien peint** | `champs.json` |
| Végétation | 1 109 zones BD TOPO ; **essai Nogent (PK 147,1-150) seulement** : arbres/buissons DLC posés ; **utilisateur : « toujours sur les voies »** (mesure : 12 arbres/554 à < 10 m d'une voie → cause à élucider, voir §3) | `objects_decor.json`, route `view_decor` |
| Maisons/bâtiments (10 775 emprises BD TOPO à ≤ 150 m, 1 172 ferroviaires) | **données prêtes, rien posé** ; **aucune maison française** dans les assets installés | `batiments.json` |
| Bâtiment voyageurs 3D de Nogent (Blender, `Scripts/Blender/gare_nogent.py`) | v1 et v2 faites, **jugées « dégueulasses » par l'utilisateur, mises de côté** ; chaîne Blender → TSC **validée** une fois | `Documentation/TSC/asset_pipeline.md` |

## 3. Problèmes ouverts connus, par priorité
1. **Décalage possible scène ↔ voies en jeu.** L'utilisateur voit des arbres sur les voies alors que les fichiers générés mesurent ≥ 14 m (arbres) / ≥ 9 m (buissons) en théorie (12 arbres à 4-10 m mesurés avant le dernier durcissement). Hypothèses à tester **en premier** : (a) il regarde une ancienne version ; (b) les couronnes de certains modèles (platane `NYNH_Tree_HybridPlane_01`) sont très larges ; (c) décalage de position entre objets de scenery et rubans de voie (conversion tuile/coordonnées lointaines) ; (d) rubans de voie ≠ voies SNCF à cause du lissage/lead-in. **Protocole** : générer une route de test minimale avec des repères posés exactement sur l'axe de V1 tous les 100 m et à ±10 m, demander une capture, mesurer.
2. **Nogent « posé n'importe comment ».** Constat : le faisceau de gare mélange trois sources (SNCF VPA, BD TOPO, OSM) ; quais obliques/décalés ; faisceau jugé trop large et trop long par rapport à Carto Tchoo. Une tentative « OSM seul » dans `extra_tracks.py` (`OSM_ONLY`, désormais `[]`) a été jugée **pire** par l'utilisateur. Cause réelle non identifiée. **À faire avec l'utilisateur** : lister les voies réellement en service (il compare à Carto Tchoo), puis ne poser que celles-là.
3. **Origine des coordonnées non décidée.** `Route/Configuration/coordinate_system.json` annonce l'origine (48,2 ; 1,1) mais `Scripts/Python/tsc_coords.py` utilise par défaut (48,45 ; 1,48) « origine de test » (variable `TSC_ORIGIN`) ; les routes `phase1`/`view_decor` sont générées avec le défaut. Les coordonnées `x,z` de tous les fichiers `Processed/layers/*.json` sont calculées avec ce défaut : **les recalculer depuis `lon`/`lat`**. Décision à acter avec l'utilisateur et dans `TECHNICAL_DECISIONS.md`.
4. **Relief** : `phase1` déployée avec 1 tuile de relief autour des voies ; régénérer avec `TERRAIN_RING=3` et faire valider. Le fond de vallée de l'Huisne est réellement plat (~105 m) ; les coteaux montent de +30 m à 500 m et +40 à +85 m à 1-1,5 km.
5. **Quais** : lofts obliques/décalés en jeu ; vérifier l'axe, l'écart (1,67 m + demi-largeur), la hauteur (+0,55 m), les raccords aux extrémités ; Montfort-le-Gesnois et Saint-Mars-la-Brière n'ont pas de quai OSM exploitable (règle forfaitaire).
6. **Passages à niveau / routes / ouvrages** : aucune route n'est posée ; les PN SNCF (18) sont des points fiables (0-10 m de la voie) ; les routes BD TOPO ne traversent pas les voies aux PN ; 52 croisements restent « inconnu » ; ponts-rail réels connus par BD TOPO (`position_par_rapport_au_sol` = 1, ~51 tronçons) sans tablier modélisé ; assets : barrière/demi-barrière/feu tricolore de `DTG/LGVRhoneAlpes` (`LMR_LC_*`), fillers de croisement `MP_Track_Crossing_Filler*`, BridgeKit `BK_*`.
7. **Eau / champs / sol** : méthode de rendu à définir (creusement du lit dans le terrain, objets/lofts d'eau, peinture du MixMap). Les codes de groupe de culture RPG sont numériques sans libellé ; utiliser les codes de culture à 3 lettres (libellés IGN dans `champs.json`).
8. **Signaux** : vérifier l'enchaînement des aspects, la visibilité côté cabine, les panneaux TIV (modèles DLC `BAL_TIV_*`, `BAL_TIV-R_*` à relier aux types SNCF `TIV D FIXE`, `TIV R MOB`…), crocodiles/KVB (types DLC `Crocodile`, `KVB_Balise01/02` non posés).
9. **Caténaire** : poteaux omis dans les faisceaux (côté libre seulement) ; vérifier le rendu des voies de garage électrifiées/non électrifiées (OSM `electrified`).
10. **Réseau** : 15 raccords impossibles laissés libres (voies < 40 m aux tangentes incompatibles), ~100 croisements de voies au même niveau non raccordés (traversées-jonctions ? à comparer aux orthophotos), voies BD TOPO de service non présentes dans OSM vers PK 199,5-200,3 (515/172/168 m).
11. **Végétation** : essences DLC méditerranéennes/génériques (érable champêtre, peuplier, taillis, platane, frêne, aubépine) ; aucun chêne/hêtre/saule ; conifères semés en feuillus ; zones BD TOPO imparfaites (une « forêt » vue sur orthophoto est en partie une prairie) ; pas d'arbres isolés de jardin.
12. **Maisons** : aucune maison française nommée dans les assets (les « maison » du DLC LGVMedSouth sont des entrepôts de Marseille). Voir §6 (décision utilisateur).
13. **Fiabilité des sources réseau** : Overpass renvoie souvent 429/502/504 ; réessayer avec temporisation, alterner `overpass-api.de` et `maps.mail.ru`.

## 4. Cartographie du dépôt (`E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\`)
- `Scripts/Python/gen_route.py` (~860 lignes) : **générateur principal** : `python Scripts/Python/gen_route.py <pk_debut> <pk_fin> <nom>` (sortie `Route/Exports/<nom>/<GUID>/`, GUID déterministe de `<nom>`). Environnement : `TSC_ORIGIN`, `NO_EXTRA`, `NO_SIGNALS`, `NO_DECOR`, `DECOR_FILE`, `DECOR_MAX_PER_TILE` (2 500), `TERRAIN_RING` (3), `NO_OSM_QUAIS`, `PLT_TEST`, `TRACK_BP`, `ROUTE_BASE`, `DBG_POLES`, `DBG_TRACK`. Modèles XML issus du DLC Marseille-Avignon dans `Tests/Phase1/marseille/` (non versionné, extraits par `extract_templates.py`).
- `Scripts/Python/netbuild.py` (raccordements, aiguillages, courbes de départ), `curvefit.py` (ajustement droites/arcs, `fit_ls`), `extra_tracks.py` (liste des voies hors V1/V2 → `GeographicData/Processed/extra_tracks_phase1.json`), `tsc_coords.py`, `tsc_tiles.py`.
- Contrôles : `validate_network.py <dossier_route_GUID>` (position/cap/hauteur aux nœuds, aiguillages), `validate_route.py`, `plot_network.py` (tracé PNG du réseau).
- Données : `GeographicData/Raw/` (téléchargements, gitignoré), `GeographicData/Processed/layers/*.json` (couches du §2), scripts `fetch_*.py`, `build_*.py`, `veg_phase1.py`, `scatter_vegetation.py` (semis → `Route/Configuration/objects_decor.json`), `batiments_couloir_150m.py`.
- Assets : `Assets/Inventory/blueprints_inventory.json` (8 554 blueprints classés par mots-clés, **heuristique**), `Assets/Custom/PCLM_Gares_Source/` (sources des modèles à l'utilisateur), `Scripts/Blender/`.
- Aperçus et cartes de comparaison : `Tests/Phase1/previews/`.

### Déploiement (à respecter)
1. Fermer le jeu (`Get-Process railworks64` doit être vide). 2. Sauvegarder. 3. Copier `Route\Exports\<nom>\<GUID>\*` vers `D:\Programmes\Steam\steamapps\common\RailWorks\Content\Routes\<GUID>\` (supprimer d'abord seulement Networks, Scenery, Terrain, MixMap de cette destination). 4. Vérifier l'identité des fichiers par SHA-256. 5. L'utilisateur lance le jeu par le bouton JOUER de Steam (jamais `steam.exe -applaunch`, qui fige l'écran de démarrage), puis Construire.
Routes de mon projet déjà dans le jeu : `ee4a17ee-10e2-540d-a40d-750281467cb5` (phase1), `cba59624-4c5a-5583-8cce-e036931840f1` (view_decor, PK 147,1-150), et d'anciens essais `2a1f7969-…`, `8c69da3d-…`, `43b648ef-…`.

### Pièges déjà rencontrés (ne pas les refaire)
- `serz.exe` : `.bin` ↔ XML ; écrire `<X d:type="cDeltaString"></X>` (pas auto-fermé) et retirer `d:alt_encoding`.
- Un terrain/MixMap sans l'en-tête `FF 43 00 <LE32 taille+4>` plante le jeu (0xc0000374).
- Les rubans de voie DLC exigent la `RouteProperties` du DLC (`ROUTE_BASE=dlc`, valeur par défaut) ; les lofts de caténaire exigent 2 nœuds `Network-cLoftNode` par travée.
- PowerShell : ne jamais utiliser `$R` et `$r` comme variables distinctes (insensible à la casse : copie récursive de 193 Go provoquée une fois).
- Les polylignes SNCF/OSM filtrées dans la boîte lon 0,17-0,835 / lat 47,99-48,34 ne commencent pas au PK de la polyligne complète : **PK = distance projetée en L93 sur V1 complète / 1000 + 1,186** (écart médian de −94 m constaté sur 45 PN/ponts : à recaler).
- Les fichiers JSON écrits sous Windows doivent l'être en UTF-8 explicitement ; les accents s'affichent mal dans la console sans être corrompus.
- Overpass : User-Agent `TSC-route-builder/1.0` (sans e-mail).
- Le champ latitude/longitude de l'éditeur TSC ne téléporte pas ; `Lat/Long` y affichent l'origine de la route DLC de base (Marseille), pas Nogent.
- Orientation des signaux : l'axe Z de l'objet pointe dans le sens servi (`_direction` forwards = sens du ruban), signal à gauche du sens de marche (3 m).
- Ne jamais commiter `.mcp.json` ni `Scripts/Python/foundry_mcp.py` (hors projet).

## 5. Plan de travail ordonné (critères d'acceptation entre parenthèses)
**A. Base et protocole (avant de produire quoi que ce soit)**
 A1. Lire la documentation, vérifier la sauvegarde, créer une branche Git de travail. A2. Lister avec l'utilisateur ses réponses aux questions du §6 et les consigner dans `TECHNICAL_DECISIONS.md`. A3. Fixer l'origine des coordonnées et recalculer les `x,z`. A4. **Test d'alignement** (repères sur l'axe de V1/V2 et à ±10 m) pour trancher le problème n°1 du §3 (preuve : capture + mesure).
**B. Voies et gares de Nogent → Le Mans** (comparaison cartes : OSM/Carto Tchoo + orthophotos IGN ; l'utilisateur valide **gare par gare**, en commençant par Nogent) : voies réellement en service, numérotation des voies, quais (position/axe/longueur), raccords et aiguillages de gare, traversées-jonctions, voies de service douteuses.
**C. Équipements de voie** : signaux (vérification des aspects, TIV, KVB/crocodiles), pancartes (seulement celles dont le sens est établi par une source ; glossaire à obtenir), bornes PK, passages à niveau (18, depuis les points SNCF ; matériel DLC), caténaire.
**D. Sol** : relief sur 3 tuiles (régénérer `phase1`), peinture du MixMap (champs/prairies/forêt/urbain à partir de `champs.json`, `zones_urbaines.json`, `vegetation.json`), eau (cours d'eau, plans d'eau, franchissements), talus/déblais.
**E. Routes et ouvrages** : réseau routier autour des voies (≤ 150 m), ponts-route, passages inférieurs, ponts-rail, tunnels éventuels, tabliers (assets BridgeKit) ; décider avec l'utilisateur de la méthode (réseau `Roads` du jeu ou lofts).
**F. Végétation et clôtures** : arbres/haies d'après BD TOPO sur 100 m, écarts aux voies/routes/bâtiments, plafond d'objets par tuile (suivre la fluidité), clôtures/murs.
**G. Bâtiments** : maisons d'après les 10 775 emprises (filtrer : surface minimale, bâtiments ferroviaires à part), hauteurs/étages/toits BD TOPO, avec les assets disponibles (voir §6).
**H. Assets 3D (en TOUT dernier)** : bâtiments voyageurs (Nogent d'abord ; sources d'apparence : photos de façade côté place et côté quai envoyées par l'utilisateur, orthophotos, Street View/Mapillary seulement pour observation), marquises, passerelles/souterrains, postes d'aiguillage, bâtiments emblématiques ; **la chaîne** : Blender 5.2.3 (`D:\Programmes\Blender`) + add-on BRIAGE 4.1 (`bpy.ops.export_scene.igs`, matériaux `IgsMat`), conversion PNG → ACE par RWAceTool (GUI), compilation par Blueprint Editor 2 (F7), pose par `objects.json`/`objects_decor.json`. Les deux premières versions de la gare de Nogent ont été refusées : **valider chaque modèle avec l'utilisateur sur aperçu rendu avant export**, comparer aux photos, éviter les textures procédurales plates (préférer des textures dérivées de photos libres de droits ou d'orthophotos/BD ORTHO après accord de licence).
**I. Validation globale** : régénération complète de `phase1`, `validate_network.py`, audits chiffrés (couverture OSM/BD TOPO), fluidité en jeu (FPS, objets par tuile), scénarios (marqueurs « <gare> Voie n »), mise à jour de `PROJECT_STATUS.md`, `CHANGELOG.md`, `ISSUES.md`.

## 6. Questions à poser à l'utilisateur AVANT d'avancer (ne rien supposer)
Pose-les par blocs, consigne les réponses dans `TECHNICAL_DECISIONS.md`, et ne passe à l'étape suivante qu'après réponse :
1. **Périmètre/fidélité** : quelles voies de Nogent sont réellement en service ? idem pour chaque gare (liste ou capture Carto Tchoo annotée) ; quel niveau de détail attend-il (voie principale + quais seulement ? tout le faisceau ?).
2. **Références de réalité** : accepte-t-il les orthophotos IGN et OSM comme références ? Fournira-t-il des photos/vidéos cabine par gare ? Ordre de priorité des gares ?
3. **Maisons/assets** : volumes génériques simples, assets communautaires (chacun soumis à son accord), ou modélisation Blender tout à la fin ? Quels assets communautaires déjà connus (auteur, licence) ?
4. **3D** : liste des bâtiments à modéliser, niveau de détail, budget de polygones, source des textures (photos personnelles ? libres de droits ?), qui valide, combien d'itérations.
5. **Performance** : FPS minimal sur sa machine, plafond d'objets par tuile, densité de végétation acceptable.
6. **Voies/quais** : numérotation officielle des voies de chaque gare (surtout Le Mans) ; hauteur de quai ; passerelles/souterrains à poser ?
7. **Signalisation** : quels équipements en priorité (TIV, KVB, crocodiles, bornes PK) ; veut-il la signalisation fonctionnelle (aspects) ou seulement visuelle ?
8. **PN et routes** : matériel de PN (barrières demi/complètes, feux) ; routes : toutes ou seulement les principales ; chemins/sentiers ; marquages ; éclairage public.
9. **Eau/sol** : eau animée ou plane ; rivières larges (Huisne, Sarthe) : modèle de rive ; saison/ambiance ; textures de sol.
10. **Ouvrages** : tabliers de pont modélisés ? tunnels ? murs de soutènement ?
11. **Trains/scénarios** : quels engins (DLC possédés), quels services entre Nogent et Le Mans, quelle époque de signalisation/livrée ?
12. **Origine/coordonnées** : valider (48,2 ; 1,1) ou autre origine, et la jonction avec les phases suivantes.
13. **Livrable** : usage privé uniquement ? packaging (zip de route, dépendances DLC listées) ; publication prévue (Workshop ?) → contraintes de licence.
14. **Méthode** : fréquence des points de contrôle ; format des retours (captures + position PK) ; qui sauvegarde ; budget temps/tokens.
15. **Qualité** : par quoi sait-il que « c'est bon » ? (comparaison à Carto Tchoo ? à des photos ? parcours en cabine ?)

## 7. Livrables attendus
- Route `phase1` régénérée, validée par l'utilisateur gare par gare, déployée avec sauvegarde.
- Journal complet dans `history.md`, `PROJECT_STATUS.md`, `RAILWAY_DATA.md`, `ASSET_INVENTORY.md`, `ISSUES.md`, `CHANGELOG.md`, `TECHNICAL_DECISIONS.md` à jour.
- Scripts reproductibles et idempotents, commités par petits lots (jamais de fichiers lourds ou personnels).
- Un rapport final listant : fait/vérifié/non vérifié, écarts à la réalité connus, sources, et la liste des assets externes requis (DLC).
