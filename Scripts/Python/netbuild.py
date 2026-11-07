"""Construction du reseau : raccordements entre voies (aiguillages, jonctions bout a bout), position exacte sur la voie ajustee,
depart tangent des voies deviees (courbe de Hermite), decoupe des voies meres aux aiguillages. Coordonnees locales TSC (m)."""
import math
import numpy as np
from shapely.geometry import LineString, Point


def pos_on(seg, u):
    th = math.atan2(seg["tz"], seg["tx"]); k = seg["k"]
    if k == 0: return seg["x"] + seg["tx"] * u, seg["z"] + seg["tz"] * u, th
    return seg["x"] + (math.sin(th + k * u) - math.sin(th)) / k, seg["z"] - (math.cos(th + k * u) - math.cos(th)) / k, th + k * u


class Fitted:
    """voie ajustee (segments continus) : position/cap a l'abscisse s, recherche du point le plus proche autour d'une abscisse approchee"""
    def __init__(self, segs):
        self.segs = segs; self.cum = np.r_[0.0, np.cumsum([g["len"] for g in segs])]; self.L = float(self.cum[-1])

    def at(self, s):
        s = min(max(s, 0.0), self.L); j = min(int(np.searchsorted(self.cum, s, side="right")) - 1, len(self.segs) - 1)
        return pos_on(self.segs[j], s - self.cum[j])

    def locate(self, p, s_guess, win=60.0):
        ss = np.arange(max(0.0, s_guess - win), min(self.L, s_guess + win) + 0.5, 0.5)
        P = np.array([self.at(s)[:2] for s in ss]); d = np.hypot(P[:, 0] - p[0], P[:, 1] - p[1]); i = int(np.argmin(d))
        s = float(ss[i]); x, z, th = self.at(s); return s, (x, z), th, float(d[i])


def _tangent(P, i, span=4.0):
    n = len(P); a = max(i - 1, 0); b = min(i + 1, n - 1)
    t = P[b] - P[a]; return t / (np.hypot(*t) or 1.0)


def find_connections(polys, skip_ids, tol=5.0, ang_max=45.0):
    """raccordements des extremites des voies (hors skip_ids) : T sur le milieu d'une autre voie (aiguillage) ou bout a bout (jonction).
    polys : {id: ndarray(n,2)}. Retourne une liste de dict {branch, end, host, kind, p, u, s_raw, host_end}."""
    lines = {k: LineString(P) for k, P in polys.items()}; out = []; seen = set()
    cosmax = math.cos(math.radians(ang_max))
    for code, P in polys.items():
        if code in skip_ids: continue
        for end in (0, 1):
            p = P[0] if end == 0 else P[-1]
            Q = P if end == 0 else P[::-1]; d_ = np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]
            q = np.array([np.interp(min(8.0, 0.4 * d_[-1]), d_, Q[:, 0]), np.interp(min(8.0, 0.4 * d_[-1]), d_, Q[:, 1])])
            u = q - p; u = u / (np.hypot(*u) or 1.0); best = None
            for h, L in lines.items():
                if h == code: continue
                d = L.distance(Point(*p))
                if d > tol: continue
                s = L.project(Point(*p)); a = L.interpolate(max(s - 2, 0)); b = L.interpolate(min(s + 2, L.length))
                t = np.array([b.x - a.x, b.y - a.y]); t = t / (np.hypot(*t) or 1.0); dot = float(u @ t)
                if abs(dot) < cosmax: continue
                he = 0 if s < 1.5 else (1 if L.length - s < 1.5 else None)
                if he is not None:
                    outward = -t if he == 0 else t          # direction de la voie mere au-dela de son extremite
                    if float(u @ outward) < cosmax: continue
                score = d + 0.05 * math.degrees(math.acos(min(1.0, abs(dot))))
                if best is None or score < best[0]: best = (score, h, s, he, d, t, dot)
            if best is None: continue
            _, h, s, he, d, t, dot = best
            if he is not None:
                key = frozenset({(code, end), (h, he)})
                if key in seen: continue
                seen.add(key)
            out.append({"branch": code, "end": end, "host": h, "kind": "END" if he is not None else "T", "p": p, "u": u, "s_raw": float(s), "host_end": he, "d": float(d)})
    return out


def processing_order(ids, main_ids, conns):
    """voies meres d'abord : une voie est traitee quand les voies auxquelles ses extremites se raccordent le sont (cycle : la derniere est liberee)"""
    order = [m for m in main_ids if m in ids]; done = set(order); rest = [i for i in ids if i not in done]
    deps = {i: {c["host"] for c in conns if c["branch"] == i} for i in rest}
    while rest:
        ready = [i for i in rest if deps[i] <= done]
        if not ready: ready = [min(rest, key=lambda i: len(deps[i] - done))]
        for i in ready: order.append(i); done.add(i); rest.remove(i)
    return order


def lead_in(P, H, u, lq_max=40.0, lq_min=12.0):
    """polyligne P (P[0] proche du noeud) : remplace son debut par une courbe de Hermite partant de H avec le cap u (vecteur unitaire)
    et rejoignant P a l'abscisse lq avec la tangente de P."""
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; L = d[-1]
    lq = float(min(lq_max, max(lq_min, 0.45 * L), 0.7 * L)); i = int(np.searchsorted(d, lq)); i = min(max(i, 1), len(P) - 1)
    Qp = P[i]; v = _tangent(P, i); M = float(np.hypot(*(Qp - H)))
    if M < 3.0: P = P.copy(); P[0] = H; return P, False
    t = np.linspace(0, 1, max(6, int(M / 2.0)))[:, None]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t; h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    Hc = h00 * H + h10 * M * u + h01 * Qp + h11 * M * v
    return np.vstack([Hc, P[i + 1:]]), True


def cut_segs(segs, cuts):
    """coupe une liste de segments aux abscisses s (liste de (s, cid)); le segment qui suit une coupe porte 'cut' = cid."""
    if not cuts: return segs
    cuts = sorted(cuts); out = []; cum = 0.0; k = 0
    for g in segs:
        L = g["len"]; starts = [(0.0, None)]
        while k < len(cuts) and cuts[k][0] < cum + L - 1e-6:
            u = max(cuts[k][0] - cum, 0.0); cid = cuts[k][1]; k += 1
            if u < 0.05: starts[0] = (0.0, cid)
            elif u - starts[-1][0] >= 0.05: starts.append((u, cid))
        edges = [a for a, _ in starts] + [L]
        for j, (a, cid) in enumerate(starts):
            x, z, th = pos_on(g, a)
            d = {"type": g["type"], "x": x, "z": z, "tx": math.cos(th), "tz": math.sin(th), "len": edges[j + 1] - a, "k": g["k"]}
            if cid is not None: d["cut"] = cid
            out.append(d)
        cum += L
    return out
