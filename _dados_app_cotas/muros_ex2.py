# -*- coding: utf-8 -*-
# Extrai das vistas frontais (PDF vetorial) as colunas de 2 m de cada muro:
# cota de base, cota de topo e pecas Terramesh (pelos rotulos).
import sys, io, re, json, math, collections, glob, os
import pymupdf

PT = 72 / 2.54  # pontos por metro em 1:100
D = sys.argv[1]
OUT = sys.argv[2]
LOG = io.open(sys.argv[3], "w", encoding="utf-8")
SHEETS = [("001", "Muro 1"), ("003", "Muro 1"), ("004", "Muro 2"), ("005", "Muro 3"), ("006", "Muro 4")]


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")


def med(v):
    v = sorted(v)
    return v[len(v) // 2]


def res05(z):
    r = z % 0.5
    return r if r < 0.25 else r - 0.5


res = collections.defaultdict(dict)
for num, muro in SHEETS:
    f = glob.glob(os.path.join(D, num + "*.pdf"))[0]
    pg = pymupdf.open(f)[0]
    pg.remove_rotation()
    words = pg.get_text("words")
    W = [((w[0] + w[2]) / 2, (w[1] + w[3]) / 2, w[4]) for w in words]
    cot = [(x, y, int(t)) for x, y, t in W if re.fullmatch(r"[78]\d\d", t)]
    sta = [(x, y, int(t.split("+")[0]) * 100 + int(t.split("+")[1])) for x, y, t in W if re.fullmatch(r"\d\+\d\d", t)]
    lab = [(x, y, t) for x, y, t in W if re.fullmatch(r"(0\.5|1)x1x\d", t)]
    log("=====", num, muro, "cotas", len(cot), "estacas", len(sta), "rotulos", len(lab))
    vx = []; vy = []
    for (x, y, v) in cot:
        best = None
        for (x2, y2, v2) in cot:
            if v2 == v + 1:
                dd = math.hypot(x2 - x, y2 - y)
                if best is None or dd < best[0]:
                    best = (dd, x2 - x, y2 - y)
        if best and abs(best[0] - PT) < 3:
            vx.append(best[1]); vy.append(best[2])
    nx, ny = round(med(vx) / PT), round(med(vy) / PT)
    tx, ty = ny, -nx
    N = lambda x, y: (x * nx + y * ny) / PT
    sgn = 0
    for p in sta:
        for q in sta:
            if q[2] > p[2] and abs(N(*p[:2]) - N(*q[:2])) < 0.3:
                sgn += 1 if ((q[0] * tx + q[1] * ty) - (p[0] * tx + p[1] * ty)) > 0 else -1
    if sgn < 0:
        tx, ty = -tx, -ty
    T = lambda x, y: (x * tx + y * ty) / PT
    grp = collections.defaultdict(list)
    for x, y, v in cot:
        grp[round(v - N(x, y), 1)].append((x, y, v))
    strips = []
    for off, g in grp.items():
        if len(g) < 6:
            continue
        ts = [T(x, y) for x, y, v in g]; ns = [N(x, y) for x, y, v in g]
        s = {"off": med([v - N(x, y) for x, y, v in g]), "tmin": min(ts), "tmax": max(ts), "nmin": min(ns), "nmax": max(ns)}
        zs = [(v - T(x, y), v) for x, y, v in sta if s["tmin"] - 1 <= T(x, y) <= s["tmax"] + 1 and s["nmax"] - 0.2 <= N(x, y) <= s["nmax"] + 1.5]
        s["sta"] = sorted(v for _, v in zs)
        s["soff"] = med([a for a, _ in zs]) if zs else None
        s["nlab"] = 0
        strips.append(s)
    strips = [s for s in strips if len(s["sta"]) >= 2 or (not s["sta"] and (s["tmax"] - s["tmin"]) > 35)]
    strips.sort(key=lambda s: (s["sta"][0] if s["sta"] else 9999))

    def cands(x, y):
        t = T(x, y); n = N(x, y)
        return [s for s in strips if s["tmin"] - 0.5 <= t <= s["tmax"] + 0.5 and s["nmin"] - 1.2 <= n <= s["nmax"] + 0.7]

    raw = []
    for g in pg.get_drawings():
        if g.get("type") != "s" or (g.get("width") or 0) < 1.6:
            continue
        c = g.get("color") or (9, 9, 9)
        if max(c) > 0.05:
            continue
        for it in g["items"]:
            if it[0] != "l":
                continue
            p, q = it[1], it[2]
            if abs(N(p.x, p.y) - N(q.x, q.y)) < 0.03 and abs(T(p.x, p.y) - T(q.x, q.y)) > 0.4:
                raw.append((min(T(p.x, p.y), T(q.x, q.y)), max(T(p.x, p.y), T(q.x, q.y)), N(p.x, p.y), (p.x + q.x) / 2, (p.y + q.y) / 2))
    for s in strips:
        rr = []
        for a, b, n, mx, my in raw:
            cs = cands(mx, my)
            if len(cs) == 1 and cs[0] is s:
                rr.append(res05(n + s["off"]))
        if rr:
            s["off"] -= med(rr)
        log("faixa off=%.3f n %.1f..%.1f t %.1f..%.1f estacas %s soff %s (calib %d)" % (s["off"], s["nmin"], s["nmax"], s["tmin"], s["tmax"], s["sta"], s["soff"], len(rr)))

    def pick(x, y, target):
        cs = cands(x, y)
        if not cs:
            return None
        return min(cs, key=lambda s: abs(res05(N(x, y) + s["off"] - target)))

    cells = collections.defaultdict(list); segs = collections.defaultdict(list)
    for x, y, t in lab:
        s = pick(x, y, -0.1)
        if s is None:
            continue
        s["nlab"] += 1
        h = 0.5 if t.startswith("0.5") else 1.0
        cells[id(s)].append((T(x, y), N(x, y) + s["off"], h, int(t[-1])))
    for a, b, n, mx, my in raw:
        s = pick(mx, my, 0.0)
        if s is None:
            continue
        segs[id(s)].append((a, b, n + s["off"]))
    prev_end = None
    for s in strips:
        sg = segs[id(s)]
        if not sg:
            continue
        tmin = min(a for a, b, z in sg); tmax = max(b for a, b, z in sg)
        if s["soff"] is None:
            s["soff"] = prev_end - tmin
            log("  faixa sem estaca: continua em s=%.2f" % prev_end)
        log("  desenho de s=%.2f a s=%.2f, rotulos %d, segs %d" % (tmin + s["soff"], tmax + s["soff"], s["nlab"], len(sg)))
        prev_end = tmax + s["soff"]
        cols = res[muro]
        for t, z, h, L in cells[id(s)]:
            st = t + s["soff"]
            k = int(math.floor((st + 0.05) / 2))
            top = math.ceil((z - 0.02) / 0.5) * 0.5
            cols.setdefault(k, {"cells": [], "segz": []})["cells"].append([h, L, top - h])
        for a, b, z in sg:
            a += s["soff"]; b += s["soff"]
            k0 = int(math.floor((a + 0.3) / 2)); k1 = int(math.floor((b - 0.3) / 2))
            for k in range(k0, k1 + 1):
                cols.setdefault(k, {"cells": [], "segz": []})["segz"].append(round(z * 2) / 2)

out = {}
for muro, cols in res.items():
    arr = []; tot = collections.Counter()
    for k in sorted(cols):
        c = cols[k]
        if not c["segz"]:
            log("  !! coluna", k * 2, "com rotulos mas sem contorno", len(c["cells"]))
            continue
        base, top = min(c["segz"]), max(c["segz"])
        hsum = sum(x[0] for x in c["cells"])
        for h, L, zb in c["cells"]:
            tot[("0.5" if h == 0.5 else "1") + "x1x%d" % L] += 1
        zt = [zb for h, L, zb in c["cells"]]
        arr.append({"s": k * 2, "base": base, "top": top, "H": round(top - base, 2), "hcel": hsum,
                    "cbase": min(zt) if zt else None, "ctop": max(zb + h for h, L, zb in c["cells"]) if zt else None,
                    "pecas": dict(collections.Counter(("0.5" if h == 0.5 else "1") + "x1x%d" % L for h, L, zb in c["cells"]))})
    out[muro] = arr
    log("#####", muro, "colunas", len(arr), "s de", arr[0]["s"], "a", arr[-1]["s"] + 2, "| area face %.1f" % sum(2 * c["H"] for c in arr),
        "| area terramesh %.1f" % sum(2 * c["hcel"] for c in arr), "| pecas", dict(sorted(tot.items())))
    for c in arr:
        flag = ""
        if c["hcel"] and (abs(c["hcel"] - c["H"]) > 0.01):
            flag = "  <-- cel != H (cel %s..%s)" % (c["cbase"], c["ctop"])
        log("  s=%3d base %.1f topo %.1f H %4.1f cel %4.1f %s%s" % (c["s"], c["base"], c["top"], c["H"], c["hcel"], c["pecas"], flag))
json.dump(out, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
LOG.close()
print("ok")
