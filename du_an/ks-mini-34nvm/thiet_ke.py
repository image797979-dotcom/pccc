"""Thiết kế PCCC khách sạn mini 34 NVM: vị trí thiết bị 3 hệ (báo cháy, họng nước + bình, chiếu sáng sự cố),
thuỷ lực sơ bộ họng nước; ghi thiet_ke.json + ảnh kiểm tra tk_<tầng>.png.

Đầu vào: phong.json (phong_tay.py). Toạ độ theo tầng (mm, gốc = điểm chèn block 'MBBT <tầng>').
Người dùng chốt 31/10/2026: không làm sprinkler; nhóm nguy hiểm 1; trần ≤ 3,5 m toàn bộ.
Không bố trí đầu báo trong WC, buồng thang bộ, thang máy, thang xoắn.
"""
import json
import math
import sys
from collections import defaultdict

sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import matplotlib
import numpy as np
from matplotlib.path import Path as MPath

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import rai_thiet_bi as rtb
import thuy_luc as TLU

TRAN = 3.3
TANG = ["HAM", "TRET", "LUNG", "T2", "T3", "T4", "T5", "T6"]
TEN_TANG = {"HAM": "TẦNG HẦM", "TRET": "TẦNG TRỆT", "LUNG": "TẦNG LỬNG", "T2": "TẦNG 2", "T3": "TẦNG 3",
            "T4": "TẦNG 4", "T5": "TẦNG 5", "T6": "TẦNG 6"}
# cao độ sàn (m) suy từ dim mặt cắt 3,7/3,3/3,5/3,3/3,3/3,0/2,4; hầm giả thiết -3,0 (bản vẽ không có cao độ hầm)
CAO_DO = {"HAM": -3.0, "TRET": 0.0, "LUNG": 3.7, "T2": 7.0, "T3": 10.5, "T4": 13.8, "T5": 17.1, "T6": 20.1}
THANG = (6100, 11400, 8600, 14450)
# hộp họng gắn tường bắc thang máy, bên phải cửa thang máy, quay ra sảnh hành lang (lối đi chung, dễ tiếp cận);
# cùng hoành độ mọi tầng để trục đứng thẳng. Tường thang máy tầng hầm lùi về 8300.
P_HONG = {t: (8200, 8480 if t == "HAM" else 8780) for t in ("HAM", "TRET", "LUNG", "T2", "T3", "T4", "T5", "T6")}
P_BINH_NAM = (7500, 3300)       # cặp bình ở sảnh thang xoắn
R_PHU = {"bao_khoi": 4.5 * math.sqrt(2) * 1000, "bao_nhiet": 2.5 * math.sqrt(2) * 1000}

PH = json.load(open("phong.json", encoding="utf-8"))


def trong_hcn(p, h, gian=0):
    return h[0] - gian <= p[0] <= h[2] + gian and h[1] - gian <= p[1] <= h[3] + gian


def cach_bien(dg, p):
    return rtb.khoang_cach_tuong(p[0], p[1], dg)


def luoi(dg, buoc):
    xs, ys = [q[0] for q in dg], [q[1] for q in dg]
    gx, gy = np.meshgrid(np.arange(min(xs), max(xs), buoc) + buoc / 2, np.arange(min(ys), max(ys), buoc) + buoc / 2)
    pts = np.c_[gx.ravel(), gy.ravel()]
    return pts[MPath(dg).contains_points(pts)]


def diem_trong(dg, gan, cach_min=300, buoc=50):
    """Điểm trong phòng cách tường >= cach_min, gần điểm `gan` nhất."""
    tot = [tuple(p) for p in luoi(dg, buoc) if cach_bien(dg, p) >= cach_min]
    return min(tot, key=lambda p: math.dist(p, gan)) if tot else None


