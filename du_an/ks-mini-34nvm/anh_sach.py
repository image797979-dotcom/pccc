"""Ảnh tường sạch từng tầng (tường, cột, cung cửa, thiết bị vệ sinh, thang) lưới 500 mm để khai báo phòng."""
import sys, ezdxf
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = ezdxf.readfile("tang.dxf")
M = {"WALL": "k", "7. BO - WALL": "k", "COLUMS": "r", "STAIR": "m", "32. BO - SANITARY": "c", "P-SANR-FIXT": "c",
     "DRAW  LINE 3": "g", "154. BO - DRAW  LINE 3": "g", "DRAW  LINE 2": "y", "10. BO - DOOR": "b", "BOUNDARY": "orange", "5. BO - BOUNDARY": "orange"}
for t in sys.argv[1:]:
    fig, ax = plt.subplots(figsize=(24, 24), dpi=60)
    for e in d.blocks["T_" + t]:
        l = e.dxf.layer; ty = e.dxftype()
        m = M.get(l)
        if l == "DOOR" and ty == "ARC" and 400 <= e.dxf.radius <= 1300: m = "b"
        if l == "TEN-PHONG": ax.text(e.dxf.insert.x, e.dxf.insert.y, e.dxf.text, color="darkred", fontsize=12); continue
        if not m: continue
        try:
            if ty == "LWPOLYLINE":
                p = [(v[0], v[1]) for v in e.get_points("xy")]
                if e.closed: p.append(p[0])
            elif ty == "LINE": p = [e.dxf.start, e.dxf.end]
            else: p = list(e.flattening(30))
            xs = [q[0] for q in p]; ys = [q[1] for q in p]
            if min(xs) < -800 or max(xs) > 16500 or min(ys) < -1000 or max(ys) > 16000: continue
            ax.plot(xs, ys, color=m, lw=1)
        except Exception: pass
    ax.set_aspect("equal"); ax.set_xticks(range(-500, 16500, 500)); ax.set_yticks(range(-500, 15500, 500))
    ax.set_xlim(-600, 16000); ax.set_ylim(-600, 15200)
    ax.grid(True, lw=0.4); ax.tick_params(labelsize=9, labelrotation=90); ax.set_title(t)
    fig.tight_layout(); fig.savefig(f"sach_{t}.png"); plt.close(fig)
