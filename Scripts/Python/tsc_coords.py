"""Systeme de coordonnees unique du projet (decision TECHNICAL_DECISIONS.md, 2026-11-07).
Projection locale transverse de Mercator centree sur la ligne (k0=1, ellipsoide GRS80) : distances ~exactes.
TSC : X vers l'est, Z vers le nord (hypothese a valider en jeu), tuiles de 1024 m, coordonnee de tuile mesuree depuis le coin [0,1024[.
"""
import math
from pyproj import Transformer
import os
LAT0, LON0 = (float(v) for v in os.environ.get('TSC_ORIGIN', '48.45,1.48').split(','))  # TSC_ORIGIN : origine de test (vue editeur), jamais pour la vraie route
TILE = 1024.0
_to = Transformer.from_crs(4326, f"+proj=tmerc +lat_0={LAT0} +lon_0={LON0} +k=1 +x_0=0 +y_0=0 +ellps=GRS80 +units=m", always_xy=True)

def lonlat_to_xz(lon, lat):
    return _to.transform(lon, lat)

def xz_to_lonlat(x, z):
    return _to.transform(x, z, direction="INVERSE")

def split_tile(v):
    """metres -> (indice de tuile entier, position 0..1024 dans la tuile)"""
    t = math.floor(v / TILE)
    return t, v - t * TILE

def tile_name(tx, tz):
    return f"{tx:+07d}{tz:+07d}"
