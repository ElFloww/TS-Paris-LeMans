"""Ajustement d'une polyligne (m) par droites et arcs a courbure constante, continu en position et en tangente."""
import math
import numpy as np

def resample(P, step):
    P=np.asarray(P,float); d=np.r_[0,np.cumsum(np.hypot(*np.diff(P,axis=0).T))]
    s=np.arange(0,d[-1],step); s=np.r_[s,d[-1]]
    return s, np.c_[np.interp(s,d,P[:,0]),np.interp(s,d,P[:,1])]

def heading(Q, win=5):
    """cap lisse (rad, deplie) en chaque point"""
    v=np.gradient(Q,axis=0); th=np.unwrap(np.arctan2(v[:,1],v[:,0]))
    k=np.ones(win)/win; pad=win//2
    thp=np.r_[np.full(pad,th[0]),th,np.full(pad,th[-1])]
    return np.convolve(thp,k,mode='valid')

def breakpoints(s, th, tol, min_len):
    """decoupage recursif de th(s) en morceaux lineaires (ecart max < tol)"""
    out=[0,len(s)-1]
    stack=[(0,len(s)-1)]; res=set(out)
    while stack:
        a,b=stack.pop()
        if b-a<2: continue
        line=th[a]+(th[b]-th[a])*(s[a:b+1]-s[a])/(s[b]-s[a]); err=np.abs(th[a:b+1]-line)
        i=int(np.argmax(err))+a
        if err.max()>tol and (s[i]-s[a])>=min_len and (s[b]-s[i])>=min_len:
            res.add(i); stack+= [(a,i),(i,b)]
    return sorted(res)

def _end(x,z,t,k,L):
    if abs(k)<1e-12: return x+math.cos(t)*L, z+math.sin(t)*L, t
    t2=t+k*L; return x+(math.sin(t2)-math.sin(t))/k, z-(math.cos(t2)-math.cos(t))/k, t2

def _solve_k(x,z,t,L,T):
    """courbure k telle que la fin de l'arc (longueur L, cap initial t) soit sur le rayon depart->T"""
    dx,dz=T[0]-x,T[1]-z; n=math.hypot(dx,dz); ux,uz=dx/n,dz/n
    g=lambda k:(lambda e:(e[0]-x)*(-uz)+(e[1]-z)*ux)(_end(x,z,t,k,L))
    lo,hi=-1/60.0,1/60.0
    glo,ghi=g(lo),g(hi)
    if glo*ghi>0: return lo if abs(glo)<abs(ghi) else hi
    for _ in range(60):
        mid=(lo+hi)/2; gm=g(mid)
        if glo*gm<=0: hi=mid
        else: lo,glo=mid,gm
    return (lo+hi)/2

def _build(s, Q, th, bp, straight_k):
    segs = []; x, z = Q[0]; t = th[0]
    for a, b in zip(bp, bp[1:]):
        L = s[b] - s[a]; k = _solve_k(x, z, t, L, Q[b])
        if abs(k) < straight_k:
            ex, ez, _ = _end(x, z, t, 0.0, L)
            if math.hypot(ex - Q[b][0], ez - Q[b][1]) < 0.15: k = 0.0
        segs.append({'type': 'straight' if k == 0 else 'arc', 'x': x, 'z': z, 'tx': math.cos(t), 'tz': math.sin(t), 'len': L, 'k': k})
        x, z, t = _end(x, z, t, k, L)
    return segs

