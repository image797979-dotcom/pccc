"""Ảnh kiểm tra từng tầng từ tang.dxf: tường đen, cột tô, cửa xanh, thang tím, vệ sinh cam, chữ đỏ."""
import sys, math
import ezdxf, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
doc = ezdxf.readfile("tang.dxf")
MAU = {"WALL": "k", "WALL-PARTITION": "k", "WALL-RENOVATION": "k", "COLUMS": "k", "DOOR": "tab:blue", "GLASS": "tab:cyan",
       "STAIR": "tab:purple", "SANITARY": "tab:orange", "32. BO - SANITARY": "tab:orange", "STEEL - FRAME": "tab:green"}
for ten in sys.argv[1:]:
    blk = doc.blocks["T_" + ten]
    fig, ax = plt.subplots(figsize=(18, 14), dpi=80)
    for e in blk:
        l, t = e.dxf.layer, e.dxftype()
        m = MAU.get(l, "0.8"); lw = 1.4 if m == "k" else 0.5
        if t == "LINE":
            ax.plot([e.dxf.start.x, e.dxf.end.x], [e.dxf.start.y, e.dxf.end.y], color=m, lw=lw)
        elif t == "LWPOLYLINE":
            p = [tuple(v) for v in e.get_points("xy")]
            if l == "COLUMS" and e.closed:
                ax.add_patch(Polygon(p, closed=True, color="k"))
            if e.closed: p.append(p[0])
            ax.plot([a for a, b in p], [b for a, b in p], color=m, lw=lw)
        elif t in ("ARC", "CIRCLE"):
            c, r = e.dxf.center, e.dxf.radius
            a0, a1 = (e.dxf.start_angle, e.dxf.end_angle) if t == "ARC" else (0, 360)
            if a1 < a0: a1 += 360
            th = [math.radians(a0 + (a1 - a0) * i / 30) for i in range(31)]
            ax.plot([c.x + r * math.cos(x) for x in th], [c.y + r * math.sin(x) for x in th], color=m, lw=lw)
        elif t == "TEXT" and l in ("TEN-PHONG",):
            ax.text(e.dxf.insert.x, e.dxf.insert.y, e.dxf.text, color="r", fontsize=9)
    ax.set_aspect("equal"); ax.grid(True, lw=0.3); ax.set_title(ten)
    ax.xaxis.set_major_locator(plt.MultipleLocator(2000)); ax.yaxis.set_major_locator(plt.MultipleLocator(2000))
    plt.xticks(fontsize=6, rotation=90); plt.yticks(fontsize=6)
    fig.tight_layout(); fig.savefig(f"anh_{ten}.png"); plt.close(fig); print("saved", ten)