def phu_dau_bao(dg, loai, cam, buoc=200, cach_tuong=500):
    """Số đầu báo ít nhất phủ kín vùng: mọi điểm cách một đầu báo <= R (nửa khoảng cách lớn nhất × √2,
    TCVN 5738:2021), đầu báo cách tường >= 0,5 m, ngoài vùng cấm; không vượt diện tích tối đa mỗi đầu."""
    tso = rtb.doc_thong_so(loai, tran=TRAN)
    pts = np.array([p for p in luoi(dg, buoc) if not any(trong_hcn(p, h) for h in cam)])
    if len(pts) == 0:
        return [], tso["nguon"]
    ung = np.array([p for p in pts if cach_bien(dg, p) >= cach_tuong])
    if len(ung) == 0:
        ung = pts
    d = np.hypot(ung[:, None, 0] - pts[None, :, 0], ung[:, None, 1] - pts[None, :, 1]) <= R_PHU[loai]
    chua = np.ones(len(pts), bool)
    chon = []
    while chua.any():
        dem = (d & chua).sum(1)
        tam = pts[chua].mean(0)
        i = int(np.argmax(dem * 1e6 - np.hypot(ung[:, 0] - tam[0], ung[:, 1] - tam[1])))
        if dem[i] == 0:
            break
        chon.append(tuple(ung[i]))
        chua &= ~d[i]
    S = abs(rtb.dien_tich(dg)) / 1e6
    while S / max(1, len(chon)) > tso["dien_tich_max"]:
        xa = np.min(np.hypot(ung[:, None, 0] - np.array(chon)[None, :, 0], ung[:, None, 1] - np.array(chon)[None, :, 1]), 1)
        chon.append(tuple(ung[int(np.argmax(xa))]))
    return chon, tso["nguon"]


def mst_cap(diem):
    """Cây khung nhỏ nhất (Manhattan) nối thiết bị; mỗi cạnh vẽ chữ L."""
    if len(diem) < 2:
        return []
    trong, canh = {0}, []
    while len(trong) < len(diem):
        i, j = min(((i, j) for i in trong for j in range(len(diem)) if j not in trong),
                   key=lambda ij: abs(diem[ij[0]][0] - diem[ij[1]][0]) + abs(diem[ij[0]][1] - diem[ij[1]][1]))
        trong.add(j)
        a, b = diem[i], diem[j]
        canh.append([a, (b[0], a[1]), b])
    return canh


def tim_vung(R, p):
    return next((r for r in R if MPath(r["dg"]).contains_point(p)), None)


