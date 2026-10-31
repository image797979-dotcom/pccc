"""Khai báo phòng từng tầng bằng tay (đọc từ ảnh sach_<tầng>.png), bắt dính mép vào mặt tường thật, ghi phong.json
và ảnh kiểm tra anh_phong_<tầng>.png.

Vách ngăn của bản vẽ này vẽ không liền nét và rèm cửa nằm trên layer DOOR, nên tim_phong dò không ra phòng.
Mỗi phòng = hợp các hình chữ nhật (x0, y0, x1, y1) trừ các hình chữ nhật WC / thang (toạ độ tầng, mm).
loai: phong | hanh_lang | bep | kho | ky_thuat | bai_xe | (wc, thang, tm, san: không bố trí thiết bị).
"""
import json
import sys

import ezdxf
import matplotlib
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

matplotlib.use("Agg")
import matplotlib.pyplot as plt

TUONG = {"WALL", "7. BO - WALL", "COLUMS"}

THANG = (6100, 11400, 8600, 14450)       # thang bộ chính (hầm không có)
TM = (6100, 5600, 8600, 8600)            # thang máy
XOAN = (5650, 150, 9350, 2450)           # thang xoắn (trệt - tầng 4)

WC_NW = (4250, 12250, 6050, 14450)
WC_WM = (1400, 8500, 4600, 9950)         # lửng, tầng 2-3
WC_WM2 = (4900, 5650, 6100, 7900)        # tầng 4-6 (phòng tây giữa mở rộng tới thang máy)
WC_SW = (1900, 3950, 4600, 5500)
WC_NE = (8650, 12250, 10400, 14450)
WC_EM = (8650, 5650, 9950, 8050)
WC_SE = (7600, 3950, 9400, 5500)

P_NW = [(400, 10100, 5650, 14400)]
P_WM = [(500, 5700, 4600, 9950)]
P_WM2 = [(500, 5700, 6100, 9950)]
P_SW = [(800, 200, 4600, 3950), (4600, 200, 5600, 2700), (800, 3950, 1900, 5450)]
P_NE = [(9150, 10100, 14400, 14400)]
P_EM = [(9950, 5700, 14400, 8050), (9150, 8050, 14400, 9950)]
P_SE = [(9450, 200, 14400, 5450)]
HL_GIUA = [(4650, 5650, 6100, 9950), (5650, 8600, 9150, 11400)]
HL_NAM = [(5600, 200, 9400, 3950), (4600, 2700, 5600, 3950), (4600, 3950, 7600, 5450)]

