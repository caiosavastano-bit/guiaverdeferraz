# -*- coding: utf-8 -*-
# Monta as chaves novas do pacote da obra: muros, fundacao, precos.
import json, io, math, sys, collections

E = json.load(io.open("eixos.json", encoding="utf-8"))
C = json.load(io.open("muros_cols_fix.json", encoding="utf-8"))
B = json.load(io.open("real_block.json", encoding="utf-8"))
LOG = io.open("dados_log.txt", "w", encoding="utf-8")
P = lambda *a: LOG.write(" ".join(str(x) for x in a) + "\n")
dist = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])

# ---------- eixos ----------
S = [(a, b) for a, b, w in E["segs"] if w >= 1.6]
par = list(range(len(S)))


def f(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i


ends = [(p, i) for i, (a, b) in enumerate(S) for p in (a, b)]
for i in range(len(ends)):
    for j in range(i + 1, len(ends)):
        if dist(ends[i][0], ends[j][0]) < 0.15:
            par[f(ends[i][1])] = f(ends[j][1])
comp = collections.defaultdict(list)
for i, s in enumerate(S):
    comp[f(i)].append(s)


def ring(segs):
    segs = [list(s) for s in segs]
    r = [segs[0][0], segs[0][1]]; used = {0}
    while len(used) < len(segs):
        ok = False
        for i, (a, b) in enumerate(segs):
            if i in used:
                continue
            if dist(a, r[-1]) < 0.15:
                r.append(b); used.add(i); ok = True; break
            if dist(b, r[-1]) < 0.15:
                r.append(a); used.add(i); ok = True; break
        if not ok:
            break
    if dist(r[0], r[-1]) < 0.15:
        r.pop()
    return r


def resample(pts, n):
    L = [0]
    for i in range(1, len(pts)):
        L.append(L[-1] + dist(pts[i - 1], pts[i]))
    out = []
    for k in range(n + 1):
        t = L[-1] * k / n
        i = 1
        while i < len(L) - 1 and L[i] < t:
            i += 1
        u = (t - L[i - 1]) / (L[i] - L[i - 1]) if L[i] > L[i - 1] else 0
        out.append([pts[i - 1][0] + u * (pts[i][0] - pts[i - 1][0]), pts[i - 1][1] + u * (pts[i][1] - pts[i - 1][1])])
    return out


def dp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    L = dist(a, b) or 1e-9
    dm, im = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs((b[0] - a[0]) * (a[1] - pts[i][1]) - (a[0] - pts[i][0]) * (b[1] - a[1])) / L
        if d > dm:
            dm, im = d, i
    if dm <= tol:
        return [a, b]
    return dp(pts[:im + 1], tol)[:-1] + dp(pts[im:], tol)


def centerline(segs):
    r = ring(segs)
    n = len(r)
    edges = [(i, dist(r[i], r[(i + 1) % n])) for i in range(n)]
    per = sum(l for _, l in edges)
    cum = [0]
    for i, l in edges:
        cum.append(cum[-1] + l)
    caps = [i for i, l in edges if 0.85 <= l <= 1.15]
    best = None
    for i in caps:
        for j in caps:
            if j <= i:
                continue
            d = cum[j] - cum[i + 1]  # entre fim da tampa i e inicio da tampa j
            d2 = per - (cum[j + 1] - cum[i])
            sc = abs(d - d2)
            if best is None or sc < best[0]:
                best = (sc, i, j)
    _, i, j = best
    A = [r[k % n] for k in range(i + 1, j + 1)]
    Bc = [r[k % n] for k in range(j + 1, i + n + 1)][::-1]
    La = sum(dist(A[k], A[k + 1]) for k in range(len(A) - 1)); Lb = sum(dist(Bc[k], Bc[k + 1]) for k in range(len(Bc) - 1))
    m = max(8, int(round(max(La, Lb) * 2)))
    ra, rb = resample(A, m), resample(Bc, m)
    cl = [[(p[0] + q[0]) / 2, (p[1] + q[1]) / 2] for p, q in zip(ra, rb)]
    cl = dp(cl, 0.04)
    return cl, La, Lb


def plen(p):
    return sum(dist(p[k], p[k + 1]) for k in range(len(p) - 1))


eix = []
for k, v in comp.items():
    cl, La, Lb = centerline(v)
    eix.append({"cl": cl, "L": plen(cl), "La": La, "Lb": Lb})
    P("componente: eixo %.2f m, lados %.2f / %.2f, vertices %d, de %s a %s" % (plen(cl), La, Lb, len(cl), [round(x, 1) for x in cl[0]], [round(x, 1) for x in cl[-1]]))


def pick(test):
    c = [e for e in eix if test(e)]
    assert len(c) == 1, len(c)
    return c[0]


m1 = pick(lambda e: abs(e["L"] - 158) < 1.5 and min(p[1] for p in e["cl"]) < 7394320)
m4 = pick(lambda e: abs(e["L"] - 118) < 1.5)
m2 = pick(lambda e: abs(e["L"] - 38) < 1.5)
m3 = pick(lambda e: e["L"] > 150 and max(p[1] for p in e["cl"]) > 7394380)
# sentido do estaqueamento
if m1["cl"][0][0] > m1["cl"][-1][0]: m1["cl"].reverse()      # 0+00 no oeste
if m4["cl"][0][0] > m4["cl"][-1][0]: m4["cl"].reverse()      # 0+00 no oeste
if m2["cl"][0][1] < m2["cl"][-1][1]: m2["cl"].reverse()      # 0+00 no norte
if m3["cl"][0][1] > m3["cl"][-1][1]: m3["cl"].reverse()      # 0+00 no canto sudeste
TIPOS = ["0.5x1x5", "0.5x1x6", "0.5x1x7", "0.5x1x8", "1x1x5", "1x1x6", "1x1x7", "1x1x8"]
TAB = {"Muro 1": dict(g05=16.5, g10=195.5, g4r=135, pol=1590, geo=2650),
       "Muro 2": dict(g05=32.75, g10=91.5, g4r=80, pol=0, geo=135),
       "Muro 3": dict(g05=40.25, g10=214.0, g4r=160, pol=1170, geo=2135),
       "Muro 4": dict(g05=19.5, g10=30.0, g4r=35, pol=1120, geo=1885)}
muros = []
for nome, e in (("Muro 1", m1), ("Muro 2", m2), ("Muro 3", m3), ("Muro 4", m4)):
    cols = C[nome]
    s0, s1 = cols[0]["s"], cols[-1]["s"] + 2
    L = plen(e["cl"])
    # trecho da vista que cabe no eixo da planta: do inicio ate sE; o resto (fechamento) fica preso ao ponto final
    if nome == "Muro 1":
        sE = 158.0; k = 1.0           # planta 158 m; vista segue ate 166 (fechamento no canto com o Muro 3)
    else:
        sE = float(s1); k = (s1 - s0) / L   # ajuste proporcional do comprimento da vista ao eixo da planta
    muros.append({"nome": nome, "eixo": [[round(p[0], 2), round(p[1], 2)] for p in e["cl"]], "s0": s0, "sE": sE, "s1": s1, "k": round(k, 5),
                  "passo": 2, "cols": [[c["base"], c["top"]] + [c["pecas"].get(t, 0) for t in TIPOS] for c in cols], "tab": TAB[nome]})
    P(nome, "eixo %.2f m, vista de %d a %d (%d m), fator k %.4f, colunas %d" % (L, s0, s1, s1 - s0, k, len(cols)))


# conferencia do estaqueamento: projeta os rotulos de estaca da planta no eixo mais proximo
def proj(cl, p):
    best = None; acc = 0
    for i in range(len(cl) - 1):
        a, b = cl[i], cl[i + 1]
        vx, vy = b[0] - a[0], b[1] - a[1]; L2 = vx * vx + vy * vy
        t = max(0, min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2)) if L2 else 0
        q = (a[0] + t * vx, a[1] + t * vy); d = dist(p, q)
        if best is None or d < best[0]:
            best = (d, acc + t * math.sqrt(L2))
        acc += math.sqrt(L2)
    return best


