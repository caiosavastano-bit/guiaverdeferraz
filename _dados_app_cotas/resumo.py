# -*- coding: utf-8 -*-
import json, io, sys, collections
d = json.load(io.open("muros_cols.json", encoding="utf-8"))
out = io.open("resumo.txt", "w", encoding="utf-8")
P = lambda *a: out.write(" ".join(str(x) for x in a) + "\n")
# colunas sem rotulo dentro do trecho Terramesh: copiar do vizinho da esquerda (quebra de folha)
fix = {"Muro 3": 80, "Muro 4": 78}
for m, s in fix.items():
    arr = d[m]
    i = [k for k, c in enumerate(arr) if c["s"] == s][0]
    arr[i]["pecas"] = dict(arr[i - 1]["pecas"]); arr[i]["hcel"] = arr[i]["H"]
TAB = {"Muro 1": {"0.5x1x6": 100, "1x1x6": 86, "0.5x1x7": 220, "1x1x7": 174, "0.5x1x8": 154, "1x1x8": 115, "g05": 16.5, "g10": 195.5, "g4r": 135, "pol": 1590, "geo": 2650, "rach": 1655, "face": 1319},
       "Muro 2": {"g05": 32.75, "g10": 91.5, "g4r": 80, "pol": 0, "geo": 135, "rach": 145, "face": 82},
       "Muro 3": {"0.5x1x6": 114, "1x1x6": 99, "0.5x1x7": 163, "1x1x7": 129, "0.5x1x8": 72, "1x1x8": 61, "g05": 40.25, "g10": 214.0, "g4r": 160, "pol": 1170, "geo": 2135, "rach": 1360, "face": 1071},
       "Muro 4": {"0.5x1x5": 127, "1x1x5": 96, "0.5x1x7": 231, "1x1x7": 193, "g05": 19.5, "g10": 30.0, "g4r": 35, "pol": 1120, "geo": 1885, "rach": 1135, "face": 936}}
IPI = 1.0325
PU = {"0.5x1x5": 599.08 * IPI, "0.5x1x6": 666.06 * IPI, "0.5x1x7": 696.21 * IPI, "0.5x1x8": 771.77 * IPI,
      "1x1x5": 721.95 * IPI, "1x1x6": 786.83 * IPI, "1x1x7": 817.91 * IPI, "1x1x8": 897.85 * IPI,
      "g05": 231.50 * IPI, "g10": 169.06 * IPI, "pol": 15.52 * IPI, "g4r": 11.27 * IPI, "geo": 4.70}
MO_T, MO_G = 115.0, 105.0
tot_all = collections.Counter(); custo_all = 0
for m, arr in d.items():
    T = TAB[m]
    pec = collections.Counter()
    for c in arr:
        pec.update(c["pecas"])
    face = sum(2 * c["H"] for c in arr)
    at = sum(2 * c["hcel"] for c in arr)  # face terramesh
    ag = face - at
    ok = all(pec.get(k, 0) == v for k, v in T.items() if "x1x" in k)
    vt = sum(n * (1 if k.startswith("0.5") else 2) for k, n in pec.items())  # m3 de caixa terramesh
    vg = T["g05"] + T["g10"]
    mac = sum(pec[k] * PU[k] for k in pec) + T["g05"] * PU["g05"] + T["g10"] * PU["g10"] + T["pol"] * PU["pol"] + T["g4r"] * PU["g4r"] + T["geo"] * PU["geo"]
    mo = vt * MO_T + vg * MO_G
    P("#", m, "| comprimento %d m (s %d a %d)" % (len(arr) * 2, arr[0]["s"], arr[-1]["s"] + 2), "| H min %.1f max %.1f" % (min(c["H"] for c in arr), max(c["H"] for c in arr)),
      "| cota base min %.1f topo max %.1f" % (min(c["base"] for c in arr), max(c["top"] for c in arr)),
      "| face %.0f (tabela %s) terramesh %.0f gabiao %.0f" % (face, T["face"], at, ag), "| pecas conferem:", ok)
    P("   caixa terramesh %.0f m3, gabiao %.2f m3, rachao 1,15x = %.1f (tabela %s)" % (vt, vg, 1.15 * (vt + vg), T["rach"]),
      "| Maccaferri R$ %.2f (R$ %.2f/m2) | MO R$ %.2f | rachao m3/m2 %.3f | geo m2/m2 %.3f | pol kg/m2 terramesh %.3f" % (mac, mac / face, mo, T["rach"] / face, T["geo"] / face, (T["pol"] / at if at else 0)))
    custo_all += mac
    tot_all.update(pec)
    # faixas de altura
    bands = [(0, 3), (3, 5), (5, 7), (7, 9), (9, 12)]
    for a, b in bands:
        cs = [c for c in arr if a < c["H"] <= b]
        if not cs:
            continue
        L = len(cs) * 2
        pc = collections.Counter()
        for c in cs:
            pc.update(c["pecas"])
        f = sum(2 * c["H"] for c in cs); ft = sum(2 * c["hcel"] for c in cs); fg = f - ft
        gab = (vg * fg / ag) if ag else vg * f / face
        vtt = sum(n * (1 if k.startswith("0.5") else 2) for k, n in pc.items())
        macb = sum(pc[k] * PU[k] for k in pc) + gab * (T["g05"] * PU["g05"] + T["g10"] * PU["g10"]) / vg + (T["pol"] * PU["pol"] * ft / at if at else 0) + T["g4r"] * PU["g4r"] * gab / vg + T["geo"] * PU["geo"] * f / face
        rach = 1.15 * (vtt + gab)
        mob = vtt * MO_T + gab * MO_G
        P("   H %d-%d m: %3d m de muro | por metro: face %.1f m2, pecas 0,5: %.2f, pecas 1,0: %.2f, gabiao %.2f m3, rachao %.2f m3 | Maccaferri R$ %.0f/m, MO R$ %.0f/m"
          % (a, b, L, f / L, sum(n for k, n in pc.items() if k.startswith("0.5")) / L, sum(n for k, n in pc.items() if k.startswith("1x")) / L, gab / L, rach / L, macb / L, mob / L))
P("TOTAL pecas", dict(sorted(tot_all.items())))
P("TOTAL Maccaferri R$ %.2f (proposta 1.869.671,63)" % custo_all)
P("PU com IPI:", {k: round(v, 2) for k, v in PU.items()})
json.dump(d, io.open("muros_cols_fix.json", "w", encoding="utf-8"), ensure_ascii=False)
out.close()
