"""Thiết kế PCCC khách sạn YERSIN (4.MBBT): tính vị trí thiết bị 4 hệ, ghi thiet_ke.json + ảnh kiểm tra.

  python thiet_ke.py

Đầu vào: phong.json (do_phong.py), tang.dxf (lam_phang.py). Toạ độ theo tầng (mm, gốc = điểm chèn tầng);
khi vẽ cộng thêm cao độ model của tầng (TANG_Y).
Quy ước (người dùng chốt 28/10/2026): nhóm 1 cho toàn công trình, trần treo 3,2 m, khung tên để trống,
mỗi hệ một bản vẽ riêng. Không bố trí đầu báo, sprinkler trong WC và buồng thang.
"""
import json
import math
import sys
from collections import defaultdict

sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import ezdxf
import matplotlib
import numpy as np
from matplotlib.path import Path as MPath

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import ong as ONG
import rai_thiet_bi as rtb
import thuy_luc as TLU
import tim_phong as tp

TRAN = 3.2
TANG = ["HAM", "TRET", "LUNG", "T2", "T3", "T4", "T5", "T6", "T7", "SAN_THUONG"]
TEN_TANG = {"HAM": "TẦNG HẦM", "TRET": "TẦNG TRỆT", "LUNG": "TẦNG LỬNG", "T2": "TẦNG 2", "T3": "TẦNG 3",
            "T4": "TẦNG 4", "T5": "TẦNG 5", "T6": "TẦNG 6", "T7": "TẦNG 7", "SAN_THUONG": "TẦNG SÂN THƯỢNG"}
TANG_Y = {"HAM": 0, "TRET": 23440, "LUNG": 46880, "T2": 70320, "T3": 93760, "T4": 117200, "T5": 140640,
          "T6": 164080, "T7": 187520, "SAN_THUONG": 210960, "MAI": 234400}
CAO_DO = {t: 3.5 * (i - 1) for i, t in enumerate(TANG)}  # m; hầm -3,5; chiều cao tầng 3,5 m (người dùng)

THANG_CHINH = (10750, 12000, 12550, 15170)
THANG_CANH = {"HAM": (-59, 1147, 1441, 3422)}
THANG_CANH_MD = (100, 6050, 2500, 8050)
THANG_MAY = [(9620, 8220, 11120, 9970), (11370, 8220, 12870, 9970)]
BAN_CONG = (0, 18700, 3800, 20100)  # ban công góc tây bắc các tầng phòng ngủ
CAM_THEM = {"T7": [(9800, 16000, 20100, 20100)]}  # sân thượng hở tầng 7 (rãnh thoát nước): không bố trí


def vung_cam(t):
    return thang_bo(t) + THANG_MAY + CAM_THEM.get(t, [])

phong_all = json.load(open("phong.json", encoding="utf-8"))
phong_min = json.load(open("phong_min.json", encoding="utf-8"))  # dò chi tiết (khép khe <= 1 m): tách WC, buồng thang
dxf = ezdxf.readfile("tang.dxf")


def thang_bo(t):
    if t in ("SAN_THUONG",):
        return [THANG_CHINH]
    return [THANG_CHINH, THANG_CANH.get(t, THANG_CANH_MD)] if t != "HAM" else [THANG_CANH["HAM"]]


def trong(dg, p):
    return MPath(dg).contains_point(p)


def trong_hcn(p, h, gian=0):
    return h[0] - gian <= p[0] <= h[2] + gian and h[1] - gian <= p[1] <= h[3] + gian


def cach_bien(dg, p):
    return rtb.khoang_cach_tuong(p[0], p[1], dg)