for t, e_, n_ in E["sta"]:
    v = int(t.split("+")[0]) * 100 + int(t.split("+")[1])
    r = []
    for m in muros:
        d, arc = proj(m["eixo"], (e_, n_))
        r.append((d, m["nome"], m["s0"] + arc * m["k"]))
    r.sort()
    P("estaca %s (%d): mais perto %s a %.1f m, s pelo eixo %.1f | 2o %s a %.1f m, s %.1f" % (t, v, r[0][1], r[0][0], r[0][2], r[1][1], r[1][0], r[1][2]))

# ---------- casas ----------
casas = []
tipos = [(t[0], t[1], t[3].strip()) for t in B["texts"] if t[3].strip().startswith("TIPO")]
for t in B["texts"]:
    if t[3].strip() == "CASA":
        d, tp = min((dist((t[0], t[1]), (x, y)), s) for x, y, s in tipos)
        tp = {"TIPO 1": 1, "TIPO 2": 2, "TIPO 3 PNE": 3}[tp]
        casas.append([round(t[0], 2), round(t[1], 2), tp])
        if d > 1.5:
            P("!! casa com rotulo de tipo longe", d)
P("casas", len(casas), collections.Counter(c[2] for c in casas))
fund = {"fonte": "Projeto Bassman ES_407 R0, folha 01/04 e 04/04: conjunto de 12 casas tipo 1",
        "conjunto": 12, "furos": [[68, 4.0], [94, 6.0]], "baldrame_m3": 56.48,
        "tipos": [{"id": 1, "nome": "Casa tipo 1", "projeto": True}, {"id": 2, "nome": "Casa tipo 2", "projeto": False}, {"id": 3, "nome": "Casa tipo 3 PNE", "projeto": False}],
        "casas": casas}
