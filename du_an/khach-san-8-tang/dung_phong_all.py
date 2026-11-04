"""Dò phòng cho mọi block tầng, lưu JSON và ảnh tổng hợp để kiểm tra."""
import json
import sys

sys.path.insert(0, sys.argv[1])
import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tim_phong as tp

doc = ezdxf.readfile(sys.argv[2])
ra = sys.argv[3]
BLOCKS = ["1", "2", "3", "4", "5", "6", "7", "8", "tum"]
kq = {}
fig, axs = plt.subplots(5, 2, figsize=(26, 30), dpi=70)
for ax, b in zip(axs.flat, BLOCKS):
    bao = False
    if b == "1":
        # tầng 1 để trống mặt ngoài: đóng biên theo trục 1–6, A–C (không gồm tháp thang 2 ngoài trục 6)
        gx, gy = set(), set()
        for e in doc.blocks.get(b):
            if tp._hau_to(e.dxf.layer) == "DLC-TRUC" and e.dxftype() == "LWPOLYLINE":
                (x1, y1), (x2, y2) = [tuple(v) for v in e.get_points("xy")][:2]
                if abs(x1 - x2) < 0.01 * abs(y1 - y2):
                    gx.add((x1 + x2) / 2)
                elif abs(y1 - y2) < 0.01 * abs(x1 - x2):
                    gy.add((y1 + y2) / 2)
        gx, gy = sorted(gx)[:6], sorted(gy)
        bao = (gx[0] - 150, gy[0] - 150, gx[-1] + 150, gy[-1] + 150)
    ds = [p for p in tp.tim_phong_trong_block(doc, b, tp.LOP_TUONG_MAC_DINH, tp.LOP_CUA_MAC_DINH,
                                              bao_theo_cot=bao)
          if p["dien_tich"] >= 0.8]
    if b == "tum":
        # sân mái hở (vùng lớn không tên) không phải phòng
        ds = [p for p in ds if p["ten"] or p["dien_tich"] < 25]
    kq[b] = ds
    doan, dac, cung, net = tp._thu_hinh(doc.blocks.get(b), set(tp.LOP_TUONG_MAC_DINH), set(tp.LOP_CUA_MAC_DINH))
    for a, c in doan + [s for p in net for s in zip(p, p[1:])]:
        ax.plot([a[0], c[0]], [a[1], c[1]], color="#999", lw=0.4)
    for x0, y0, x1, y1 in tp.vung_thang(doc.blocks.get(b)):
        ax.fill([x0, x1, x1, x0], [y0, y0, y1, y1], facecolor="none", edgecolor="red", hatch="///", lw=1)
    cm = plt.get_cmap("tab20")
    for k, p in enumerate(ds):
        x, y = zip(*(p["dg"] + p["dg"][:1]))
        ax.fill(x, y, color=cm(k % 20), alpha=0.4)
        ax.text(sum(x[:-1]) / len(p["dg"]), sum(y[:-1]) / len(p["dg"]), f"{k+1}\n{p['ten'][:14]}\n{p['dien_tich']}",
                fontsize=6, ha="center", va="center")
    ax.set_title(f"Block {b}: {len(ds)} phòng, {sum(p['dien_tich'] for p in ds):.0f} m²")
    ax.set_aspect("equal")
    print(f"Block {b}: {len(ds)} phòng, tổng {sum(p['dien_tich'] for p in ds):.1f} m²", flush=True)
axs.flat[-1].axis("off")
plt.tight_layout()
fig.savefig(ra + ".png")
json.dump(kq, open(ra + ".json", "w", encoding="utf-8"), ensure_ascii=False)