# (tên, loại, [hcn cộng], [hcn trừ])
P = {
    "HAM": [
        ("BÃI XE", "bai_xe", [(450, 8350, 14000, 14250)], [(8650, 5700, 14000, 11300)]),
        ("KHO", "kho", [(550, 5700, 4950, 8300)], []),
        ("PHÒNG KỸ THUẬT (TỦ ĐIỆN, BỒN NƯỚC)", "ky_thuat", [(8650, 5700, 14000, 11300)], []),
        ("SẢNH THANG MÁY", "hanh_lang", [(4950, 5700, 6100, 8300)], []),
    ],
    "TRET": [
        ("KHO COFFEE", "kho", [(400, 10200, 4250, 14400)], []),
        ("WC", "wc", [(4300, 11450, 5300, 14400)], []),
        ("SHARED KITCHEN", "bep", [(500, 5700, 6100, 10150), (4250, 10150, 6100, 11450)], []),
        ("COFFEE SHOP", "phong", [(8600, 5700, 14250, 11550), (6100, 8600, 8600, 11400)], []),
        ("RAM DỐC XUỐNG HẦM", "phong", [(8650, 11600, 14250, 14400)], []),
        ("CO-WORKING", "phong", [(1950, 200, 5600, 5450), (800, 2000, 1950, 3100), (800, 4000, 1950, 5450)], []),
        ("WC", "wc", [(800, 200, 1950, 2000)], []),
        ("KHO", "kho", [(5650, 4000, 9400, 5450)], []),
        ("RECEPTION + CVS", "phong", [(5600, 200, 14400, 4000), (9400, 4000, 14400, 5450)], [XOAN]),
    ],
    "LUNG": [
        ("PHÒNG M02 (1A)", "phong", P_NW, [WC_NW]),
        ("PHÒNG M01 (1B)", "phong", P_WM, [WC_WM]),
        ("PHÒNG M01 (4C)", "phong", P_SW, [WC_SW]),
        ("PHÒNG M03", "phong", P_NE, [WC_NE]),
        ("PHÒNG M04", "phong", P_EM, [WC_EM]),
        ("KHO", "kho", [(8100, 4000, 9400, 5450)], []),
        ("HÀNH LANG", "hanh_lang", HL_GIUA, []),
        ("SẢNH LỬNG", "hanh_lang", [(5600, 200, 9450, 3950), (4600, 2700, 5600, 3950), (4600, 3950, 8100, 5450),
                                    (9450, 4150, 14300, 5450)], [XOAN]),
    ],
    "T2": [
        ("PHÒNG 202 (1A)", "phong", P_NW, [WC_NW]),
        ("PHÒNG 201 (1B)", "phong", P_WM, [WC_WM]),
        ("PHÒNG 201 (4A)", "phong", P_SW, [WC_SW]),
        ("PHÒNG 203", "phong", P_NE, [WC_NE]),
        ("PHÒNG 204", "phong", P_EM, [WC_EM]),
        ("PHÒNG 202 (4B)", "phong", P_SE, []),
        ("HÀNH LANG", "hanh_lang", HL_GIUA + HL_NAM, [XOAN, WC_SE]),
    ],
    "T4": [
        ("PHÒNG 1A", "phong", P_NW, [WC_NW]),
        ("PHÒNG 1B", "phong", P_WM2, [WC_WM2]),
        ("PHÒNG 5A", "phong", [(800, 200, 5600, 3500), (800, 3500, 3400, 5450)], [(1900, 3950, 3400, 5500)]),
        ("PHÒNG 1A (ĐÔNG BẮC)", "phong", P_NE, [WC_NE]),
        ("PHÒNG 1B (ĐÔNG)", "phong", P_EM, [WC_EM]),
        ("KHO", "kho", [(5700, 4000, 8700, 5450)], []),
        ("HÀNH LANG", "hanh_lang", [(6100, 8600, 9150, 11400), (5650, 9950, 6100, 11400)], []),
        ("SẢNH THANG XOẮN", "hanh_lang", [(5700, 200, 9400, 3950)], [XOAN]),
    ],
    "T5": [
        ("PHÒNG 1A", "phong", P_NW, [WC_NW]),
        ("PHÒNG 1B", "phong", P_WM2, [WC_WM2]),
        ("BẾP (5B)", "bep", [(800, 200, 5600, 5450)], [(2900, 2950, 5650, 4450), (2900, 4450, 4800, 5500)]),
        ("LAUNDRY", "phong", [(8650, 7050, 10650, 11000)], []),
        ("WC", "wc", [(8650, 5700, 10650, 7000)], []),
        ("HÀNH LANG", "hanh_lang", [(6100, 8600, 8600, 11400), (5650, 9950, 6100, 11400)], []),
    ],
    "T6": [
        ("PHÒNG 1C + BẾP", "bep", [(500, 5700, 6100, 9950)], [(4300, 5650, 6100, 7900)]),
        ("SẢNH THANG", "hanh_lang", [(6100, 8600, 8600, 11000), (5650, 9950, 6100, 11000)], []),
    ],
}
P["T3"] = P["T2"]
# vùng không bố trí thiết bị (ngoài WC đã trừ): buồng thang bộ, thang máy, thang xoắn
CAM = {t: [THANG, TM] + ([XOAN] if t in ("TRET", "LUNG", "T2", "T3", "T4") else []) for t in P}
CAM["HAM"] = [(6100, 5600, 8600, 8300)]
TANG = ["HAM", "TRET", "LUNG", "T2", "T3", "T4", "T5", "T6"]
NHA = {t: (0, 0, 14900, 14500) for t in TANG}


