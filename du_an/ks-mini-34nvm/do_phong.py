"""Dò phòng từng tầng từ tang.dxf bằng tim_phong; lưu phong.json + ảnh kiểm tra anh_phong_<tầng>.png.

  python do_phong.py [tầng ...]
Chỉ lấy phần nhà (x > -800); block dò 'D_<tầng>' chỉ gồm tường/cột/kính/khung/cửa/thang/chữ."""
import json, sys, os, math
import numpy as np
sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import ezdxf, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tim_phong as tp

TUONG = ["WALL", "7. BO - WALL", "COLUMS"]
CUA = ["DOOR", "10. BO - DOOR"]
GIU = set(TUONG + CUA + ["STAIR", "TEN-PHONG"])
tp.LOP_TO_DAC = {"WALL", "COLUMS", "7. BO - WALL"}


_raster_goc = tp._raster
KHE = int(1300 / tp.O)  # khe dài nhất xét (ô lưới)
KHE_LUON = 800          # mm: khe trên lưới <= 0,8 m luôn khép (hành lang 1,0 m đo trên lưới ~0,9 m)
# Chế độ "--min": dò phòng chi tiết (khép mọi khe <= 1,0 m) để tách WC, buồng thang ra khỏi phòng ngủ/hành lang.
CHI_TIET = "--min" in sys.argv
if CHI_TIET:
    sys.argv.remove("--min")
    KHE_LUON = 1000
FILE_RA = "phong_min.json" if CHI_TIET else "phong.json"
CUNG = []               # [(tâm x, tâm y, bán kính)] cung cửa của tầng đang dò (chuan_bi điền)


def _raster_khep(doan, dac, bbox):
    """Lưới tường + khép lỗ cửa: khe ngang/dọc nằm trọn trong tầm một cung cửa
    (hai mép khe cách tâm bản lề <= r + 150 mm, khe dài <= r + 150 mm)."""
    vc = _raster_goc(doan, dac, bbox)
    if not dac:
        return vc
    return vc | _dong_khe(vc, bbox, False) | _dong_khe(vc.T, bbox, True).T


def _dong_khe(m, bbox, doc):
    x0, y0 = bbox[0], bbox[1]
    kq = np.zeros_like(m)
    for j in range(m.shape[0]):
        idx = np.flatnonzero(m[j])
        if len(idx) < 2:
            continue
        gap = np.diff(idx)
        for k in np.flatnonzero((gap > 1) & (gap <= KHE + 1)):
            a, b = idx[k] + 1, idx[k + 1]          # ô trống [a, b)
            L = (b - a) * tp.O
            if L <= KHE_LUON:   # khe hẹp (cửa trượt / cửa xếp không có cung): luôn khép
                kq[j, a:b] = True
                continue
            if doc:   # m là ma trận chuyển vị: hàng j = cột x
                p = (x0 + (j + 0.5) * tp.O, y0 + a * tp.O); q = (p[0], y0 + b * tp.O)
            else:
                p = (x0 + a * tp.O, y0 + (j + 0.5) * tp.O); q = (x0 + b * tp.O, p[1])
            for cx, cy, r in CUNG:
                if L <= r + 150 and math.dist(p, (cx, cy)) <= r + 150 and math.dist(q, (cx, cy)) <= r + 150:
                    kq[j, a:b] = True
                    break
    return kq


tp._raster = _raster_khep
def _net_cua_dong(vc_tuong, bbox, cung, net_cua):
    """Giữ nét cửa thẳng nằm ngoài vòng quét mọi cung (cửa tủ, cửa xếp, khung cửa sổ) làm vật cản;
    bỏ cánh cửa đang mở. Lỗ cửa có cung đã khép bằng _dong_khe."""
    doan = []
    for p in net_cua:
        if not any(all(math.dist(c, q) <= math.dist(c, a) + 60 for q in p) for c, a, _ in cung):
            doan += list(zip(p, p[1:]))
    return doan


tp._dong_lo_cua = _net_cua_dong