def fit(P, step=5.0, tol=0.001, min_len=20.0, straight_k=1/20000, dev_tol=1.0, sigma_m=30.0):
    """segments continus (position et tangente) sur une version LISSEE de la polyligne (gaussienne sigma_m, extremites fixes) ;
    un segment qui s'ecarte de plus de dev_tol metres de la polyligne d'origine est coupe en deux et recalcule"""
    from shapely.geometry import LineString, Point
    from scipy.ndimage import gaussian_filter1d
    s, Q0 = resample(P, step)
    S = np.c_[gaussian_filter1d(Q0[:, 0], sigma_m / step, mode='nearest'), gaussian_filter1d(Q0[:, 1], sigma_m / step, mode='nearest')]
    S[0], S[-1] = Q0[0], Q0[-1]
    th = heading(S); bp = breakpoints(s, th, tol, min_len); ls = LineString(Q0)
    for _ in range(12):
        segs = _build(s, S, th, bp, straight_k); new = set(bp)
        for j, g in enumerate(segs):
            if bp[j + 1] - bp[j] < 2: continue
            m = sample_segs([g], 5.0)
            if max(ls.distance(Point(*p)) for p in m) > dev_tol: new.add((bp[j] + bp[j + 1]) // 2)
        if len(new) == len(bp): break
        bp = sorted(new)
    return segs

def sample_segs(segs, step=2.0):
    pts=[]
    for g in segs:
        n=max(2,int(g['len']/step)+1); th=math.atan2(g['tz'],g['tx'])
        for u in np.linspace(0,g['len'],n):
            if g['k']==0: pts.append((g['x']+g['tx']*u,g['z']+g['tz']*u))
            else:
                k=g['k']; pts.append((g['x']+(math.sin(th+k*u)-math.sin(th))/k, g['z']-(math.cos(th+k*u)-math.cos(th))/k))
    return np.array(pts)

def max_deviation(P, segs):
    from shapely.geometry import LineString, Point
    ls=LineString(P); S=sample_segs(segs)
    return max(ls.distance(Point(*p)) for p in S), math.hypot(*(S[-1]-np.asarray(P[-1])))



def fit_ls(P, step=5.0, sigma_m=20.0, tol=0.003, min_len=30.0, chunk=40, lam=2500.0, straight_k=1/20000, t_start=None, t_end=None):
    """segments droite/arc continus : courbures ajustees par moindres carres sur la polyligne lissee (continuite position+cap
    entre segments, penalite sur les sauts de courbure) -> pas d'oscillation de courbure, contrairement a l'ancrage point par point."""
    from scipy.ndimage import gaussian_filter1d
    from scipy.optimize import least_squares
    s, Q0 = resample(P, step)
    S = np.c_[gaussian_filter1d(Q0[:, 0], sigma_m / step, mode='nearest'), gaussian_filter1d(Q0[:, 1], sigma_m / step, mode='nearest')]
    S[0], S[-1] = Q0[0], Q0[-1]
    th = heading(S)
    if t_start is not None: th = th.copy(); th[0] = t_start + 2 * math.pi * round((th[0] - t_start) / (2 * math.pi))   # cap de depart impose (raccord tangent a la voie mere)
    bp = breakpoints(s, th, tol, min_len)
    if t_end is not None:   # segment final court (30 m) pour absorber la correction de position/cap a l'extremite raccordee
        j = int(np.searchsorted(s, s[-1] - 30.0))
        if 0 < j < len(s) - 1 and bp[-2] < j - 1: bp = bp[:-1] + [j, bp[-1]]
    segs = []; x, z, t0 = S[0][0], S[0][1], th[0]; kprev = 0.0
    for c0 in range(0, len(bp) - 1, chunk):
        b = bp[c0:c0 + chunk + 1]; nseg = len(b) - 1; L = np.array([s[b[i + 1]] - s[b[i]] for i in range(nseg)])
        idx = np.arange(b[0] + 1, b[-1] + 1); seg_of = np.searchsorted(np.array(b[1:]), idx, side='left')
        target = S[idx]
        def path(k):
            th_s = t0 + np.r_[0, np.cumsum(k * L)][:-1]; ex, ez = [x], [z]
            sx = np.zeros(nseg); sz = np.zeros(nseg)
            for j in range(nseg):
                if abs(k[j]) < 1e-12: sx[j] = x if j == 0 else ex[-1]
                ex.append(0); ez.append(0)
            # integration segment par segment
            px, pz, ps = [x], [z], [t0]; X = np.empty(len(idx)); Z = np.empty(len(idx))
            cx, cz, ct = x, z, t0
            for j in range(nseg):
                m = seg_of == j; u = s[idx[m]] - s[b[j]]
                if abs(k[j]) < 1e-12: X[m] = cx + np.cos(ct) * u; Z[m] = cz + np.sin(ct) * u
                else: X[m] = cx + (np.sin(ct + k[j] * u) - np.sin(ct)) / k[j]; Z[m] = cz - (np.cos(ct + k[j] * u) - np.cos(ct)) / k[j]
                if abs(k[j]) < 1e-12: cx += np.cos(ct) * L[j]; cz += np.sin(ct) * L[j]
                else: cx += (np.sin(ct + k[j] * L[j]) - np.sin(ct)) / k[j]; cz -= (np.cos(ct + k[j] * L[j]) - np.cos(ct)) / k[j]; ct += k[j] * L[j]
            return X, Z, (cx, cz, ct)
        last = c0 + chunk >= len(bp) - 1
        def res(k):
            X, Z, (_, _, ct_) = path(k); r_ = np.r_[X - target[:, 0], Z - target[:, 1], lam * np.diff(np.r_[kprev, k])]
            if last and t_end is not None: r_ = np.r_[r_, 400.0 * ((ct_ - t_end + math.pi) % (2 * math.pi) - math.pi), 400.0 * (X[-1] - target[-1, 0]), 400.0 * (Z[-1] - target[-1, 1])]   # cap et position d'arrivee imposes (1 deg ~ 1,7 m)
            return r_
        k0 = np.array([(th[b[i + 1]] - th[b[i]]) / L[i] for i in range(nseg)]); k0 = np.clip(k0, -1/60, 1/60)
        sol = least_squares(res, k0, bounds=(-1/60, 1/60), method='trf', x_scale=1e-3, max_nfev=120)
        k = np.where(np.abs(sol.x) < straight_k, 0.0, sol.x)
        cx, cz, ct = x, z, t0
        for j in range(nseg):
            segs.append({'type': 'straight' if k[j] == 0 else 'arc', 'x': cx, 'z': cz, 'tx': math.cos(ct), 'tz': math.sin(ct), 'len': float(L[j]), 'k': float(k[j])})
            cx, cz, ct = _end(cx, cz, ct, k[j], L[j])
        x, z, t0, kprev = cx, cz, ct, k[-1]
    return segs
