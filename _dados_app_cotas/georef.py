# -*- coding: utf-8 -*-
# Encaixa a planta de localizacao dos muros (folha 2, PDF 1:500) no arquivo real (UTM)
# usando os rotulos "CASA" das 131 casas como pontos comuns.
import sys, io, json, math, collections
import pymupdf
import numpy as np

pdf, blockjson, outjson = sys.argv[1], sys.argv[2], sys.argv[3]
pg = pymupdf.open(pdf)[0]
pg.remove_rotation()
words = pg.get_text("words")
P = np.array([[(w[0] + w[2]) / 2, (w[1] + w[3]) / 2] for w in words if w[4] == "CASA"])
B = json.load(io.open(blockjson, encoding="utf-8"))
Q = np.array([[t[0], t[1]] for t in B["texts"] if t[3].strip() == "CASA"])
print("PDF CASA", len(P), "DXF CASA", len(Q))
# restringe o PDF a planta (maior aglomerado): usa mediana e descarta longe
med = np.median(P, axis=0)
P = P[np.hypot(*(P - med).T) < 900]
print("PDF CASA na planta", len(P))
S0 = 500 * 0.0254 / 72  # metros por ponto em 1:500
pc = P.mean(axis=0); qc = Q.mean(axis=0)


def nn(A, Bq):
    d = np.hypot(A[:, None, 0] - Bq[None, :, 0], A[:, None, 1] - Bq[None, :, 1])
    return d.argmin(axis=1), d.min(axis=1)


best = None
for mir in (1, -1):
    X = (P - pc) * S0
    X = X * np.array([1, mir])
    for a in np.arange(0, 360, 1.0):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        Y = X @ np.array([[c, s], [-s, c]]) + qc
        idx, d = nn(Y, Q)
        sc = np.median(d)
        if best is None or sc < best[0]:
            best = (sc, mir, a)
print("melhor inicial: mediana %.2f m, espelho %d, angulo %.0f" % best)
_, mir, a = best
X = (P - pc) * S0 * np.array([1, mir])
c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
M = np.array([[c, s], [-s, c]]); tvec = qc.copy(); sc = 1.0
# ICP com similaridade (escala livre)
for it in range(30):
    Y = sc * (X @ M) + tvec
    idx, d = nn(Y, Q)
    keep = d < max(1.0, np.percentile(d, 90))
    A = X[keep]; Bq = Q[idx[keep]]
    ac = A.mean(axis=0); bc = Bq.mean(axis=0)
    H = (A - ac).T @ (Bq - bc)
    U, Sv, Vt = np.linalg.svd(H)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U[:, -1] *= -1; R = U @ Vt
    sc = Sv.sum() / ((A - ac) ** 2).sum()
    M = R
    tvec = bc - sc * (ac @ M)
Y = sc * (X @ M) + tvec
idx, d = nn(Y, Q)
print("pares unicos", len(set(idx.tolist())), "de", len(P))
print("escala ajustada %.5f (1,0 = 1:500 exato)" % sc)
print("erro: media %.3f m, RMS %.3f m, mediana %.3f m, max %.3f m, p90 %.3f" % (d.mean(), math.sqrt((d ** 2).mean()), np.median(d), d.max(), np.percentile(d, 90)))
ang = math.degrees(math.atan2(M[0, 1], M[0, 0]))
print("rotacao %.3f graus, espelho %d" % (ang, mir))
json.dump({"pc": pc.tolist(), "S0": S0, "mir": mir, "M": M.tolist(), "sc": sc, "t": tvec.tolist(),
           "rms": math.sqrt((d ** 2).mean()), "max": float(d.max()), "n": int(len(P))}, io.open(outjson, "w"))
# estatistica dos tracos na regiao da planta
x0, y0 = P.min(axis=0) - 150; x1, y1 = P.max(axis=0) + 150
st = collections.Counter()
for g in pg.get_drawings():
    r = g["rect"]
    if r.x0 > x1 or r.x1 < x0 or r.y0 > y1 or r.y1 < y0:
        continue
    st[(g.get("type"), tuple(round(v, 2) for v in (g.get("color") or ())), tuple(round(v, 2) for v in (g.get("fill") or ())), round(g.get("width") or 0, 2), str(g.get("dashes"))[:14])] += 1
for k, v in st.most_common(25):
    print(v, k)
print("bbox planta", x0, y0, x1, y1)