IPI = 1.0325
r2 = lambda v: round(v, 2)
precos = {"fonte": "Maccaferri QT0013511 (24/02/2026, com IPI de 3,25%); contrato de mão de obra do muro; BRMIX; valores informados pelo Caio em 22/11/2026",
          "itens": [
              ["t05x5", "Terramesh System 80 PoliMac 0,5×1,0×5,0", "pç", r2(599.08 * IPI)],
              ["t05x6", "Terramesh System 80 PoliMac 0,5×1,0×6,0", "pç", r2(666.06 * IPI)],
              ["t05x7", "Terramesh System 80 PoliMac 0,5×1,0×7,0", "pç", r2(696.21 * IPI)],
              ["t05x8", "Terramesh System 80 PoliMac 0,5×1,0×8,0", "pç", r2(771.77 * IPI)],
              ["t10x5", "Terramesh System 80 PoliMac 1,0×1,0×5,0", "pç", r2(721.95 * IPI)],
              ["t10x6", "Terramesh System 80 PoliMac 1,0×1,0×6,0", "pç", r2(786.83 * IPI)],
              ["t10x7", "Terramesh System 80 PoliMac 1,0×1,0×7,0", "pç", r2(817.91 * IPI)],
              ["t10x8", "Terramesh System 80 PoliMac 1,0×1,0×8,0", "pç", r2(897.85 * IPI)],
              ["g05", "Gabião caixa 8×10 GalMac 4R h=0,50 m", "m³", r2(231.50 * IPI)],
              ["g10", "Gabião caixa 8×10 GalMac 4R h=1,00 m", "m³", r2(169.06 * IPI)],
              ["pol", "Arame PoliMac 3,2 mm", "kg", r2(15.52 * IPI)],
              ["g4r", "Arame GalMac 4R 2,2 mm", "kg", r2(11.27 * IPI)],
              ["geo", "Geotêxtil MacTex H 40.2", "m²", 4.70],
              ["rach", "Rachão", "t", 80.00],
              ["dens", "Rachão: toneladas por m³", "t/m³", 1.50],
              ["moT", "Mão de obra Terramesh", "m³", 115.00],
              ["moG", "Mão de obra gabião", "m³", 105.00],
              ["furo", "Furo de estaca Ø30", "m", 17.40],
              ["conc", "Concreto da viga baldrame FCK 25", "m³", 522.00]]}
json.dump({"muros": {"tipos": TIPOS, "perda_rachao": 1.15, "lista": muros}, "fundacao": fund, "precos": precos},
          io.open("novos_dados.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
LOG.close()
print("ok")
