# Chaîne de fabrication des assets personnalisés (Blender → TSC)

État au 2026-11-07. **Tout est vérifié sauf la dernière étape (compilation Blueprint Editor).**

1. **Modélisation dans Blender 5.2.3** (instance pilotée par le serveur MCP).
2. **Export IGS** par l'add-on **BRIAGE 4.1** (MIT, J. Merle-Rémond, déjà installé : `bpy.ops.export_scene.igs`) — vérifié : un cube texturé exporte un `.igs` binaire (`KIGF`, 9 Ko).
   - Matériau : propriété `material.IgsMat` (`shader_name` ex. `TexDiff`, `TrainBasicObjectDiffuse.fx`…) et `IgsMat.textures[i].texture = <image>` ; pas via les nœuds Principled.
   - Le chemin d'export et les textures doivent être **sur le même disque** (erreur « same drive ») : exporter dans `Assets/Custom/<asset>/` avec `target_textures_directory` = chemin absolu.
   - Les objets sont renommés `1_1000_<nom>` (règle LOD de BRIAGE).
   - Il faut sortir du mode édition (`object.mode_set(OBJECT)`) avant d'exporter.
3. **Compilation (vérifiée le 2026-11-07 avec le Blueprint Editor 2 v72.4a)** — voir « Commandes exactes » plus bas. Ancien constat : **Géométrie PC** : `ConvertToGEO.exe` du jeu ne produit que du `.GeoPs2` (PlayStation) et lit `LegacyShaderMap.xml` + shaders dans le répertoire courant (copie de `dev\Shaders\*`). **Il ne produit pas le `.GeoPcDx` attendu par le jeu.** Le `.GeoPcDx` et les `.TgPcDx` sont générés par le **Blueprint Editor** (`BlueprintEditor2.exe`, interface graphique) à l'export.
4. **Blueprint** : XML `cBlueprintLoader / cSceneryBlueprint` (modèle lu dans le DLC : `Scenery\Buildings\SH_Shed_gen13`), `GeometryID` = `Provider\Product\chemin\[00]Nom`, converti en `.bin` par `serz.exe`.
5. **Pose dans la route** : entité de Scenery (`cDynamicEntity`) avec le `BlueprintID` correspondant, générée par `gen_route.py`.

Documentation officielle (installée avec le jeu) : `RailWorks\dev\Docs\HOWTOUSE_TS14Tech_P1.pdf`, `HOWTOUSE_TS15Tech.pdf`. Plugins 3ds Max dans `dev\MaxPlugins`.

## À faire
- Piloter le Blueprint Editor (Computer Use) pour compiler un asset de test et obtenir `.GeoPcDx` + `.TgPcDx`, ou trouver une compilation en ligne de commande.
- Cadre de licence BRIAGE : MIT. Les modèles créés restent des dépendances externes du dossier `Assets/Custom` (à versionner : fichiers sources Blender/IGS/textures originaux créés par nous).

## Commandes exactes (relevées dans la sortie du Blueprint Editor, export réussi d'un cube texturé)
Arborescence : sources dans `RailWorks\Source\<Provider>\<Product>\...` (IGS, textures `.ace`, blueprint XML source), résultats dans `RailWorks\Assets\<Provider>\<Product>\...`. Provider/produit du projet : `PCLM` / `Gares`.
1. Texture : `ConvertToTg.exe -i <Source>\...\X.ace -o <Assets>\...\X.TgPcDx -target pc -nowindow -costXML <...>\X.TgPcDx.cost -r <RailWorks>\Source -interpalpha -forcecompress` (à lancer avec `Start-Process -Wait` depuis `RailWorks`, sinon rien n'est écrit ; accepte l'ACE, plante sur un TGA).
2. Géométrie : `ConvertToGeo.exe <Source>\...\X.igs <Assets>\...\X.GeoPcDx -pc -lf -nowindow -shaderpath <RailWorks>\Dev\Shaders -costXML <...>\X.GeoPcDx.cost`.
3. Blueprint : le Blueprint Editor écrit `X.xml` compilé puis `serz.exe X.xml` → `X.bin`.
4. **PNG → ACE** : seul RWAceTool (interface graphique : « Single/Multiple image conversion », génère les mips, compresse) a été utilisé ; sortie `SIMISA@F` + zlib (en-tête SimisACE v2, 152 octets). Un écrivain ACE en Python reste à faire pour éviter l'interface.
5. Création du blueprint : dans l'explorateur, clic droit sur le `.igs` → « Create scenery blueprint » ; `Ctrl+S` ; clic droit sur le `.xml` → Export → « Export With References » (F7). Il faut d'abord créer `RailWorks\Source` (absent d'une installation Steam neuve : « Invalid source path! »).

## Pose dans la route
`Route/Configuration/objects.json` : liste d'objets `{name, blueprint:[provider, product, id], pk, lateral (gauche > 0 par rapport à V1), heading_deg, dz}` ; `gen_route.py` les écrit comme entités de Scenery (modèle `obj_template.xml` extrait du DLC) et ajoute `Provider/Product` au préchargement.
