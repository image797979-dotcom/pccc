"""Đọc mbbt.dxf: mỗi block 'MBBT ...' -> thống kê layer lá, bao, chữ (tên phòng) và ảnh kiểm tra."""
import collections, sys, json
import ezdxf
from ezdxf.addons.drawing import matplotlib as dm
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
doc = ezdxf.readfile("mbbt.dxf")
ms = doc.modelspace()
def phang(e, lop_cha, sau=0):
    if e.dxftype() == "INSERT":
        if sau > 12: return
        try: con = list(e.virtual_entities())
        except Exception: return
        lop = e.dxf.layer if e.dxf.layer != "0" else lop_cha
        for c in con: yield from phang(c, lop, sau + 1)
        for a in getattr(e, "attribs", []): yield a, lop
        return
    lop = e.dxf.layer if e.dxf.layer != "0" else lop_cha
    yield e, lop
kq = {}
for ins in ms.query("INSERT"):
    ten = ins.dxf.name
    if not ten.startswith("MBBT"): continue
    c = collections.Counter(); txt = []; xs = []; ys = []
    for e, l in phang(ins, ins.dxf.layer):
        c[(l, e.dxftype())] += 1
        if e.dxftype() in ("TEXT", "MTEXT", "ATTRIB"):
            s = e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text
            p = e.dxf.insert; txt.append((" ".join(s.split())[:50], l, round(p.x), round(p.y)))
        if e.dxftype() == "LINE":
            xs += [e.dxf.start.x, e.dxf.end.x]; ys += [e.dxf.start.y, e.dxf.end.y]
    print("=====", ten, ins.dxf.insert, "bao", round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys)))
    lay = collections.Counter()
    for (l, t), n in c.items(): lay[l] += n
    print(" layers:", lay.most_common(40))
    for t in txt:
        if len(t[0]) > 1 and not t[0].replace('.', '').replace(',', '').isdigit(): print("  T", t)
