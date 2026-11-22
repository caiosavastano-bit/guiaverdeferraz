# -*- coding: utf-8 -*-
# Extrai da planta de localizacao (folha 2) os tracos pretos grossos (muros) e os rotulos de estaca,
# ja em UTM, e desenha uma figura de conferencia.
import sys, io, json, math, re, collections
import pymupdf
import numpy as np
from PIL import Image, ImageDraw

pdf, gj, blockjson, outjson, outpng = sys.argv[1:6]
G = json.load(io.open(gj))
pc = np.array(G["pc"]); M = np.array(G["M"]); tv = np.array(G["t"])


def utm(x, y):
    X = (np.array([x, y]) - pc) * G["S0"] * np.array([1, G["mir"]])
    return (G["sc"] * (X @ M) + tv).tolist()


pg = pymupdf.open(pdf)[0]
pg.remove_rotation()
x0, y0, x1, y1 = 940, 112, 1701, 1364
segs = []; red = []
for g in pg.get_drawings():
    r = g["rect"]
    if r.x0 > x1 or r.x1 < x0 or r.y0 > y1 or r.y1 < y0:
        continue
    if g.get("type") != "s":
        continue
    c = tuple(round(v, 2) for v in (g.get("color") or ()))
    w = round(g.get("width") or 0, 2)
    for it in g["items"]:
        if it[0] == "l":
            a = utm(it[1].x, it[1].y); b = utm(it[2].x, it[2].y)
            if c == (0.0, 0.0, 0.0) and w >= 1.4:
                segs.append([a, b, w])
            elif c == (1.0, 0.0, 0.0):
                red.append([a, b, w])
words = pg.get_text("words")
sta = []; names = []
for w in words:
    cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
    if not (x0 <= cx <= x1 and y0 <= cy <= y1):
        continue
    if re.fullmatch(r"\d\+\d\d", w[4]):
        sta.append([w[4]] + utm(cx, cy))
    if w[4] in ("Muro", "MURO", "Ext.:", "PERFIL"):
        names.append([w[4]] + utm(cx, cy))
txt = pg.get_text("dict")
labels = []
for b in txt["blocks"]:
    for l in b.get("lines", []):
        t = "".join(s["text"] for s in l["spans"]).strip()
        if re.search(r"Muro 0\d|Ext\.|MURO \d|PERFIL", t):
            bb = l["bbox"]
            cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            if x0 <= cx <= x1 and y0 <= cy <= y1:
                labels.append([t] + utm(cx, cy))
L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b, w in segs)
print("segmentos pretos grossos", len(segs), "comprimento total %.1f m" % L, collections.Counter(w for *_, w in segs))
print("vermelhos", len(red), "estacas", len(sta), "rotulos", labels)
json.dump({"segs": segs, "red": red, "sta": sta, "labels": labels}, io.open(outjson, "w", encoding="utf-8"), ensure_ascii=False)
# figura
B = json.load(io.open(blockjson, encoding="utf-8"))
E0, N0, E1, N1 = 360455, 7394290, 360660, 7394425
k = 14
im = Image.new("RGB", (int((E1 - E0) * k), int((N1 - N0) * k)), "white")
d = ImageDraw.Draw(im)
px = lambda e, n: ((e - E0) * k, (N1 - n) * k)
for lay, closed, pts, depth in B["polys"]:
    if lay in ("A-WALL", "0", "C-TOPO") and len(pts) >= 2:
        d.line([px(*p) for p in pts], fill=(190, 190, 190), width=1)
for a, b, w in red:
    d.line([px(*a), px(*b)], fill=(255, 150, 150), width=1)
for a, b, w in segs:
    d.line([px(*a), px(*b)], fill=(0, 0, 0) if w < 1.6 else (0, 0, 255), width=3)
for t, e, n in sta:
    d.text(px(e, n), t, fill=(200, 0, 0))
for t, e, n in labels:
    d.text(px(e, n), t, fill=(0, 120, 0))
im.save(outpng)
print(im.size)
