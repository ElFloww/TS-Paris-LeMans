"""Extrait de la route Marseille-Avignon (DLC, copie locale non versionnee) les modeles XML de la caténaire.
Sortie : Tests/Phase1/marseille/loft_cat.xml, loft_wire.xml, loft_container.xml (ne jamais versionner ni redistribuer)."""
import os, zipfile, subprocess, copy
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
R = r"D:\Programmes\Steam\steamapps\common\RailWorks\Content\Routes\00000065-0000-0000-0000-000000002016\MainContent.ap"
SERZ = r"D:\Programmes\Steam\steamapps\common\RailWorks\serz.exe"
OUT = os.path.join(ROOT, "Tests", "Phase1", "marseille"); os.makedirs(OUT, exist_ok=True)

def main():
    z = zipfile.ZipFile(R)
    # tuile de loft riche en travees de caténaire (la 000000+000000 en contient 860)
    b = os.path.join(OUT, "p000000p000000.bin"); x = b[:-4] + ".xml"
    if not os.path.exists(x):
        open(b, "wb").write(z.read("Networks/Loft Tiles/+000000+000000.bin"))
        subprocess.run([SERZ, b, "/xml:" + x], capture_output=True)
    root = etree.parse(x).getroot()
    cont = root.find(".//{*}Network-cRibbonContainerStreamed"); ribs = cont.find("{*}Ribbon")
    found = {}
    for r in ribs:
        c = r.find(".//{*}cCurveCatenary")
        if c is None or len(list(r.iter("{*}Network-iRibbon-cHeight"))) != 2: continue
        t = c.find("{*}CurveType").text
        if t not in found: found[t] = r
        if len(found) == 2: break
    for t, name in (("eCatenary", "loft_cat.xml"), ("eWire", "loft_wire.xml")):
        etree.ElementTree(found[t]).write(os.path.join(OUT, name), encoding="utf-8")
    sk = copy.deepcopy(root); c2 = sk.find(".//{*}Network-cRibbonContainerStreamed")
    for ch in list(c2.find("{*}Ribbon")): c2.find("{*}Ribbon").remove(ch)
    for ch in list(c2.find("{*}Node")): c2.find("{*}Node").remove(ch)
    for ch in list(c2.find("{*}Connection")): c2.find("{*}Connection").remove(ch)
    etree.ElementTree(sk).write(os.path.join(OUT, "loft_container.xml"), encoding="utf-8", xml_declaration=True)
    cat = {r.find("{*}RibbonID/{*}cGUID/{*}DevString").text for r in ribs if r.find(".//{*}cCurveCatenary") is not None}
    for n in cont.find("{*}Node"):   # noeud d'extremite (1 connexion) d'une travee de cat?naire
        if n.find(".//{*}Network-cNetworkNode-sRConnection/{*}_id/{*}cGUID/{*}DevString").text in cat:
            etree.ElementTree(n).write(os.path.join(OUT, "loft_node.xml"), encoding="utf-8"); break
    # poteaux 1 500 V (entites de Scenery) : modeles Pull_L / Push_L et squelette de tuile
    sb = os.path.join(OUT, "sc0.bin"); sx = sb[:-4] + ".xml"
    if not os.path.exists(sx):
        open(sb, "wb").write(z.read("Scenery/+000000+000000.bin")); subprocess.run([SERZ, sb, "/xml:" + sx], capture_output=True)
    sroot = etree.parse(sx).getroot(); rec = sroot[0]; want = {"Pull": "LGV Gantry HPost 1500 Med Pull.xml", "Push": "LGV Gantry HPost 1500 Med Push.xml", "1Pull": "LGV Gantry HPost 1500 Single Pull_L.xml", "1Push": "LGV Gantry HPost 1500 Single Push_L.xml"}
    for ent in rec:
        b_ = ent.find(".//{*}BlueprintID/{*}iBlueprintLibrary-cAbsoluteBlueprintID/{*}BlueprintID"); nm = (b_.text or "") if b_ is not None else ""
        for k_, w_ in list(want.items()):
            if nm.endswith(w_): etree.ElementTree(ent).write(os.path.join(OUT, ("pole_%s.xml" % k_) if k_ in ("Pull", "Push") else ("pole1_%s.xml" % k_[1:])), encoding="utf-8"); del want[k_]
    for ent in rec:
        b_ = ent.find(".//{*}BlueprintID/{*}iBlueprintLibrary-cAbsoluteBlueprintID/{*}BlueprintID")
        if b_ is not None and (b_.text or "").endswith("Scenery\\Buildings\\SH_Shed_gen13.xml"):
            etree.ElementTree(ent).write(os.path.join(OUT, "obj_template.xml"), encoding="utf-8"); break
    for ch in list(rec): rec.remove(ch)
    etree.ElementTree(sroot).write(os.path.join(OUT, "scenery_container.xml"), encoding="utf-8", xml_declaration=True)
    print("modeles ecrits dans", OUT, sorted(found), "poteaux manquants:", list(want))

if __name__ == "__main__":
    main()
