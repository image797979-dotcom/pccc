"""Ảnh phóng một vùng của tầng: python zoom.py T3 x0 y0 x1 y1 — màu theo layer, ghi tên layer chú giải."""
import sys, math
import ezdxf, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from ezdxf import bbox
doc = ezdxf.readfile("tang.dxf"); ten = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6])
cm = plt.get_cmap("tab10"); mau = {}
fig, ax = plt.subplots(figsize=(14, 14), dpi=70)
for e in doc.blocks["T_" + ten]:
    l, t = e.dxf.layer, e.dxftype()
    if l in ("FURNITURE",): continue
    c = mau.setdefault(l, cm(len(mau) % 10))
    if t == "LINE": pts = [e.dxf.start, e.dxf.end]
    elif t == "LWPOLYLINE":
        pts = [tuple(v) for v in e.get_points("xy")] + ([tuple(e.get_points("xy")[0])] if e.closed else [])
    elif t in ("ARC", "CIRCLE"):
        cc, r = e.dxf.center, e.dxf.radius
        a0, a1 = (e.dxf.start_angle, e.dxf.end_angle) if t == "ARC" else (0, 360)
        if a1 < a0: a1 += 360
        pts = [(cc.x + r * math.cos(math.radians(a0 + (a1 - a0) * i / 20)), cc.y + r * math.sin(math.radians(a0 + (a1 - a0) * i / 20))) for i in range(21)]
    else: continue
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1: continue
    ax.plot(xs, ys, color=c, lw=1.2 if l in ("WALL", "COLUMS") else 0.8, label=l)
h, lb = ax.get_legend_handles_labels(); u = dict(zip(lb, h)); ax.legend(u.values(), u.keys(), fontsize=8)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.grid(True, lw=0.3)
fig.tight_layout(); fig.savefig(f"zoom_{ten}.png")
