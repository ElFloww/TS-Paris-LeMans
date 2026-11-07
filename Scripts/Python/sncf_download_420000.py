import requests,json,os,time
H={'User-Agent':'TSC-line-project/0.1'}
base='https://data.sncf.com/api/explore/v2.1/catalog/datasets'
out=r'E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\GeographicData\Raw\sncf'
os.makedirs(out,exist_ok=True)
DS=['liste-des-gares','fichier-de-formes-des-voies-du-reseau-ferre-national','formes-des-lignes-du-rfn','liste-des-lignes-electrifiees','caracteristique-des-voies-et-declivite','vitesse-maximale-nominale-sur-ligne','liste-des-passages-a-niveau','lignes-equipees-de-kvb','mode-de-cantonnement-des-lignes','liste-des-ponts-route','liste-des-traversees-de-voie-par-le-public','particularite-dexploitation-des-voies','liste-des-circuits-de-voie','liste-ouvrages-en-terre','regime-dexploitation-des-lignes','classification-darmement-des-voies']
def fetch(ds,where):
    rows=[];off=0
    while True:
        r=requests.get(f'{base}/{ds}/records',params={'limit':100,'offset':off,'where':where},headers=H,timeout=180)
        if r.status_code!=200: return None,r.text[:150]
        res=r.json().get('results',[]); rows+=res; off+=100
        if len(res)<100 or off>=10000: break
    return rows,None
for ds in DS:
    for where in ('code_ligne="420000"','ligne_code="420000"','code_ligne=420000'):
        rows,err=fetch(ds,where)
        if rows is not None: break
    if rows is None: print(ds,'ECHEC',err); continue
    json.dump(rows,open(f'{out}\\{ds}_420000.json','w',encoding='utf-8'),ensure_ascii=False)
    print(ds,len(rows),'enregistrements')