def diem_trong(dg, gan, cach_min=300, buoc=100, cam=()):
    """Điểm trong phòng cách tường >= cach_min, ngoài các vùng cấm (cách >= 300 mm), gần điểm `gan` nhất."""
    xs, ys = [q[0] for q in dg], [q[1] for q in dg]
    gx, gy = np.meshgrid(np.arange(min(xs), max(xs), buoc) + buoc / 2, np.arange(min(ys), max(ys), buoc) + buoc / 2)
    pts = np.c_[gx.ravel(), gy.ravel()]
    pts = pts[MPath(dg).contains_points(pts)]
    tot = [tuple(p) for p in pts if cach_bien(dg, p) >= cach_min and not any(trong_hcn(p, h, 300) for h in cam)]
    if not tot:
        return None
    return min(tot, key=lambda p: math.dist(p, gan))


def ve_sinh(t):
    """Tâm các thiết bị vệ sinh (bồn cầu, lavabo, sen) của tầng: nhận WC."""
    from ezdxf import bbox
    tam = []
    for e in dxf.blocks["T_" + t]:
        if "SANITARY" in e.dxf.layer:
            b = bbox.extents([e])
            if b.has_data and max(b.size.x, b.size.y) < 1200:
                tam.append(((b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2))
    return tam


def phan_loai(t):
    """Gán loại cho từng phòng: thang | wc | ban_cong | be | kin | nho | phong."""
    vs = ve_sinh(t)
    kq = []
    for k, p in enumerate(phong_all[t]["phong"]):
        dg = [tuple(q) for q in p["dg"]]
        S = p["dien_tich"]
        cx = sum(q[0] for q in dg) / len(dg)
        cy = sum(q[1] for q in dg) / len(dg)
        so_vs = sum(1 for q in vs if trong(dg, q))
        ten = p["ten"]
        xs_, ys_ = [q[0] for q in dg], [q[1] for q in dg]
        w_, h_ = max(xs_) - min(xs_), max(ys_) - min(ys_)
        gon = max(w_, h_) / max(1, min(w_, h_)) <= 2.5
        if p["ty_le_thang"] > 0.6:
            loai = "thang"
        elif S < 1.0:
            loai = "nho"
        elif "BỀ NƯỚC" in ten or "BỂ NƯỚC" in ten:
            loai = "be"
        elif t == "HAM" and not ten and S > 40:
            loai = "kin"  # khối kín không cửa phía bắc tầng hầm (bể ngầm / ram): kiểm tra lại
        elif t not in ("HAM", "TRET") and trong_hcn((cx, cy), BAN_CONG) and S < 5:
            loai = "ban_cong"
        elif 0.3 < p["ty_le_thang"] <= 0.6:
            loai = "phong"  # sảnh / chiếu nghỉ thang (thiết bị nằm ngoài vùng thang)
        elif so_vs >= 2 and S <= 6 and gon:  # WC 2–4 m²; WC nằm trong phòng đã trừ ở lớp chi tiết
            loai = "wc"
        else:
            loai = "phong"
        kq.append({"k": k, "ten": ten, "dg": dg, "S": S, "loai": loai, "tam": (cx, cy), "tl_thang": p["ty_le_thang"],
                   "rong_tb": S * 1e6 / max(w_, h_)})
    # Hành lang / sảnh thoát nạn: chạm thang chính hoặc sảnh thang máy (≤ 700 mm), hoặc là sảnh thang (30–60 % trong thang)
    for r in kq:
        r["hanh_lang"] = r["loai"] == "phong" and (
            0.3 < r["tl_thang"] <= 0.6 or (r["S"] >= 3 and r["rong_tb"] <= 1800) or
            any(any(trong_hcn(q, h, 700) for q in r["dg"]) for h in thang_bo(t) if h != THANG_CANH.get("HAM")
                and h == THANG_CHINH))
    return kq


def loc_thang(diem, t):
    return [p for p in diem if not any(trong_hcn(p, h) for h in vung_cam(t))]


def rai(r, loai, nhom=None):
    tso = rtb.doc_thong_so(loai, nhom=nhom, tran=None if loai == "sprinkler" else TRAN)
    kq = rtb.tinh_phong([(x / 1000, y / 1000) for x, y in r["dg"]], tso)
    diem = [(x * 1000, y * 1000) for x, y in kq["diem"]]
    dim = [((a[0] * 1000, a[1] * 1000), (b[0] * 1000, b[1] * 1000)) for a, b in kq["dim"]]
    return diem, dim, kq["canh_bao"], tso["nguon"]


R_PHU = {"bao_khoi": 4.5 * math.sqrt(2) * 1000, "bao_nhiet": 2.5 * math.sqrt(2) * 1000}  # mm


def phu_dau_bao(r, loai, t, buoc=250, cach_tuong=500):
    """Số đầu báo ít nhất phủ kín phòng: mọi điểm mẫu cách một đầu báo <= R (khói 6,36 m, nhiệt 3,54 m;
    = nửa khoảng cách lớn nhất × √2 theo TCVN 5738), đầu báo cách tường >= 0,5 m, ngoài buồng thang."""
    dg = r["dg"]
    tso = rtb.doc_thong_so(loai, tran=TRAN)
    R = R_PHU[loai]
    xs, ys = [q[0] for q in dg], [q[1] for q in dg]
    gx, gy = np.meshgrid(np.arange(min(xs), max(xs), buoc) + buoc / 2, np.arange(min(ys), max(ys), buoc) + buoc / 2)
    pts = np.c_[gx.ravel(), gy.ravel()]
    pts = pts[MPath(dg).contains_points(pts)]
    pts = np.array([p for p in pts if not any(trong_hcn(p, h) for h in vung_cam(t))])
    if len(pts) == 0:
        return [], tso["nguon"]
    ung = np.array([p for p in pts if cach_bien(dg, p) >= cach_tuong]) if len(pts) else pts
    if len(ung) == 0:
        ung = pts
    d = np.hypot(ung[:, None, 0] - pts[None, :, 0], ung[:, None, 1] - pts[None, :, 1]) <= R
    chua = np.ones(len(pts), bool)
    chon = []
    while chua.any():
        dem = (d & chua).sum(1)
        tam = pts[chua].mean(0)
        diem = dem * 1e6 - np.hypot(ung[:, 0] - tam[0], ung[:, 1] - tam[1])
        i = int(np.argmax(diem))
        if dem[i] == 0:
            break
        chon.append(tuple(ung[i]))
        chua &= ~d[i]
    # giới hạn diện tích mỗi đầu báo
    while r["S"] / max(1, len(chon)) > tso["dien_tich_max"]:
        chon.append(tuple(ung[int(np.argmax(np.min(np.hypot(ung[:, None, 0] - np.array(chon)[None, :, 0],
                                                            ung[:, None, 1] - np.array(chon)[None, :, 1]), 1)))]))
    return chon, tso["nguon"]


def hcn_dg(h):
    return [(h[0], h[1]), (h[2], h[1]), (h[2], h[3]), (h[0], h[3])]


def vung_cam_da_giac(t):
    """Vùng không bố trí đầu phun / đầu báo: WC và buồng thang (từ lớp dò chi tiết), vùng thang,
    thang máy, vùng cấm riêng. Trả về [(loại, đa giác)]."""
    vs = ve_sinh(t)
    kq = [("thang", hcn_dg(h)) for h in thang_bo(t) + THANG_MAY] + [("cam", hcn_dg(h)) for h in CAM_THEM.get(t, [])]
    for p in phong_min.get(t, {}).get("phong", []):
        dg = [tuple(q) for q in p["dg"]]
        if p["ty_le_thang"] >= 0.5:
            kq.append(("thang", dg))
        elif p["dien_tich"] <= 6 and sum(1 for q in vs if trong(dg, q)) >= 2:  # WC công trình này 2–4 m²
            kq.append(("wc", dg))
    return kq


def tru_vung(dg, cam, S_min=1.0):
    """Phần còn lại của phòng sau khi trừ các vùng cấm (lưới tp.O mm) -> [đa giác trực giao]."""
    O = tp.O
    xs, ys = [q[0] for q in dg], [q[1] for q in dg]
    x0, y0 = min(xs) - 2 * O, min(ys) - 2 * O
    nx, ny = int((max(xs) - x0) / O) + 3, int((max(ys) - y0) / O) + 3
    gx, gy = np.meshgrid(x0 + (np.arange(nx) + 0.5) * O, y0 + (np.arange(ny) + 0.5) * O)
    pts = np.c_[gx.ravel(), gy.ravel()]
    m = MPath(dg).contains_points(pts)
    cat = False
    for _, c in cam:
        cx, cy = [q[0] for q in c], [q[1] for q in c]
        if max(cx) < min(xs) or min(cx) > max(xs) or max(cy) < min(ys) or min(cy) > max(ys):
            continue
        mc = MPath(c).contains_points(pts)
        if (m & mc).any():
            m &= ~mc
            cat = True
    if not cat:
        return [dg]
    m = m.reshape(ny, nx)
    nhan, so = tp._gan_nhan(m)
    manh = []
    for k in range(1, so + 1):
        mk = nhan == k
        if mk.sum() * O * O / 1e6 < S_min:
            continue
        d = tp._don_bac(tp._do_bien(mk, x0, y0))
        if len(d) >= 4:
            manh.append([tuple(q) for q in d])
    return manh


def mst_cap(diem):
    """Cây khung nhỏ nhất (khoảng cách Manhattan) nối các thiết bị: mỗi cạnh vẽ chữ L."""
    if len(diem) < 2:
        return []
    trong_cay, canh = {0}, []
    while len(trong_cay) < len(diem):
        i, j = min(((i, j) for i in trong_cay for j in range(len(diem)) if j not in trong_cay),
                   key=lambda ij: abs(diem[ij[0]][0] - diem[ij[1]][0]) + abs(diem[ij[0]][1] - diem[ij[1]][1]))
        trong_cay.add(j)
        a, b = diem[i], diem[j]
        canh.append([a, (b[0], a[1]), b])
    return canh


ts_all = json.loads((rtb.THU_MUC / "thong_so.json").read_text(encoding="utf-8"))
NHOM1 = ts_all["sprinkler"]["nhom"]["1"]
TL = ts_all["thuy_luc"]
TL["sprinkler"]["cao_tran_tren_san_m"] = TRAN

out = {"tang": {}, "canh_bao": [], "nguon": {}}
for t in TANG:
    R = phan_loai(t)
    CAM = vung_cam_da_giac(t)
    for r in R:
        r["manh"] = tru_vung(r["dg"], CAM) if r["loai"] == "phong" else []
    T = {"cam": CAM, "phong": R, "bc": defaultdict(list), "spr": [], "spr_dim": [], "bc_dim": [], "cap": [], "hong": [], "binh": [],
         "cs": defaultdict(list), "ong": [], "ghi_chu": []}
    ds_thang = thang_bo(t)
    # ---- điểm thoát nạn: điểm hành lang gần cửa từng thang bộ ----
    cua_thang = []
    for h in ds_thang:
        tam = ((h[0] + h[2]) / 2, (h[1] + h[3]) / 2)
        ung = [(diem_trong(r["dg"], tam, 300, cam=thang_bo(t) + THANG_MAY), r) for r in R if r["hanh_lang"]]
        ung = [(p, r) for p, r in ung if p]
        if ung:
            p, r = min(ung, key=lambda pr: math.dist(pr[0], tam))
            cua_thang.append({"thang": h, "p": p, "phong": r["k"]})
    T["cua_thang"] = cua_thang

    # ---- BÁO CHÁY ----
    for r in R:
        if r["loai"] != "phong":
            continue
        loai = "bao_nhiet" if any(k in r["ten"] for k in ("BẾP",)) else "bao_khoi"
        r["bc"], r["bc_manh"], cb = [], [], []
        for dg in r["manh"]:  # phòng đã trừ WC, buồng thang
            diem, nguon = phu_dau_bao({"dg": dg, "S": abs(rtb.dien_tich(dg)) / 1e6}, loai, t)
            T["bc"][loai] += diem
            r["bc"] += [(loai, p) for p in diem]
            r["bc_manh"].append((dg, [(loai, p) for p in diem]))
            out["nguon"][loai] = nguon
        out["canh_bao"] += [f"{TEN_TANG[t]} – báo cháy phòng {r['k']}: {c}" for c in cb]
    for c in cua_thang:
        x, y = c["p"]
        T["bc"]["nut_an"].append((x, y))
        T["bc"]["chuong_den"].append((x, y))  # vẽ lệch nhau khi chèn
    if t == "TRET":
        le_tan = next(r for r in R if "RECEPTION" in r["ten"])
        T["bc"]["tu_tt"].append(diem_trong(le_tan["dg"], (16500, 13200), 400))
        T["bc"]["den_fire"].append((20600, 14000))  # mặt ngoài cạnh sảnh chính
    dau_bc = [p for k in ("bao_khoi", "bao_nhiet") for p in T["bc"][k]] + T["bc"]["nut_an"]
    T["cap"] = mst_cap(dau_bc + T["bc"]["tu_tt"])

    # ---- SPRINKLER ----
    for r in R:
        if r["loai"] != "phong":
            continue
        r["spr"], r["S_spr"] = [], 0.0
        for dg in r["manh"]:  # phòng đã trừ WC, buồng thang
            diem, dim, cb, nguon = rai({"dg": dg}, "sprinkler", "1")
            diem = loc_thang(diem, t)
            T["spr"] += diem
            T["spr_dim"] += dim
            r["spr"] += diem
            r["S_spr"] += abs(rtb.dien_tich(dg)) / 1e6
            out["nguon"]["sprinkler"] = nguon
        out["canh_bao"] += [f"{TEN_TANG[t]} – sprinkler phòng {r['k']}: {c}" for c in cb]
    # trục đứng cạnh thang chính (hầm: cạnh khu kỹ thuật nước), ống chính theo hành lang
    if t == "HAM":
        truc, y_chinh = (3300, 11800), 11000
    elif t == "SAN_THUONG":
        truc, y_chinh = (10400, 12400), 12400
    else:
        truc, y_chinh = (10450, 11750), 11400
    T["truc"] = truc
    T["y_chinh"] = y_chinh
    T["ong_spr"] = ONG.tuyen_spr([(round(x), round(y)) for x, y in T["spr"]], truc[0], truc[1], y_chinh, sai_so=5)

    # ---- HỌNG NƯỚC + BÌNH ----
    c_chinh = next((c for c in cua_thang if c["thang"] == THANG_CHINH), cua_thang[0] if cua_thang else None)
    if t != "SAN_THUONG" and c_chinh:
        T["hong"].append(c_chinh["p"])
        T["truc_hong"] = (c_chinh["p"][0], c_chinh["p"][1])
        for c in cua_thang:
            T["binh"].append(c["p"])
    elif t == "SAN_THUONG":
        T["binh"].append((9800, 12700))

    # ---- CHIẾU SÁNG SỰ CỐ ----
    cs_ts = {"khoang_cach_max": 8.0, "cach_tuong_max": 4.0, "dien_tich_max": 1e9, "khoang_cach_min": 0.0,
             "cach_tuong_min": 0.0}
    for r in R:
        if r["loai"] != "phong":
            continue
        if r["hanh_lang"] or r["S"] >= 40:
            kq = rtb.tinh_phong([(x / 1000, y / 1000) for x, y in r["dg"]], cs_ts)
            diem = loc_thang([(x * 1000, y * 1000) for x, y in kq["diem"]], t)
            for p in diem:
                gan = min((math.dist(p, c["p"]) for c in cua_thang), default=1e9)
                (T["cs"]["exit_huong"] if gan > 6000 and r["hanh_lang"] else T["cs"]["den_su_co"]).append(p)
            if not diem:
                T["cs"]["den_su_co"].append(diem_trong(r["dg"], r["tam"], 300))
        elif r["S"] >= 6 and t not in ("HAM", "TRET"):
            hl = [q for x in R if x["hanh_lang"] for q in x["dg"]]
            if hl:
                gan = min(hl, key=lambda q: math.dist(q, r["tam"]))
                T["cs"]["sdtnp"].append(diem_trong(r["dg"], gan, 400))
    for c in cua_thang:
        x, y = c["p"]
        T["cs"]["exit"].append((x, y))
        h = c["thang"]
        T["cs"]["den_su_co"].append(((h[0] + h[2]) / 2, (h[1] + h[3]) / 2))  # đèn trong buồng thang
    if t not in ("HAM", "SAN_THUONG"):
        T["cs"]["sdtn"].append((13100, 10600))  # sơ đồ thoát nạn tầng cạnh thang máy
    T["cs"] = {k: [p for p in v if p] for k, v in T["cs"].items()}
    T["bc"] = {k: [p for p in v if p] for k, v in T["bc"].items()}
    out["tang"][t] = T
    print(t, {k: len(v) for k, v in T["bc"].items()}, "spr", len(T["spr"]), "họng", len(T["hong"]),
          "bình", len(T["binh"]), {k: len(v) for k, v in T["cs"].items()},
          "bỏ:", [(r["k"], r["loai"]) for r in R if r["loai"] != "phong"], flush=True)

# ---- THUỶ LỰC SƠ BỘ: từng tầng, lấy tầng bất lợi ----
dn_theo = ONG.dn_spr
kq_tl = []
for t in TANG:
    T = out["tang"][t]
    if not T["spr"]:
        continue
    dt_dau = {}
    for r in T["phong"]:
        for p in r.get("spr", []):
            dt_dau[(round(p[0]), round(p[1]))] = r.get("S_spr", r["S"]) / max(1, len(r["spr"]))
    mang = {"truc": list(T["truc"]), "doan": [[list(a), list(b), n, l] for a, b, n, l in T["ong_spr"]],
            "dau": [[x, y, dt_dau[(x, y)], ""] for x, y in dt_dau]}
    try:
        kq = TLU.tinh_tang_spr(mang, NHOM1, TL, dn_theo)
    except Exception as ex:
        out["canh_bao"].append(f"Thuỷ lực {TEN_TANG[t]}: {ex}")
        continue
    P, tp_ = TLU.ap_luc_bom_spr(kq, CAO_DO[t] - CAO_DO["HAM"], 15.0, TL)
    kq_tl.append((P, t, kq, tp_))
    print("thuỷ lực", t, "Q", round(kq["Q_lpm"] / 60, 2), "l/s", "P bơm", round(P, 2), "bar", flush=True)
# Bơm phải thoả mọi tầng: lưu lượng lớn nhất (tầng có vùng tính toán nhiều đầu nhất) và áp lớn nhất (tầng cao nhất)
P_spr, t_bat_loi, _, tp_bl = max(kq_tl, key=lambda x: x[0])
_, t_q_max, kq_bl, _ = max(kq_tl, key=lambda x: x[2]["Q_lpm"])
t_hong = max((t for t in TANG if out["tang"][t]["hong"]), key=lambda t: CAO_DO[t])
Q_h, P_h, tp_h = TLU.tinh_hong(CAO_DO[t_hong] - CAO_DO["HAM"], CAO_DO[t_hong] - CAO_DO["HAM"] + 3.5, 15.0, TL)
Q_spr_ls = kq_bl["Q_lpm"] / 60
Q_bom = Q_spr_ls + Q_h / 60
H_bom = max(P_spr, P_h) / TLU.G_BAR_M * TL["bom"]["he_so_du_tru_cot_ap"]
V_be = Q_spr_ls * NHOM1["thoi_gian_phut"] * 60 / 1000 + Q_h / 60 * TL["hong"]["thoi_gian_gio"] * 3600 / 1000
out["thuy_luc"] = {"tang_bat_loi": t_bat_loi, "tang_Q_max": t_q_max,
                   "tung_tang": {t: {"Q_l_s": round(k["Q_lpm"] / 60, 2), "P_bom_bar": round(P, 2)} for P, t, k, _ in kq_tl}, "Q_spr_l_s": round(Q_spr_ls, 2), "P_spr_bar": round(P_spr, 2),
                   "thanh_phan_spr": {k: round(v, 3) for k, v in tp_bl.items()},
                   "Q_hong_l_s": round(Q_h / 60, 2), "P_hong_bar": round(P_h, 2),
                   "thanh_phan_hong": {k: round(v, 3) for k, v in tp_h.items()},
                   "Q_bom_l_s": round(Q_bom, 1), "H_bom_m": math.ceil(H_bom),
                   "V_be_m3": round(V_be, 1), "V_be_chon_m3": math.ceil(V_be)}
print("BƠM", out["thuy_luc"])
json.dump(out, open("thiet_ke.json", "w", encoding="utf-8"), ensure_ascii=False, default=list)

# ---- ảnh kiểm tra: mỗi tầng một ảnh, 4 hệ chồng nhau ----
MAU = {"bao_khoi": "r", "bao_nhiet": "g", "nut_an": "lime", "chuong_den": "lime", "tu_tt": "k", "den_fire": "k"}
for t in TANG:
    T = out["tang"][t]
    fig, axs = plt.subplots(2, 2, figsize=(20, 20), dpi=60)
    for ax, he in zip(axs.flat, ("BÁO CHÁY", "SPRINKLER", "HỌNG + BÌNH", "CHIẾU SÁNG SỰ CỐ")):
        for r in T["phong"]:
            x, y = zip(*(r["dg"] + r["dg"][:1]))
            ax.fill(x, y, color={"phong": "#eef", "wc": "#fdd", "thang": "#ddd"}.get(r["loai"], "#ffd"), lw=0)
            ax.plot(x, y, color="#888", lw=0.6)
            ax.text(r["tam"][0], r["tam"][1], f"{r['k']}{'' if r['loai'] == 'phong' else ' ' + r['loai']}", fontsize=7)
        for lc, c in T["cam"]:
            x, y = zip(*(list(c) + [c[0]]))
            ax.fill(x, y, color={"wc": "#f99", "thang": "#999"}.get(lc, "#cc9"), alpha=0.5, hatch="//", lw=0)
        if he == "BÁO CHÁY":
            for k, ds in T["bc"].items():
                for p in ds:
                    ax.plot(*p, "o", color=MAU[k], ms=6)
            for c in T["cap"]:
                ax.plot([q[0] for q in c], [q[1] for q in c], "m--", lw=0.6)
        elif he == "SPRINKLER":
            for a, b, n, l in T["ong_spr"]:
                ax.plot([a[0], b[0]], [a[1], b[1]], "r-" if l != "nhanh" else "m-", lw=1.5 if l != "nhanh" else 0.7)
            for p in T["spr"]:
                ax.plot(*p, "o", mfc="none", mec="r", ms=6)
        elif he == "HỌNG + BÌNH":
            for p in T["hong"]:
                ax.plot(*p, "s", color="r", ms=10)
                ax.add_patch(plt.Circle(p, 20000, fill=False, ls="--"))
            for p in T["binh"]:
                ax.plot(p[0] + 600, p[1], "^", color="r", ms=8)
        else:
            for k, ds in T["cs"].items():
                for p in ds:
                    ax.plot(*p, {"exit": "s", "exit_huong": ">", "den_su_co": "*", "sdtnp": "D", "sdtn": "P"}[k],
                            color="g" if "exit" in k else "r", ms=8)
        ax.set_title(f"{TEN_TANG[t]} – {he}")
        ax.set_aspect("equal")
        ax.set_xlim(-1500, 21500); ax.set_ylim(-1500, 21500)
    fig.tight_layout()
    fig.savefig(f"tk_{t}.png")
    plt.close(fig)
