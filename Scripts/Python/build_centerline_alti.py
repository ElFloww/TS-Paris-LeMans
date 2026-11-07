import json,csv,time,requests,os
import numpy as np
from shapely.geometry import shape,Point
from shapely.ops import transform
from pyproj import Transformer
B=r'E:\mods\Ligne Paris-Chartres-Nogent-le-Rotrou-Le-Mans\GeographicData'
t=Transformer.from_crs(4326,2154,always_xy=True); ti=Transformer.from_crs(2154,4326,always_xy=True)
V=json.load(open(B+r'\Raw\sncf\fichier-de-formes-des-voies-du-reseau-ferre-national_420000.json',encoding='utf-8'))
def pk(s): a,b=s.split('+'); return int(a)+int(b)/1000
os.makedirs(B+r'\Processed',exist_ok=True)
STEP=20.0; END_PK=214.5
out={}
for code in ('420000-1-V1','420000-1-V2'):
    v=[x for x in V if x['code_voie']==code][0]; g=transform(t.transform,shape(v['geo_shape']['geometry'])); pk0=pk(v['pk_debut_r'])
    n=int((END_PK-pk0)*1000/STEP)+1
    ds=np.arange(n)*STEP; pts=[g.interpolate(d) for d in ds]
    xs=np.array([p.x for p in pts]); ys=np.array([p.y for p in pts]); lon,lat=ti.transform(xs,ys)
    out[code]=(pk0,ds,xs,ys,lon,lat)
    print(code,n,'points')
H={'User-Agent':'TSC-line-project/0.1'}
u='https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json'
def alti(lon,lat):
    z=[]
    for i in range(0,len(lon),150):
        a=lon[i:i+150]; b=lat[i:i+150]
        for k in range(4):
            try:
                r=requests.get(u,params={'lon':'|'.join(f'{x:.6f}' for x in a),'lat':'|'.join(f'{x:.6f}' for x in b),'resource':'ign_rge_alti_wld','delimiter':'|','zonly':'true'},headers=H,timeout=90)
                r.raise_for_status(); z+=r.json()['elevations']; break
            except Exception as e:
                if k==3: raise
                time.sleep(3)
    return z
for code,(pk0,ds,xs,ys,lon,lat) in out.items():
    z=alti(lon,lat)
    f=B+rf'\Processed\{code}_20m_alti.csv'
    with open(f,'w',newline='') as fh:
        w=csv.writer(fh); w.writerow(['chainage_m','pk_approx_km','x_l93','y_l93','lon','lat','z_ign_m'])
        for i in range(len(ds)): w.writerow([round(ds[i],1),round(pk0+ds[i]/1000,3),round(xs[i],2),round(ys[i],2),round(lon[i],7),round(lat[i],7),z[i]])
    print(code,'->',f,'z min/max',min(z),max(z))