out = {"tang": {}, "canh_bao": [], "nguon": {}}
for t in TANG:
    R = PH[t]["phong"]
    cam = PH[t]["cam"]
    for k, r in enumerate(R):
        r["k"] = k
        xs, ys = [q[0] for q in r["dg"]], [q[1] for q in r["dg"]]
        r["tam"] = (sum(xs) / len(xs), sum(ys) / len(ys))
    HL = [r for r in R if r["loai"] == "hanh_lang"]
    T = {"phong": R, "cam": cam, "bc": defaultdict(list), "bc_manh": [], "cap": [], "hong": [], "binh": [],
         "cs": defaultdict(list)}

    # điểm hành lang trước cửa thang bộ chính (cụm nút ấn + chuông, EXIT)
    if t == "HAM":
        cua = None
    else:
        ung = [p for p in (diem_trong(r["dg"], (8350, 11150), 250) for r in (HL or R) if r["loai"] not in ("wc",)) if p]
        cua = min(ung, key=lambda p: math.dist(p, (8350, 11150)))
    T["cua_thang"] = cua

    # ---- BÁO CHÁY ----
    da_dat = defaultdict(list)   # tên phòng -> đầu báo đã đặt (mảnh lớn trước)
    for r in sorted(R, key=lambda r: -r["dien_tich"]):
        if r["loai"] == "wc":
            continue
        loai = "bao_nhiet" if r["loai"] in ("bep", "bai_xe") else "bao_khoi"
        # mảnh nhỏ (< 3 m²) của phòng đã có đầu báo: bỏ nếu đầu báo sẵn có đã phủ hết mảnh
        if r["dien_tich"] < 3 and da_dat[r["ten"]] and all(
                min(math.dist(q, p) for p in da_dat[r["ten"]]) <= R_PHU[loai] for q in luoi(r["dg"], 200)):
            continue
        diem, nguon = phu_dau_bao(r["dg"], loai, cam)
        da_dat[r["ten"]] += diem
        T["bc"][loai] += diem
        T["bc_manh"].append((r["dg"], [(loai, p) for p in diem]))
        out["nguon"][loai] = nguon
        if not diem:
            out["canh_bao"].append(f"{TEN_TANG[t]} – {r['ten']}: không đặt được đầu báo")
    if cua:
        T["bc"]["nut_an"].append(cua)
    if t == "HAM":
        T["bc"]["nut_an"].append(diem_trong(next(r["dg"] for r in R if r["loai"] == "hanh_lang"), (5500, 8000), 250))
    if t == "TRET":
        le_tan = next(r for r in R if r["ten"].startswith("RECEPTION"))
        T["bc"]["nut_an"].append(diem_trong(le_tan["dg"], (14100, 4600), 250))   # cửa chính phía đông
        T["bc"]["tu_tt"].append(diem_trong(le_tan["dg"], (12000, 450), 300))
        T["bc"]["den_fire"].append((15400, 4700))                                 # mặt ngoài cạnh cửa chính
    T["bc"]["chuong_den"] = list(T["bc"]["nut_an"])
    T["cap"] = mst_cap([p for k in ("bao_khoi", "bao_nhiet", "nut_an", "tu_tt") for p in T["bc"][k]])

    # ---- HỌNG NƯỚC + BÌNH ----
    T["hong"].append(P_HONG[t])
    if t in ("TRET", "LUNG", "T2", "T3", "T4"):
        T["binh"].append(P_BINH_NAM)
    if t == "HAM":
        T["binh"] += [(9300, 6200), (12500, 13600)]          # phòng kỹ thuật, cuối bãi xe
    if t == "TRET":
        T["binh"].append((13700, 4600))                       # sảnh cửa chính
    if t in ("T5", "T6"):
        bep = next(r for r in R if r["loai"] == "bep")
        T["binh"].append(diem_trong(bep["dg"], (1500, 5300) if t == "T5" else (1200, 9500), 300))

    # ---- CHIẾU SÁNG SỰ CỐ ----
    cs_ts = {"khoang_cach_max": 8.0, "cach_tuong_max": 4.0, "dien_tich_max": 1e9, "khoang_cach_min": 0.0,
             "cach_tuong_min": 0.0}
    for r in R:
        if r["loai"] in ("hanh_lang", "bai_xe") or (r["loai"] == "phong" and r["dien_tich"] >= 25 and t == "TRET"):
            kq = rtb.tinh_phong([(x / 1000, y / 1000) for x, y in r["dg"]], cs_ts)
            diem = [(x * 1000, y * 1000) for x, y in kq["diem"]]
            diem = [p for p in diem if not any(trong_hcn(p, h, 200) for h in cam)] or [diem_trong(r["dg"], r["tam"], 300)]
            T["cs"]["den_su_co"] += diem
        elif r["loai"] in ("phong", "bep") and t not in ("HAM", "TRET") and r["dien_tich"] >= 6 \
                and r["ten"].startswith(("PHÒNG", "BẾP")):
            gan = min((q for h in HL for q in h["dg"]), key=lambda q: math.dist(q, r["tam"]), default=r["tam"])
            T["cs"]["sdtnp"].append(diem_trong(r["dg"], gan, 400))
    if cua:
        T["cs"]["exit"].append((cua[0], cua[1]))
        T["cs"]["den_su_co"].append(((THANG[0] + THANG[2]) / 2, (THANG[1] + THANG[3]) / 2))   # trong buồng thang
        T["cs"]["sdtn"].append(diem_trong(next((r["dg"] for r in HL), R[0]["dg"]), (6000, 9300), 250))
    if t == "TRET":
        T["cs"]["exit"] += [(14150, 2600)]                    # cửa chính phía đông
        T["cs"]["exit_huong"] += [(11000, 3200), (11000, 9000)]
    if t == "HAM":
        T["cs"]["exit"].append((7700, 12800))                 # lối lên ram dốc
        T["cs"]["exit_huong"] += [(3500, 11000), (5500, 7000)]
        T["cs"]["sdtn"].append((5500, 6200))
    T["cs"] = {k: [p for p in v if p] for k, v in T["cs"].items()}
    T["bc"] = {k: [p for p in v if p] for k, v in T["bc"].items()}
    out["tang"][t] = T
    print(t, {k: len(v) for k, v in T["bc"].items()}, "họng", len(T["hong"]), "cặp bình", len(T["hong"]) + len(T["binh"]),
          {k: len(v) for k, v in T["cs"].items()}, flush=True)

