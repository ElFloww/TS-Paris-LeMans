# PROJECT_STATUS.md

État global (2026-11-07) : phase 0 en cours. Aucune route créée. Méthode d'édition par code non validée.


## Mise à jour 2026-11-07
- Fait : squelette, documents, Git, bibliothèques Python, test d'aller-retour serz.exe.
- À faire : extraire données du tronçon 1 (SNCF, IGN, OSM), système de coordonnées, prototype 2 km.

## Mise à jour fin de session 2026-11-07
- Données officielles SNCF (ligne 420000) téléchargées ; géométrie V1/V2 validée contre les PK ; électrification 1 500 V confirmée sur tout l'axe.
- Système de coordonnées fixé (TM locale, tuiles 1024 m). Format de route analysé (`Documentation/TSC/route_format.md`).
- Bloquants / risques : profil en long (MNT ≠ voie), Overpass inaccessible, génération de `Tracks.bin` + chargement en jeu non testés.
- Prochaine étape : générateur de prototype (ajustement polyligne → droites/arcs/clothoïdes, rubans + hauteurs), route de test dans `Content\Routes\{GUID}`, chargement dans le jeu.
- 2026-11-07 : première route générée par code (`proto1`, 2 km, PK 150-152) chargée dans l'éditeur de TSC sans plantage ; relief IGN et voie visibles. Reste à tester : conduite, raccords, orientation, textures.

## Mise à jour 2026-11-07 (soir)
- **Validé en jeu** (utilisateur) : voies V1/V2 de la phase 1 (rails à textures, lissées, même hauteur), fils porteur et de contact, pendules, poteaux simples `Single Pull_L/Push_L` à l'extérieur des deux voies.
- **Générateur** : `Scripts/Python/gen_route.py` (une passe : voies, terrain IGN, MixMap, caténaire, poteaux) ; contrôle `validate_route.py` ; modèles du DLC extraits par `extract_templates.py`.
- Sauvegarde : `Backups/phase1_*.zip`, `Backups/scripts_docs_*.zip` ; commit Git `8d5507e`.
- **À faire** : gares et quais, signaux BAL/TIV/KVB, passages à niveau (117), ponts et tunnels, textures de sol (MixMap), scénarios/services, conduite d'un train de test, phases 2 à 4 (en cours de génération).
