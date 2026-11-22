# -*- coding: utf-8 -*-
# explode recursivamente os INSERT do modelspace e resume camadas, textos e polilinhas
import sys, io, collections, json
import ezdxf
doc = ezdxf.readfile(sys.argv[1])
msp = doc.modelspace()
o = io.open(sys.argv[2], "w", encoding="utf-8")
cnt = collections.Counter()
texts = []
polys = []


def walk(e, depth=0):
    t = e.dxftype()
    if t == "INSERT":
        if depth == 0:
            o.write("INSERT %s layer=%s at %s scale=(%s,%s) rot=%s\n" % (e.dxf.name, e.dxf.layer, tuple(round(v, 3) for v in e.dxf.insert), e.dxf.get("xscale", 1), e.dxf.get("yscale", 1), e.dxf.get("rotation", 0)))
        try:
            for v in e.virtual_entities():
                walk(v, depth + 1)
        except Exception as ex:
            o.write("ERR %s\n" % ex)
        return
    cnt[(depth > 0, e.dxf.layer, t)] += 1
    if t == "TEXT":
        p = e.dxf.insert
        texts.append([round(p.x, 3), round(p.y, 3), e.dxf.layer, e.dxf.text, round(e.dxf.get("rotation", 0), 2), round(e.dxf.get("height", 0), 3)])
    elif t == "MTEXT":
        p = e.dxf.insert
        texts.append([round(p.x, 3), round(p.y, 3), e.dxf.layer, e.plain_text().replace("\n", " "), round(e.dxf.get("rotation", 0) or 0, 2), round(e.dxf.get("char_height", 0), 3)])
    elif t == "LWPOLYLINE":
        pts = [[round(x, 3), round(y, 3)] for x, y, *_ in e.get_points()]
        polys.append([e.dxf.layer, bool(e.closed), pts, depth])
    elif t == "LINE":
        polys.append([e.dxf.layer, False, [[round(e.dxf.start.x, 3), round(e.dxf.start.y, 3)], [round(e.dxf.end.x, 3), round(e.dxf.end.y, 3)]], depth])
    elif t == "POLYLINE":
        pts = [[round(v.dxf.location.x, 3), round(v.dxf.location.y, 3)] for v in e.vertices]
        polys.append([e.dxf.layer, bool(e.is_closed), pts, depth])


for e in msp:
    walk(e)
for k, v in sorted(cnt.items(), key=lambda kv: (-kv[1])):
    o.write("%s\t%s\t%s\t%d\n" % (k[0], k[1], k[2], v))
tc = collections.Counter(t[3][:30] for t in texts)
o.write("--- textos mais comuns\n")
for k, v in tc.most_common(60):
    o.write("%d\t%s\n" % (v, k))
o.close()
json.dump({"texts": texts, "polys": polys}, io.open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
print("texts", len(texts), "polys", len(polys))
