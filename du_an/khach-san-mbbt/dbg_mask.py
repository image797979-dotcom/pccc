import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import ezdxf, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import tim_phong as tp
TUONG = ["WALL", "WALL-PARTITION", "WALL-RENOVATION", "COLUMS", "GLASS", "STEEL - FRAME", "FUR-CUT"]
CUA = ["DOOR", "10. BO - DOOR"]
tp.LOP_TO_DAC = {"WALL", "COLUMS", "WALL-PARTITION"}
doc = ezdxf.readfile("tang.dxf"); ten = sys.argv[1]
src = doc.blocks["T_" + ten]; d = doc.blocks.new("X")
for e in src:
    if e.dxf.layer in TUONG + CUA:
        try:
            if e.dxftype()=="LINE" and min(e.dxf.start.x,e.dxf.end.x)<-800: continue
            if e.dxftype()=="LWPOLYLINE" and min(p[0] for p in e.get_points("xy"))<-800: continue
        except Exception: pass
        from ezdxf import bbox as _bb
        if e.dxf.layer in CUA:
            q = _bb.extents([e])
            if q.has_data and max(q.size.x, q.size.y) > 3000: continue
        if e.dxftype() == "LWPOLYLINE" and any(abs(b[0]) > 1e-6 for b in e.get_points("b")):
            for v in e.virtual_entities():  # cung cửa (bán kính 0,4–1,3 m) giữ ARC; cung khác -> dây cung
                if v.dxftype() == "ARC" and not 400 <= v.dxf.radius <= 1300:
                    v = d.add_line(v.start_point, v.end_point)
                else:
                    d.add_entity(v)
                v.dxf.layer = e.dxf.layer
            continue
        d.add_entity(e.copy())
L_NHA = [(-150, -50), (3950, -50), (3950, 8000), (20100, 8000), (20100, 20100), (-150, 20100)]
for a, b in zip(L_NHA, L_NHA[1:] + L_NHA[:1]): d.add_line(a, b, dxfattribs={"layer": "WALL"})
doan, dac, cung, net_cua = tp._thu_hinh(d, set(TUONG), set(CUA))
xs = [p[0] for s in doan for p in s]; ys = [p[1] for s in doan for p in s]
bbox = (min(xs) - 1000, min(ys) - 1000, max(xs) + 1000, max(ys) + 1000)
vt = tp._raster(doan, dac, bbox)
vd = tp._raster(tp._dong_lo_cua(vt, bbox, cung, net_cua), [], bbox)
img = np.zeros(vt.shape + (3,)); img[vt] = (0, 0, 0); img[~vt] = (1, 1, 1); img[vd & ~vt] = (0, 0.4, 1)
print("cung", len(cung), "net_cua", len(net_cua))
plt.figure(figsize=(16, 16), dpi=70); plt.imshow(img, origin="lower", extent=(bbox[0], bbox[2], bbox[1], bbox[3]))
for c, a, b in cung: plt.plot([a[0], c[0], b[0]], [a[1], c[1], b[1]], "r-", lw=0.6)
import json
for p in json.load(open("phong.json", encoding="utf-8"))[ten]["phong"]:
    if p["dien_tich"] > 40:
        x, y = zip(*(p["dg"] + p["dg"][:1])); plt.plot(x, y, "g-", lw=2)
plt.grid(True, lw=0.3)
if len(sys.argv) > 2: plt.xlim(float(sys.argv[2]), float(sys.argv[4])); plt.ylim(float(sys.argv[3]), float(sys.argv[5])); plt.savefig(f"mask_{ten}.png")
