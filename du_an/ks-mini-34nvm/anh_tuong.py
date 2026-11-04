"""Ảnh tường/cột/cửa/thang từng tầng từ tang.dxf (toạ độ tầng) để dò đường bao và kiểm tra."""
import sys, ezdxf
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = ezdxf.readfile("tang.dxf")
M = {"WALL": "k", "7. BO - WALL": "k", "COLUMS": "r", "STAIR": "m", "DOOR": "b", "10. BO - DOOR": "c",
     "DRAW  LINE 3": "g", "154. BO - DRAW  LINE 3": "g", "DRAW  LINE 2": "y", "TEN-PHONG": "darkred",
     "BOUNDARY": "orange", "5. BO - BOUNDARY": "orange", "32. BO - SANITARY": "#aaa", "P-SANR-FIXT": "#aaa"}
for t in sys.argv[1:]:
    fig, ax = plt.subplots(figsize=(18, 18), dpi=70)
    for e in d.blocks["T_" + t]:
        m = M.get(e.dxf.layer)
        if not m: continue
        try:
            if e.dxftype() == "TEXT":
                ax.text(e.dxf.insert.x, e.dxf.insert.y, e.dxf.text, color=m, fontsize=8); continue
            if e.dxftype() == "LWPOLYLINE":
                p = [(v[0], v[1]) for v in e.get_points("xy")] + ([e.get_points("xy")[0][:2]] if e.closed else [])
            elif e.dxftype() == "LINE": p = [e.dxf.start, e.dxf.end]
            else: p = list(e.flattening(30))
            xs = [q[0] for q in p]; ys = [q[1] for q in p]
            if min(xs) < -1500 or max(xs) > 17000: continue
            ax.plot(xs, ys, color=m, lw=0.7)
        except Exception: pass
    ax.set_aspect("equal"); ax.set_xticks(range(-1000, 17000, 1000)); ax.set_yticks(range(-3000, 20000, 1000))
    ax.grid(True, lw=0.3); ax.tick_params(labelsize=7); ax.set_title(t)
    fig.tight_layout(); fig.savefig(f"tuong_{t}.png"); plt.close(fig)
