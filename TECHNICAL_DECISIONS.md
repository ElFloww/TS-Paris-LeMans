# TECHNICAL_DECISIONS.md

## 2026-11-07
- Installation de référence : Steam officielle, D:\Programmes\Steam\steamapps\common\RailWorks.
- Hiérarchie des sources : officielles > OSM > contrôle visuel.
- Système de coordonnées / origine unique : à décider (phase 0.5).

- Routes TSC : archive `MainContent.ap` (zip) dans `Content\Routes\{GUID}`. Édition envisagée par `serz.exe` .bin ↔ XML. Aller-retour validé sur une tuile de voies (2026-11-07). Chargement dans le jeu : à valider.
- Système de coordonnées (2026-11-07) : projection transverse de Mercator locale centrée (48.2°N, 1.1°E), k0=1, GRS80, tuiles de 1024 m ; module `Scripts/Python/tsc_coords.py`, config `Route/Configuration/coordinate_system.json`. Étendue de la ligne : X −69 à +89 km, Z −23 à +71 km (268 tuiles traversées par V1). Longueur V1 projetée 213,38 km. Axes et convention de tuile à valider en jeu.
- Géométrie de référence : polylignes officielles SNCF V1/V2 (ligne 420000) ; profil en long : MNT IGN filtré, contrôlé par déclivités SNCF.
- Binaires générés : les `.bin` Terrain et MixMap doivent porter l'en-tête `FF 43 00 <LE32 taille du blob + 4>` après `SERZ` (serz ne l'écrit pas ; sans lui le jeu plante, c0000374). Géré par `gen_prototype.py`. Lancer le jeu via le bouton JOUER de Steam, pas `steam.exe -applaunch` (blocage au démarrage).