# ---- THUỶ LỰC SƠ BỘ HỌNG NƯỚC: bơm đặt phòng kỹ thuật tầng hầm, hộp họng cao nhất tầng 6 ----
ts_all = json.loads((rtb.THU_MUC / "thong_so.json").read_text(encoding="utf-8"))
TL = ts_all["thuy_luc"]
cao = CAO_DO["T6"] - CAO_DO["HAM"]
Q_h, P_h, tp_h = TLU.tinh_hong(cao, cao + TL["hong"]["tam_van_tren_san_m"], 15.0, TL)
H_bom = P_h / TLU.G_BAR_M * TL["bom"]["he_so_du_tru_cot_ap"]
V_be = Q_h / 60 * TL["hong"]["thoi_gian_gio"] * 3600 / 1000
out["thuy_luc"] = {"Q_hong_l_s": round(Q_h / 60, 2), "P_hong_bar": round(P_h, 2),
                   "thanh_phan_hong": {k: round(v, 3) for k, v in tp_h.items()},
                   "Q_bom_l_s": round(Q_h / 60, 1), "H_bom_m": math.ceil(H_bom),
                   "V_be_m3": round(V_be, 1), "V_be_chon_m3": math.ceil(V_be)}
print("BƠM", out["thuy_luc"])
json.dump(out, open("thiet_ke.json", "w", encoding="utf-8"), ensure_ascii=False, default=list)

# ---- ảnh kiểm tra ----
MAU = {"bao_khoi": "r", "bao_nhiet": "g", "nut_an": "lime", "chuong_den": "lime", "tu_tt": "k", "den_fire": "k"}
for t in TANG:
    T = out["tang"][t]
    fig, axs = plt.subplots(1, 3, figsize=(30, 10), dpi=55)
    for ax, he in zip(axs, ("BÁO CHÁY", "HỌNG + BÌNH", "CHIẾU SÁNG SỰ CỐ")):
        for r in T["phong"]:
            x, y = zip(*(r["dg"] + r["dg"][:1]))
            ax.fill(x, y, color="#fdd" if r["loai"] == "wc" else "#eef", lw=0)
            ax.plot(x, y, color="#888", lw=0.6)
            ax.text(*r["tam"], r["ten"][:14], fontsize=7)
        for h in T["cam"]:
            ax.fill([h[0], h[2], h[2], h[0]], [h[1], h[1], h[3], h[3]], color="#999", alpha=0.4)
        if he == "BÁO CHÁY":
            for k, ds in T["bc"].items():
                for p in ds:
                    ax.plot(*p, "o", color=MAU[k], ms=7)
            for c in T["cap"]:
                ax.plot([q[0] for q in c], [q[1] for q in c], "m--", lw=0.6)
        elif he == "HỌNG + BÌNH":
            for p in T["hong"]:
                ax.plot(*p, "s", color="r", ms=10)
                ax.add_patch(plt.Circle(p, 20000, fill=False, ls="--"))
            for p in T["binh"]:
                ax.plot(*p, "^", color="r", ms=8)
        else:
            for k, ds in T["cs"].items():
                for p in ds:
                    ax.plot(*p, {"exit": "s", "exit_huong": ">", "den_su_co": "*", "sdtnp": "D", "sdtn": "P"}[k],
                            color="g" if "exit" in k else "r", ms=9)
        ax.set_title(f"{TEN_TANG[t]} – {he}"); ax.set_aspect("equal")
        ax.set_xlim(-500, 16000); ax.set_ylim(-500, 15000)
    fig.tight_layout(); fig.savefig(f"tk_{t}.png"); plt.close(fig)
