# RAILWAY_DATA.md

Chaque donnée indique sa source (voir hiérarchie des sources dans CLAUDE.md). Valeur inconnue = « inconnu » ou « à vérifier ».


## Ligne unique 420000 (SNCF Open Data, data.sncf.com, téléchargé 2026-11-07)
- Paris-Montparnasse à Brest ; l'axe du projet va du PK 0+430 au PK 210+980 (Le Mans).
- Gares (PK) : Paris-Montparnasse-Pasteur 0+600 · Versailles-Chantiers 16+562 · Rambouillet 47+810 · Chartres 87+137 · Nogent-le-Rotrou 148+113 · Le Mans 210+980 · Le Mans Hôpital Université 213+700.
- Électrification : 1 500 V continu PK 0+430 → 213+203 (puis 25 kV alternatif).
- Cantonnement : block automatique lumineux (BAL). KVB : 0+430 → 323+550.
- Vitesses max : voir `GeographicData/Raw/sncf/vitesse-maximale-nominale-sur-ligne_420000.json` (48 tronçons).
- Pentes/rampes : `caracteristique-des-voies-et-declivite_420000.json` (303 enregistrements).
- Voies : `fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json`.
- Passages à niveau : 117 ; ponts-route : 279 ; circuits de voie : 3060 (à analyser).

## Voies supplémentaires phase 1 (2026-11-07)
- SNCF open data ichier-de-formes-des-voies-du-reseau-ferre-national (ligne 420000) : V1, V2 et voies VPA (niveau 1).
- IGN BD TOPO V3 	roncon_de_voie_ferree via WFS data.geopf.fr (niveau 1) : voies de service, raccordements.
- OpenStreetMap via Overpass (niveau 2), uniquement pour les voies absentes des sources officielles ; à recouper avec photos aériennes (écarts à noter dans ISSUES.md).
