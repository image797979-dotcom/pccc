"""Vẽ ảnh từng tầng (block MBBT ...) tô màu theo nhóm layer để xem kết cấu tường/cửa/thang."""
import sys, math
import ezdxf
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
doc = ezdxf.readfile("mbbt.dxf")
ms = doc.modelspace()
MAU = [("WALL-PART", "orange"), ("WALL-RENO", "orange"), ("HATCH-WALL", None), ("WALL", "k"), ("COLUM", "r"), ("STAIR", "m"),
       ("DOOR", "b"), ("SANITARY", "c"), ("SANR", "c"), ("FURNITURE", "#bbbbbb"), ("TREE", None), ("SYMBOLS", None), ("CENTER", "#dddddd")]
def mau(l):
    u = l.upper()
    for k, m in MAU:
        if k in u: return m
    return "g"
def phang(e, lop_cha, sau=0):
    if e.dxftype() == "INSERT":
        if sau > 12: return
        try: con = list(e.virtual_entities())
        except Exception: return
        lop = e.dxf.layer if e.dxf.layer != "0" else lop_cha
        for c in con: yield from phang(c, lop, sau + 1)
        return
    yield e, (e.dxf.layer if e.dxf.layer != "0" else lop_cha)
chon = sys.argv[1:]
for ins in ms.query("INSERT"):
    ten = ins.dxf.name
    if not ten.startswith("MBBT") or (chon and ten not in chon): continue
    fig, ax = plt.subplots(figsize=(22, 20))
    for e, l in phang(ins, ins.dxf.layer):
        m = mau(l)
        if m is None: continue
        t = e.dxftype()
        try:
            if t == "LINE":
                ax.plot([e.dxf.start.x, e.dxf.end.x], [e.dxf.start.y, e.dxf.end.y], color=m, lw=0.6)
            elif t in ("LWPOLYLINE", "POLYLINE"):
                p = list(e.flattening(50)) if hasattr(e, "flattening") else []
                if e.dxftype() == "LWPOLYLINE":
                    p = [(v[0], v[1]) for v in e.get_points("xy")]
                    if e.closed: p.append(p[0])
                ax.plot([v[0] for v in p], [v[1] for v in p], color=m, lw=0.6)
            elif t in ("ARC", "CIRCLE", "ELLIPSE", "SPLINE"):
                p = list(e.flattening(30))
                ax.plot([v[0] for v in p], [v[1] for v in p], color=m, lw=0.5)
            elif t in ("TEXT", "MTEXT"):
                s = e.plain_text() if t == "MTEXT" else e.dxf.text
                if "FURN" in l.upper() or "TEXT" in l.upper():
                    ax.text(e.dxf.insert.x, e.dxf.insert.y, s[:20], fontsize=7, color="darkred")
        except Exception: pass
    ax.set_aspect("equal"); ax.set_title(ten)
    ax.grid(True, lw=0.2); ax.minorticks_on()
    fig.savefig(f"anh_{ten.replace(' ', '_')}.png", dpi=80, bbox_inches="tight"); plt.close(fig)
    print("anh", ten, flush=True)
