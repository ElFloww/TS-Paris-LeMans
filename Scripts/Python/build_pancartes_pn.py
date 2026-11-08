"""Pancartes (signalisation permanente hors feux), repères kilométriques (PK) et passages à niveau, phase 1 (PK 147-212, ligne 420000).

Entrées (déjà dans le projet) :
  GeographicData/Raw/sncf/signalisation-permanente_420000.json   (SNCF Open Data, signalisation-permanente)
  GeographicData/Raw/sncf/liste-des-passages-a-niveau_420000.json (SNCF Open Data)
  GeographicData/Raw/sncf/pk_420000.csv.zip                       (nicolaswurtz/extras-opendata-sncf-reseau, pks.csv.zip : PK reconstitués/extrapolés, non officiels)
Sorties :
  GeographicData/Processed/layers/pancartes.json, pancartes_resume.txt, pn_phase1.json
Le glossaire des types est récupéré via l'API GitHub du dépôt nicolaswurtz/signalisation-rfn-svg (liste des symboles SVG).
Aucune description n'est inventée : 'inconnu' si le dépôt n'en fournit pas.
"""
import sys, json, re, csv, io, zipfile, time, collections, urllib.request
from pathlib import Path

ROOT = Path(r'E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans')
sys.path.insert(0, str(ROOT / 'Scripts' / 'Python'))
import tsc_coords as C

RAW = ROOT / 'GeographicData' / 'Raw' / 'sncf'
OUT = ROOT / 'GeographicData' / 'Processed' / 'layers'
OUT.mkdir(parents=True, exist_ok=True)
PK_MIN, PK_MAX = 147.0, 212.0
EXCLUDE_TYPES = {'CARRE', 'S', 'CV'}  # déjà posés comme signaux
UA = {'User-Agent': 'TSC-route-builder/1.0'}


def pk_km(s):
    """'148+113' -> 148.113 ; None si format inconnu."""
    m = re.fullmatch(r'\s*(\d+)\+(\d{1,3})\s*', s or '')
    return int(m.group(1)) + int(m.group(2)) / 1000.0 if m else None


def github_svg_names():
    """Noms des symboles SVG du dépôt (API GitHub). Liste vide si indisponible."""
    try:
        req = urllib.request.Request('https://api.github.com/repos/nicolaswurtz/signalisation-rfn-svg/contents/svg',
                                     headers={**UA, 'Accept': 'application/vnd.github+json'})
        items = json.loads(urllib.request.urlopen(req, timeout=30).read())
        time.sleep(0.2)
        return {i['name'][:-4] for i in items if i['name'].endswith('.svg')}
    except Exception as e:
        print('API GitHub indisponible :', e)
        return set()


def xz(lon, lat):
    x, z = C.lonlat_to_xz(lon, lat)
    return round(x, 3), round(z, 3)


# ---------- 1. Pancartes ----------
sig = json.loads((RAW / 'signalisation-permanente_420000.json').read_text(encoding='utf-8'))
svg_names = github_svg_names()
pancartes = []
for o in sig:
    km = pk_km(o.get('pk'))
    if km is None or not (PK_MIN <= km <= PK_MAX):
        continue
    if o.get('type_if') in EXCLUDE_TYPES:
        continue
    lon, lat = o.get('x_wgs84'), o.get('y_wgs84')
    x, z = xz(lon, lat)
    pancartes.append({
        'type_if': o.get('type_if'),
        'description': 'inconnu',
        'sens': o.get('sens'),
        'position': o.get('position'),
        'angle': o.get('angle'),
        'pk': o.get('pk'),
        'voie': o.get('code_voie'),
        'lon': lon, 'lat': lat, 'x': x, 'z': z,
        'idreseau': o.get('idreseau'),
    })
pancartes.sort(key=lambda p: pk_km(p['pk']))

# Glossaire : le dépôt ne fournit que des symboles graphiques (noms de fichiers), pas de description.
type_counts = collections.Counter(p['type_if'] for p in pancartes)
glossary = {t: {'description': 'inconnu', 'symbole_svg_dans_depot': t in svg_names} for t in type_counts}

