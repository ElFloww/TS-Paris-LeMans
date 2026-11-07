"""Lecture des tuiles de voies TSC (XML issu de serz) -> courbes en coordonnees absolues (m). Sert a valider les conventions."""
import math
from lxml import etree
TILE=1024.0
def _q(e): return etree.QName(e).localname
def far(e):
    """cFarCoordinate -> metres absolus"""
    rc=int(e.find('.//{*}RouteCoordinate//{*}Distance').text); tc=float(e.find('.//{*}TileCoordinate//{*}Distance').text)
    return rc*TILE+tc
def read_tile(path):
    root=etree.parse(path).getroot(); out=[]
    for rec in root.iter('{*}Network-cNetworkRibbon-cCurveContainer-cID'): pass
    for cont in root.iter('{*}Network-cNetworkRibbonUnstreamed-cCurveContainerUnstreamed'):
        rid=cont.find('.//{*}RibbonID//{*}DevString').text
        curves=[]
        for c in cont.find('{*}Curve'):
            k=_q(c); L=float(c.find('{*}Length').text)
            x=far(c.find('{*}StartPos/{*}cFarVector2/{*}X')); z=far(c.find('{*}StartPos/{*}cFarVector2/{*}Z'))
            tx,tz=map(float,c.find('{*}StartTangent').text.split())
            d={'type':k,'len':L,'x':x,'z':z,'tx':tx,'tz':tz}
            if k=='cCurveArc': d['curv']=float(c.find('{*}Curvature').text); d['sign']=float(c.find('{*}CurveSign').text)
            curves.append(d)
        out.append((rid,curves))
    return out
def advance(c):
    """fin d'une courbe (x,z,tx,tz) d'apres le modele : sign=-1 => angle atan2(z,x) croissant"""
    L=c['len']
    if c['type']=='cCurveStraight': return c['x']+c['tx']*L,c['z']+c['tz']*L,c['tx'],c['tz']
    if c['type']=='cCurveArc':
        k=-c['sign']*c['curv']; th=math.atan2(c['tz'],c['tx']); th2=th+k*L
        # centre
        cx=c['x']-math.sin(th)/k; cz=c['z']+math.cos(th)/k
        return cx+math.sin(th2)/k, cz-math.cos(th2)/k, math.cos(th2), math.sin(th2)
    return None
