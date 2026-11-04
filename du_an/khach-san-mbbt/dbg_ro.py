"""Gỡ lỗi dò phòng: vẽ lưới vật cản (đã khép khe) và tô vùng chứa điểm (x, y) để thấy chỗ hở.
  python dbg_ro.py T3 6000 11200"""
import sys
ten, px, py = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
khung = sys.argv[4:8]
sys.argv = [sys.argv[0]] + khung
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import do_phong as P
tp = P.tp
bn, d = P.chuan_bi(ten)
doan, dac, cung, net_cua = tp._thu_hinh(d, set(P.TUONG), set(P.CUA))
xs = [p[0] for s in doan for p in s] + [p[0] for q in dac for p in q]
ys = [p[1] for s in doan for p in s] + [p[1] for q in dac for p in q]
bbox = (min(xs) - 1000, min(ys) - 1000, max(xs) + 1000, max(ys) + 1000)
vc = tp._raster(doan, dac, bbox); vc = vc | tp._raster(tp._dong_lo_cua(vc, bbox, cung, net_cua), [], bbox)
nhan, so = tp._gan_nhan(~vc)
k = nhan[int((py - bbox[1]) / tp.O), int((px - bbox[0]) / tp.O)]
bien = set(nhan[0, :]) | set(nhan[-1, :]) | set(nhan[:, 0]) | set(nhan[:, -1])
print("nhãn", k, "chạm biên" if k in bien else "kín", "diện tích", (nhan == k).sum() * tp.O ** 2 / 1e6)
img = np.ones(vc.shape + (3,)); img[vc] = 0; img[nhan == k] = (1, 0.6, 0.2)
plt.figure(figsize=(16, 16), dpi=70); plt.imshow(img, origin="lower", extent=(bbox[0], bbox[2], bbox[1], bbox[3]))
import math
for cx, cy, r in P.CUNG:
    t = [i / 40 * 2 * math.pi for i in range(41)]
    plt.plot([cx + r * math.cos(a) for a in t], [cy + r * math.sin(a) for a in t], "b-", lw=0.6)
if len(sys.argv) > 1: plt.xlim(*map(float, sys.argv[1:3])); plt.ylim(*map(float, sys.argv[3:5]))
plt.grid(True, lw=0.3); plt.savefig(f"ro_{ten}.png")