(OUT / 'pancartes.json').write_text(json.dumps(pancartes, ensure_ascii=False, indent=1), encoding='utf-8')

# ---------- 2. Repères kilométriques (PK) ----------
pk_count = 0
pk_fields = None
pk_km_min = pk_km_max = None
with zipfile.ZipFile(RAW / 'pk_420000.csv.zip') as z:
    with z.open('pks.csv') as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
        pk_fields = reader.fieldnames
        for r in reader:
            if r['code_ligne'] != '420000':
                continue
            try:
                km = float(r['pk'])
            except ValueError:
                continue
            if PK_MIN <= km <= PK_MAX:
                pk_count += 1
                pk_km_min = km if pk_km_min is None else min(pk_km_min, km)
                pk_km_max = km if pk_km_max is None else max(pk_km_max, km)

# ---------- 3. Passages à niveau ----------
pn_raw = json.loads((RAW / 'liste-des-passages-a-niveau_420000.json').read_text(encoding='utf-8'))
pn = []
for o in pn_raw:
    km = pk_km(o.get('pk'))
    if km is None or not (PK_MIN <= km <= PK_MAX):
        continue
    lon, lat = o['x_wgs84'], o['y_wgs84']
    x, z = xz(lon, lat)
    pn.append({
        'id': o.get('id_if'),
        'nom': o.get('libelle'),
        'type': o.get('mnemo'),          # le fichier ne contient pas de code SAL2/SAL4/SA : 'mnemo' (CLASSE xx) retenu
        'obstacle': o.get('obstacle'),   # VC (voie communale), CD xx-y (route départementale), CP, Autre
        'commune': o.get('saco_libelle_commune'),
        'pk': o.get('pk'),
        'lon': lon, 'lat': lat, 'x': x, 'z': z,
    })
pn.sort(key=lambda p: pk_km(p['pk']))
(OUT / 'pn_phase1.json').write_text(json.dumps(pn, ensure_ascii=False, indent=1), encoding='utf-8')
pn_types = collections.Counter(p['type'] for p in pn)
pn_obst = collections.Counter(p['obstacle'] for p in pn)

# ---------- 4. Résumé ----------
lines = [
    'Pancartes phase 1 (PK 147-212, ligne 420000) - source : SNCF Open Data signalisation-permanente (GAIA TYPE_IF)',
    f'Pancartes retenues : {len(pancartes)} (exclus CARRE, S, CV ; sens B : {sum(1 for p in pancartes if p["sens"] == "B")})',
    'Type_if | nombre | description | symbole SVG dans nicolaswurtz/signalisation-rfn-svg',
]
for t, n in type_counts.most_common():
    g = glossary[t]
    lines.append(f"{t} | {n} | {g['description']} | {'oui' if g['symbole_svg_dans_depot'] else 'non'}")
lines += [
    '',
    'Glossaire : nicolaswurtz/signalisation-rfn-svg ne contient que des symboles SVG et le nom TYPE_IF (README) ; aucune',
    'description textuelle trouvee (SVG verifies sans balise title/text). Descriptions = inconnu. A completer par une source officielle.',
    '',
    'Repères kilométriques : nicolaswurtz/extras-opendata-sncf-reseau pks.csv.zip (PK reconstitués et extrapolés par un tiers,',
    f'non officiels). Colonnes : {", ".join(pk_fields)}. Points ligne 420000 dans PK 147-212 : {pk_count}'
    f' (PK {pk_km_min} a {pk_km_max}).',
    '',
    f'Passages à niveau phase 1 : {len(pn)} (source SNCF Open Data liste-des-passages-a-niveau)',
    'Type (mnemo) : ' + ', '.join(f'{k} {v}' for k, v in pn_types.most_common()),
    'Obstacle : ' + ', '.join(f'{k} {v}' for k, v in pn_obst.most_common()),
]
(OUT / 'pancartes_resume.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

print('\n'.join(lines))
print('svg names fetched:', len(svg_names))
