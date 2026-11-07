# ROADMAP.md — Méthode de travail détaillée

Principe : une couche à la fois, chaque couche validée (chargée dans le jeu, comparée à la réalité) avant la suivante. Toute action est consignée dans `history.md`. Les hypothèses techniques sont marquées **[à valider]**.

## Phase 0 — Fondations (avant tout travail sur la route)
0.1 Squelette de dossiers, 7 documents de suivi, `.gitignore`, dépôt Git.
0.2 Bibliothèques Python : pyproj, shapely, rasterio, lxml. Vérification des imports.
0.3 Inventaire de l'install : routes, fournisseurs d'assets, DLC (croisé avec Steam), versions. Lecture seule.
0.4 Test de conversion `serz.exe` : un fichier d'une route de test, .bin → XML → .bin, comparaison. **[à valider]**
0.5 Système de coordonnées : origine unique de toute la ligne, projection (Lambert-93 → mètres TSC), orientation, limites de route. Figé dans `TECHNICAL_DECISIONS.md`.
0.6 Prototype de 2 km (voir Phase P) avant de s'engager sur les 200 km.

## Phase P — Prototype de 2 km (go/no-go de la méthode)
Une route de test vide, un tronçon de voie unique généré en XML, relief plat puis réel, une tuile de scenery. Critères de réussite : la route s'ouvre, le tracé est au bon endroit, un train circule dessus. Si échec : changement de méthode (éditeur + Computer Use) et mise à jour du plan.

## Pipeline par tronçon (répété pour chaque phase 1 → 4)
Chaque tronçon suit ces couches, dans cet ordre :

**A. Données** — Extraction OSM (voies, ponts, tunnels, PN, signaux, gares, quais), SNCF open data (lignes, PK, vitesses), IGN RGE ALTI et BD TOPO. Nettoyage, contrôle croisé sur photos aériennes. Sortie : fichiers dans `GeographicData/Processed/`, sources dans `RAILWAY_DATA.md`.

**B. Terrain** — Grille d'altitudes à partir du RGE ALTI, découpée en tuiles TSC, écrite dans `Terrain`. Contrôle : écart d'altitude voie / terrain, comparaison à la carte.

**C. Eau** — Rivières, étangs, canaux depuis BD TOPO / OSM : creusement du lit dans le terrain, placement de l'eau. Ponts et viaducs raccordés aux rivières. **[à valider : méthode d'eau de TSC]**

**D. Voies** — Géométrie (courbes, dévers si disponible), profil en long (pentes et rampes), aiguillages, voies de service et de garage. Le tracé suit les données, pas l'estimation visuelle.

**E. Électrification** — Confirmée officiellement (SNCF Open Data, ligne 420000) : 1 500 V continu sur tout l'axe (PK 0+430 à 213+203). Caténaire 1 500 V sur toute la route ; assets à choisir (DLC français ou création).

**F. Ouvrages d'art** — Ponts, viaducs, tunnels, murs de soutènement, passages inférieurs. Asset existant adapté, sinon création dans Blender.

**G. Passages à niveau** — Position exacte, type (SAL 2, SAL 4, etc.), route qui croise, barrières et feux.

**H. Textures et sol** — Ballast, textures de terrain selon l'occupation du sol (champs, forêt, ville) depuis BD TOPO / Corine Land Cover. Vérification par captures dans le jeu.

**I. Gares** — Chaque gare étudiée (voies, quais, bâtiments, passerelles, abris, équipements). Niveau 1 : assets existants ; niveau 2 : adaptation et modèles Blender ; niveau 3 (Montparnasse, Versailles-Chantiers, Chartres, Le Mans) : modélisation spécifique. Export Blender → TSC **[exporteur à identifier]**.

**J. Signalisation** — Signaux français (carrés, feux, KVB, repères de pk) placés d'après OSM et vérifiés sur photos / cab-rides. Liaison aux voies **[à valider]**.

**K. Décor** — Villages, zones industrielles, bâtiments caractéristiques, végétation, clôtures, poteaux, selon les emprises réelles.

**L. Tests** — Chargement dans le jeu, conduite du tronçon, contrôle de la géométrie, du raccord avec le tronçon précédent et de la stabilité. Problèmes consignés dans `ISSUES.md`.

**M. Services** — Scénarios et services de train, une fois le tronçon stable.

## Ordre des tronçons
1. Nogent-le-Rotrou ↔ Le Mans
2. Nogent-le-Rotrou ↔ Chartres
3. Chartres ↔ Versailles-Chantiers
4. Versailles-Chantiers ↔ Paris-Montparnasse

Règle : on ne passe pas à la suite si la couche en cours a un problème majeur. À chaque jonction entre tronçons, les coordonnées, les altitudes et les voies doivent se raccorder sans décalage.

## Assets
Inventaire dans `ASSET_INVENTORY.md`. Assets commerciaux : dépendances uniquement. Assets communautaires : téléchargés seulement avec licence claire et accord de l'utilisateur. Assets manquants : créés dans Blender.

## Avancement (2026-11-07)
Couches faites pour la phase 1 : A données, B terrain (relief IGN, texture provisoire), D voies, E électrification et caténaire (fils, pendules, poteaux). À faire : C eau, F ouvrages, G passages à niveau, H textures, I gares, J signalisation, K décor, L conduite, M services.

## Règle de phase
Chaque phase A↔B est construite avec 1 km de marge au-delà de A et de B. Phase 1 : PK 147,1 → 212,0 (Nogent-le-Rotrou PK 148,113 ; Le Mans PK 210,980). Ne pas générer les phases suivantes avant validation de la phase en cours.