def mat_tuong(blk):
    """Đoạn tường thẳng đứng [(x, y0, y1)] và nằm ngang [(y, x0, x1)]."""
    dung, ngang = [], []
    for e in blk:
        if e.dxf.layer not in TUONG:
            continue
        if e.dxftype() == "LINE":
            seg = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))]
        elif e.dxftype() == "LWPOLYLINE":
            p = [tuple(v[:2]) for v in e.get_points("xy")]
            seg = list(zip(p, p[1:] + ([p[0]] if e.closed else [])))
        else:
            continue
        for (x0, y0), (x1, y1) in seg:
            if abs(x0 - x1) < 5 and abs(y0 - y1) > 100:
                dung.append((x0, min(y0, y1), max(y0, y1)))
            elif abs(y0 - y1) < 5 and abs(x0 - x1) > 100:
                ngang.append((y0, min(x0, x1), max(x0, x1)))
    return dung, ngang


def bat_dinh(v, a, b, ds, gian=180):
    """Toạ độ v -> mặt tường gần nhất trong `gian` mm (đoạn tường phủ >= 300 mm của khoảng a..b)."""
    ung = [c for c, s0, s1 in ds if abs(c - v) <= gian and min(b, s1) - max(a, s0) >= 300]
    return min(ung, key=lambda c: abs(c - v)) if ung else v


def hcn_bd(h, dung, ngang):
    x0, y0, x1, y1 = h
    return (bat_dinh(x0, y0, y1, dung), bat_dinh(y0, x0, x1, ngang), bat_dinh(x1, y0, y1, dung), bat_dinh(y1, x0, x1, ngang))


def da_giac(geom):
    """Shapely -> [đa giác ngoài] (bỏ lỗ: phòng ở đây không có lỗ)."""
    gs = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    return [[(round(x), round(y)) for x, y in list(g.exterior.coords)[:-1]] for g in gs if g.area > 0.3e6]


if __name__ == "__main__":
    doc = ezdxf.readfile("tang.dxf")
    kq = {}
    for t in sys.argv[1:] or TANG:
        dung, ngang = mat_tuong(doc.blocks["T_" + t])
        ds = []
        for ten, loai, cong, tru in P[t]:
            g = unary_union([box(*hcn_bd(h, dung, ngang)) for h in cong])
            for h in tru + (CAM[t] if loai not in ("wc",) else []):
                g = g.difference(box(*h))
            g = g.buffer(1, join_style=2).buffer(-1, join_style=2)  # gộp khe < 2 mm giữa các hcn
            for dg in da_giac(g):
                ds.append({"ten": ten, "loai": loai, "dg": dg, "dien_tich": round(Polygon(dg).area / 1e6, 2)})
        kq[t] = {"phong": ds, "cam": CAM[t]}
        fig, ax = plt.subplots(figsize=(14, 14), dpi=70)
        for x, y0, y1 in dung:
            ax.plot([x, x], [y0, y1], color="#999", lw=0.6)
        for y, x0, x1 in ngang:
            ax.plot([x0, x1], [y, y], color="#999", lw=0.6)
        cm = plt.get_cmap("tab20")
        for k, p in enumerate(ds):
            x, y = zip(*(p["dg"] + p["dg"][:1]))
            ax.fill(x, y, color=cm(k % 20), alpha=0.45 if p["loai"] != "wc" else 0.15)
            ax.text(sum(x[:-1]) / len(p["dg"]), sum(y[:-1]) / len(p["dg"]), f"{k}:{p['ten'][:16]}\n{p['dien_tich']}",
                    fontsize=7, ha="center")
        for h in CAM[t]:
            ax.plot([h[0], h[2], h[2], h[0], h[0]], [h[1], h[1], h[3], h[3], h[1]], "m--")
        ax.set_aspect("equal"); ax.set_xlim(-500, 15500); ax.set_ylim(-500, 15000); ax.set_title(t)
        fig.tight_layout(); fig.savefig(f"anh_phong_{t}.png"); plt.close(fig)
        print(t, [(p["ten"], p["dien_tich"]) for p in ds], flush=True)
    json.dump(kq, open("phong.json", "w", encoding="utf-8"), ensure_ascii=False)
