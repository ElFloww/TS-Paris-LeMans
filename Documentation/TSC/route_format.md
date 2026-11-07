# Format d'une route TSC (observations, 2026-11-07, sur copie de la route TestTraK)

Source : copie de `Content\Routes\00000008-...\MainContent.ap` dans `Tests/Phase1/serz_test/` (jeu non modifié).

- `MainContent.ap` = archive zip. Contenu : `RouteProperties.xml` (+ `*.lan`), `RouteInformation/`, `MixMap/`, `Networks/`, `Scenery/`, `Terrain/`.
- Tuiles nommées `±XXXXXX±YYYYYY.bin` (indices entiers, tuile = 1024 m supposée).
- `serz.exe infile /xml:out` et `/bin:out` : aller-retour validé sur une tuile de voies (XML identique).
- `Networks/Track Tiles/*.bin` : par tuile, une liste de courbes (`cCurveStraight`, `cCurveArc` avec `Curvature` et `CurveSign`, `cCurveEasement`). Chaque courbe : `Length`, `StartPos` (`cFarVector2` X/Z = `RouteCoordinate` entier (tuile) + `TileCoordinate` flottant, ex. 977.185), `StartTangent` (vecteur 2D). Géométrie en plan uniquement.
- `Networks/Tracks.bin` (2,5 Mo en XML pour TestTraK) : `Network-cTrackNetwork` avec rubans (`Network-cTrackRibbon`) : `_length`, `RibbonID` (GUID), **`Height`** = liste de `Network-iRibbon-cHeight` (`_position` le long du ruban, `_height` en m, `_manual`), `RouteVector`, `RBottomLeft`/`RExtents`, propriétés ; nœuds avec connexions (`Network-cNetworkNode-sRConnection`), `BlueprintID` des types de voie.
- `Terrain/*.bin` : tous de taille identique (65 689 octets) sur TestTraK (terrain plat par défaut).
- `Scenery/*.bin` : objets placés par tuile.
- Le profil en long est donc porté par les hauteurs des rubans (pas par les tuiles de courbes).

## Non validé
- Axes (X est / Z nord), origine exacte des tuiles, unité de tuile.
- Que le jeu charge une route produite par un générateur.
- Format de `Scenery`, `Terrain` (hauteurs), `MixMap`, `Lofts`, `Roads` pour une route générée.

## Validé le 2026-11-07 (données réelles TestTraK)
- Tuile 1024 m, coordonnée de tuile depuis le coin, positions absolues = indice×1024 + valeur.
- `CurveSign = -1` ⇒ cap atan2(Z,X) croissant. Courbure = 1/rayon.
- GUID : `a = int.from_bytes(uuid.bytes_le[:8],'little')`, `b = int.from_bytes(uuid.bytes_le[8:],'little')`.
- Terrain : `cHeightFieldTile` `X`,`Y` + blob 65 536 octets = 128×128 float32 (hexadécimal en XML).
- Ruban : propriétés par tronçon `_start`/`_end` : électrification (`Network-cTrackNetworkElectrification`, `OverheadWires`), blueprint de voie + blueprint de caténaire (`Network-cSectionGenericProperties`), limite de vitesse (`Network-cTrackNetworkSpeedLimit` Primary/Secondary).