def vung_thang_layer(blk, gian=300, dt_min=2.0):
    """Buồng thang = cụm hình bao các nét layer STAIR (gộp các hình cách nhau < gian mm)."""
    from ezdxf import bbox as _bb
    hop = []
    for e in blk:
        if e.dxf.layer != "STAIR" or e.dxftype() == "TEXT":
            continue
        b = _bb.extents([e])
        if b.has_data:
            hop.append([b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y])
    gop = True
    while gop:
        gop = False
        for i in range(len(hop)):
            for j in range(i + 1, len(hop)):
                a, b = hop[i], hop[j]
                if a[0] - gian <= b[2] and b[0] - gian <= a[2] and a[1] - gian <= b[3] and b[1] - gian <= a[3]:
                    hop[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    hop.pop(j); gop = True
                    break
            if gop:
                break
    return [tuple(h) for h in hop if (h[2] - h[0]) * (h[3] - h[1]) / 1e6 >= dt_min]


tp.vung_thang = lambda blk: []  # không khoét thang khỏi phòng lúc dò; xử lý sau


def trong_thang(dg, thang):
    """Tỷ lệ diện tích phòng nằm trong các vùng thang (xấp xỉ theo lưới 100 mm)."""
    from matplotlib.path import Path as MP
    xs, ys = [p[0] for p in dg], [p[1] for p in dg]
    gx, gy = np.meshgrid(np.arange(min(xs), max(xs), 100) + 50, np.arange(min(ys), max(ys), 100) + 50)
    pts = np.c_[gx.ravel(), gy.ravel()]
    ok = MP(dg).contains_points(pts)
    if not ok.any():
        return 0.0
    tr = np.zeros(len(pts), bool)
    for x0, y0, x1, y1 in thang:
        tr |= (pts[:, 0] >= x0) & (pts[:, 0] <= x1) & (pts[:, 1] >= y0) & (pts[:, 1] <= y1)
    return float((ok & tr).sum() / ok.sum())

doc = ezdxf.readfile("tang.dxf")
TANG = sys.argv[1:] or ["HAM", "TRET", "LUNG", "T2", "T3", "T4", "T5", "T6"]
kq = json.load(open(FILE_RA, encoding="utf-8")) if os.path.exists(FILE_RA) else {}


def x_min(e):
    t = e.dxftype()
    if t == "LINE": return min(e.dxf.start.x, e.dxf.end.x)
    if t == "LWPOLYLINE": return min(p[0] for p in e.get_points("xy"))
    if t in ("ARC", "CIRCLE"): return e.dxf.center.x
    return e.dxf.insert.x


# Mặt ngoài nhà (tường tây xiên): đóng biên chỗ cửa sổ / vách kính
NHA = [(650, -60), (15000, -60), (15000, 14560), (-60, 14560)]
BAO = {t: NHA for t in ("TRET", "LUNG", "T2", "T3", "T4", "T5", "T6")}


def qua_dai(e):
    from ezdxf import bbox
    bb = bbox.extents([e])
    return bb.has_data and max(bb.size.x, bb.size.y) > 3000


def chuan_bi(ten):
    """Tạo block dò D_<tầng> (lọc layer, bỏ phần ngoài nhà, thêm đường bao)."""
    src = doc.blocks["T_" + ten]
    bn = "D_" + ten
    if bn in doc.blocks: doc.blocks.delete_block(bn, safe=False)
    d = doc.blocks.new(bn)
    for e in src:
        if e.dxf.layer in GIU and -800 < x_min(e) < 15200:
            if e.dxf.layer in CUA and qua_dai(e):
                continue
            if e.dxftype() == "LWPOLYLINE" and any(abs(b[0]) > 1e-6 for b in e.get_points("b")):
                for v in e.virtual_entities():  # cung cửa (bán kính 0,4–1,3 m) giữ ARC; cung khác -> dây cung
                    if v.dxftype() == "ARC" and not 400 <= v.dxf.radius <= 1300:
                        v = d.add_line(v.start_point, v.end_point)
                    else:
                        d.add_entity(v)
                    v.dxf.layer = e.dxf.layer
                continue
            d.add_entity(e.copy())
    CUNG.clear()
    for e in src:
        if e.dxf.layer not in CUA or not -800 < x_min(e) < 15200:
            continue
        arcs = [e] if e.dxftype() == "ARC" else             [v for v in e.virtual_entities() if v.dxftype() == "ARC"] if e.dxftype() == "LWPOLYLINE" else []
        for a in arcs:
            if 400 <= a.dxf.radius <= 1300:
                CUNG.append((a.dxf.center.x, a.dxf.center.y, a.dxf.radius))
    if ten in BAO:  # đường bao mặt ngoài (cửa sổ/vách kính không vẽ thành tường)
        p = BAO[ten]
        for a, b in zip(p, p[1:] + p[:1]):
            d.add_line(a, b, dxfattribs={"layer": "WALL"})
    return bn, d


for ten in (TANG if __name__ == "__main__" else []):
    bn, d = chuan_bi(ten)
    ds = tp.tim_phong_trong_block(doc, bn, TUONG, CUA, dien_tich_min=0.8)
    thang = vung_thang_layer(d, gian=60)
    for p in ds:
        p["ty_le_thang"] = round(trong_thang(p["dg"], thang), 2)
    kq[ten] = {"phong": ds, "thang": thang}
    fig, ax = plt.subplots(figsize=(16, 16), dpi=70)
    doan, dac, cung, net_cua = tp._thu_hinh(d, set(TUONG), set(CUA))
    for a, b in doan:
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#888", lw=0.5)
    cm = plt.get_cmap("tab20")
    for k, p in enumerate(ds):
        x, y = zip(*(p["dg"] + p["dg"][:1]))
        ax.fill(x, y, color=cm(k % 20), alpha=0.45)
        cx, cy = sum(x[:-1]) / len(p["dg"]), sum(y[:-1]) / len(p["dg"])
        ax.text(cx, cy, f"{k}:{p['ten'][:14]}\n{p['dien_tich']}", fontsize=7, ha="center")
    for x0, y0, x1, y1 in thang:
        ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], "m--", lw=1.5)
    ax.set_aspect("equal"); ax.set_title(ten)
    fig.tight_layout(); fig.savefig(f"anh_phong{'_min' if CHI_TIET else ''}_{ten}.png"); plt.close(fig)
    print(ten, len(ds), "phòng, thang", len(thang), [ (k, p["ten"], p["dien_tich"]) for k, p in enumerate(ds)], flush=True)
if __name__ == "__main__":
    json.dump(kq, open(FILE_RA, "w", encoding="utf-8"), ensure_ascii=False)
