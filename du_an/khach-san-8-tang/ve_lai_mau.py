"""Dựng lại bộ bản vẽ PCCC khách sạn 8 tầng trong AutoCAD theo hồ sơ mẫu (KS 32 Dã Tượng).

  python ve_lai_mau.py <thư mục scripts skill> du_lieu.json phong_all.json [to ...]

- Bản vẽ đang mở trong AutoCAD phải là bản sao bản vẽ hiện trạng (có block tầng 1, 2, 3, 7, tum).
- du_lieu.json: vị trí thiết bị, ống, cáp trích từ PDF mẫu (toạ độ mm, gốc giao trục 1/A).
- Vẽ qua COM bằng ky_hieu / trinh_bay (acad_msp.MSP), người dùng thấy từng tờ hiện ra.
- Bộ tờ mới đặt ở vùng trống phía dưới bản vẽ cũ; không xoá gì của bản vẽ cũ.
- `to`: chỉ dựng các tờ có tên trong danh sách (ví dụ bc-1 cc-3-6); bỏ trống = dựng tất cả.
"""
import json
import math
import sys

sys.path.insert(0, sys.argv[1])
import acad_com as ac
import acad_msp
import ky_hieu as kh
import trinh_bay as tb

DL = json.load(open(sys.argv[2], encoding="utf-8"))
PHONG = json.load(open(sys.argv[3], encoding="utf-8"))
CHON = set(sys.argv[4:])
TL = 125
S = TL                       # mm giấy -> mm model
kh.TY_LE = TL
W_TO, H_TO = 420 * S, 297 * S
X0, Y0 = -200000, -330000    # góc dưới-trái tờ đầu tiên (vùng trống dưới bản vẽ cũ)
GOC_MB = (92.4 * S, 129.6 * S)  # vị trí giao trục 1/A trên tờ (đo từ PDF mẫu)

# block tầng: trục 1 và trục A (toạ độ block) đọc từ layer DLC-TRUC
BLOCK = {"1": ("1", 327440, 94177), "2": ("2", 330241, 52461), "3-6": ("3", 332100, 23676),
         "7-8": ("7", 477440, -53433), "tum": ("tum", 340826, -93983)}
PHONG_KEY = {"1": "1", "2": "2", "3-6": "3", "7-8": "7", "tum": "tum"}
TEN = {"1": "MẶT BẰNG TẦNG 1", "2": "MẶT BẰNG TẦNG 2", "3-6": "MẶT BẰNG TẦNG 3-6",
       "7-8": "MẶT BẰNG TẦNG 7-8 ( NHÀ Ở RIÊNG LẺ)", "tum": "MẶT BẰNG TẦNG TUM"}
TT = {"phat_hanh": "Thiết kế sơ bộ", "cong_ty": ["CÔNG TY TNHH", "MTV CƠ ĐIỆN", "THỊNH PHÁT"],
      "dia_chi_cty": "AD: 8/8 Nguyễn Đình Khơi, Phường 8, Q.Tân Bình", "mst": "0317979017",
      "giam_doc": "DƯƠNG THỊ THANH XUÂN", "chu_tri": "Bùi Mạnh Cường", "thiet_ke": "Nguyễn Thanh Thế",
      "du_an": "KHÁCH SẠN KẾT HỢP NHÀ Ở", "dia_chi": "32 Dã Tượng, Phường Vũng Tàu, Hồ Chí Minh",
      "ngay": "....../10/2026"}

acad = ac.ket_noi()
doc = ac.goi_lai(lambda: acad.ActiveDocument)
assert "KS32_PCCC_DUNG_LAI" in doc.Name, doc.Name
print("Nạp thư viện ký hiệu PCCC...", flush=True)
doc = acad_msp.nap_thu_vien(doc, TL, layer_them=[("PCCC-AN", 7)], acad=acad)
msp = acad_msp.MSP(doc)


def nen_kien_truc():
    """Ẩn tên hình có sẵn trong block tầng, chuyển nền kiến trúc sang xám mảnh như bản mẫu."""
    for b, _, _ in BLOCK.values():
        blk = ac.goi_lai(lambda: doc.Blocks.Item(b))
        for i in range(ac.goi_lai(lambda: blk.Count)):
            e = ac.goi_lai(lambda: blk.Item(i))
            if ac.goi_lai(lambda: e.ObjectName) in ("AcDbText", "AcDbMText"):
                if "MẶT BẰNG" in ac.goi_lai(lambda: e.TextString).upper():
                    ac.goi_lai(lambda: setattr(e, "Layer", "PCCC-AN"))
    la = ac.goi_lai(lambda: doc.Layers.Item("PCCC-AN"))
    ac.goi_lai(lambda: setattr(la, "Freeze", True))
    for i in range(ac.goi_lai(lambda: doc.Layers.Count)):
        la = ac.goi_lai(lambda: doc.Layers.Item(i))
        ten = ac.goi_lai(lambda: la.Name).upper()
        if ten.startswith("PCCC") or ten in ("0", "DEFPOINTS"):
            continue
        ac.goi_lai(lambda: setattr(la, "Color", 8))


def goc_to(hang, cot):
    return (X0 + cot * (W_TO + 5000), Y0 - hang * (H_TO + 5000))


def chuyen(G):
    """Hàm đổi toạ độ (gốc trục 1/A, mm) -> model trên tờ có góc G."""
    P = (G[0] + GOC_MB[0], G[1] + GOC_MB[1])
    return P, (lambda q: (P[0] + q[0], P[1] + q[1]))


def chen_tang(tang, P):
    b, gx0, gy0 = BLOCK[tang]
    msp.add_blockref(b, (P[0] - gx0, P[1] - gy0), dxfattribs={"layer": "0"})
    # phòng (toạ độ block) -> model
    return [dict(p, dg=[(x - gx0 + P[0], y - gy0 + P[1]) for x, y in p["dg"]]) for p in PHONG[PHONG_KEY[tang]]]


def phong_chua(phong, q):
    for p in phong:
        if tb._trong(p["dg"], *q):
            return p
    return None


def chu_tu_pdf(spans, M, bo_so=True):
    for s in spans:
        if bo_so and s["t"].replace(".", "").isdigit():
            continue
        tb._chu(msp, s["t"], M(s["p"]), s["co"], "MIDDLE_CENTER")


def khung(G, so_to, tieu_de=None):
    vung = tb.khung_a3(msp, G, TL, dict(TT, so_to=so_to))
    if tieu_de:
        tb.tieu_de_to(msp, tieu_de, (G[0] + GOC_MB[0] + 12500, G[1] + GOC_MB[1] - 6200))
    return vung


def to_bao_chay(tang, G, so_to):
    d = DL[tang]["bao_chay"]
    vung = khung(G, so_to, TEN[tang])
    P, M = chuyen(G)
    phong = chen_tang(tang, P)
    for loai in ("bao_khoi", "bao_nhiet", "nut_an", "chuong_den", "den_phong", "den_fire", "tu_tt"):
        for q in d.get(loai, []):
            kh.chen(msp, loai, M(q))
    for a, b in d["cap"]:
        msp.add_line(M(a), M(b), dxfattribs={"layer": kh.LAYER_CAP_BC[0], "ltscale": 30})
    # dim đầu báo theo từng phòng (hàng ≥ 3 đầu báo / hành lang: chuỗi; còn lại: 2 vuông góc + 1 chéo ≤ 7,2/5,1 m)
    theo_phong = {}
    for loai_db in ("bao_khoi", "bao_nhiet"):
        for q in d[loai_db]:
            m = M(q)
            p = phong_chua(phong, m)
            if p:
                theo_phong.setdefault(id(p), (p, []))[1].append((loai_db, m))
    for p, ds in theo_phong.values():
        tb.dim_bao_chay_phong(msp, p["dg"], ds)
    chu_tu_pdf(d["ghi_chu"], M)
    tb.ghi_chu(msp, (vung[0] + 10 * S, vung[3] - 10 * S), tb.GHI_CHU_BAO_CHAY)
    kh.ve_bang(msp, (vung[0] + 4 * S, vung[1] + 4 * S),
               ["bao_khoi", "bao_nhiet", "nut_an", "chuong_den", "tu_tt", "den_fire", "den_phong"], co_cap=True)
    b = tb.hop_ghi_chu(msp, (vung[2] - 112 * S, vung[1] + 2 * S), tb.GHI_CHU_CHUNG, 110)
    tb.hop_ghi_chu(msp, (vung[2] - 85 * S, b[3] + 1 * S), tb.GHI_CHU_TC_BAO_CHAY, 83)


def to_chua_chay(tang, G, so_to):
    d = DL[tang]["chua_chay"]
    vung = khung(G, so_to, TEN[tang])
    P, M = chuyen(G)
    chen_tang(tang, P)
    dau = d["sprinkler"]
    for q in dau:
        kh.chen(msp, "sprinkler", M(q))
    chinh = [o for o in d["ong"] if o["dn"] >= 50 and not o.get("dung")]
    for o in sorted(d["ong"], key=lambda o: -o["dn"]):
        a, b = o["diem"]
        if math.dist(a, b) < 300:
            continue
        kh.ve_ong(msp, [M(a), M(b)], "spr", o["dn"], ghi_dn=math.dist(a, b) > 900)
    # họng + 2 bình cạnh hộp, cụm bình riêng, vòng bán kính phục vụ 20 m
    for f in d["hong"]:
        c = (f[0] - 1.6 * S, f[1] + 0.6 * S)
        kh.chen(msp, "hong", M(c))
        kh.chen(msp, "binh_co2", M((c[0] - 5.0 * S, c[1])))
        kh.chen(msp, "binh", M((c[0] - 7.8 * S, c[1])))
        tb.vong_phuc_vu(msp, M(c), 20000).dxf.ltscale = 60
    for c in d["cum_binh"]:
        kh.chen(msp, "binh", M((c[0] - 1.4 * S, c[1])))
        kh.chen(msp, "binh_co2", M((c[0] + 1.4 * S, c[1])))
    if tang == "1":
        kh.chen(msp, "tu_dung_cu", M((10450, 2830)))
        for x, ten in ((-650, "HỌNG TIẾP NƯỚC 2 CỬA DN65"), (-200, "HỌNG LẤY NƯỚC 2 CỬA DN65")):
            kh.chen(msp, "hong_tiep", M((x, 450)))
    # --- dim kiểu bản mẫu ---
    truc_x = [M((x, 0))[0] for x in range(0, 25001, 5000)]
    y_chinh = chinh[0]["diem"][0][1] if chinh else 4500
    tren = [q for q in dau if q[1] > y_chinh + 600]
    hl = [q for q in dau if abs(q[1] - y_chinh) <= 600]
    duoi = [q for q in dau if q[1] < y_chinh - 600]
    if tren:
        tb.dim_theo_truc(msp, truc_x, [M(q)[0] for q in tren], M((0, 10650))[1])
        tb.dim_theo_truc(msp, [M((0, 4000))[1], M((0, 10000))[1]], [M(q)[1] for q in tren],
                         M((25650, 0))[0], ngang=False)
    if duoi:
        tb.dim_theo_truc(msp, truc_x, [M(q)[0] for q in duoi], M((0, -2750))[1])
        tb.dim_theo_truc(msp, [M((0, 0))[1], M((0, 4000))[1]], [M(q)[1] for q in duoi],
                         M((-550, 0))[0], ngang=False)
    if len(hl) >= 2:
        y = sum(q[1] for q in hl) / len(hl)
        tb.dim_chuoi(msp, [M((0, 0))[0], M((25000, 0))[0]] + [M(q)[0] for q in hl], M((0, y))[1], M((0, y))[1])
    chu_tu_pdf(d["ghi_chu"], M)
    kh.ve_bang(msp, (vung[0] + 4 * S, vung[1] + 4 * S),
               ["sprinkler", "hong", "binh_co2", "binh", "tu_dung_cu"] + (["hong_tiep"] if tang == "1" else []),
               ong=("spr",), rong_mm=95.6)
    tb.bang_binh(msp, (vung[2] - 206 * S, vung[1] + 38 * S), [("Tầng " + tang, 250, 4)])


def to_chieu_sang(tang, G, so_to):
    d = DL[tang]["chieu_sang"]
    vung = khung(G, so_to, TEN[tang])
    P, M = chuyen(G)
    chen_tang(tang, P)
    for e in d["exit"]:
        kh.chen(msp, "exit_huong" if e["huong"] else "exit", M(e["p"]), goc=e["goc"])
    for q in d["sdtnp"]:
        kh.chen(msp, "sdtnp", M(q))
    for c in d["mat_na"]:
        g = min(d["sdtnp"], key=lambda q: math.dist(q, c)) if d["sdtnp"] else c
        kh.chen(msp, "mat_na", M((2 * c[0] - g[0], 2 * c[1] - g[1])))
    for q in d["den_su_co"]:
        kh.chen(msp, "den_su_co", M(q))
    for q in d["sdtn"]:
        kh.chen(msp, "sdtn", M(q))
    kh.ve_bang(msp, (vung[0] + 4 * S, vung[1] + 4 * S),
               ["exit", "exit_huong", "den_su_co", "mat_na", "sdtn", "sdtnp"], tieu_de="LEGEND : GHI CHÚ", rong_mm=70)
    tb.hop_ghi_chu(msp, (vung[2] - 152 * S, vung[1] + 2 * S), tb.GHI_CHU_CHIEU_SANG, 150, co=2.3, vien_mau=7)


def to_bia(G):
    for (a, b, c, d_), day in (((0, 0, 420, 297), None), ((5, 4, 415, 293), 70)):
        p = msp.add_lwpolyline([(G[0] + a * S, G[1] + b * S), (G[0] + c * S, G[1] + b * S), (G[0] + c * S, G[1] + d_ * S),
                                (G[0] + a * S, G[1] + d_ * S)], close=True, dxfattribs={"layer": tb.LAYER_KHUNG[0]})
        if day:
            p.dxf.lineweight = day
    cx = G[0] + 210 * S
    for y, s, co in [(270, "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", 4.5), (262, "Độc lập - Tự do - Hạnh phúc", 4.5),
                     (225, "HỒ SƠ XIN PHÉP THẨM ĐỊNH", 9), (210, "VỀ PHÒNG CHÁY CHỮA CHÁY", 9),
                     (20, "TP. HỒ CHÍ MINH - 10/2026", 3.5)]:
        tb._chu(msp, s, (cx, G[1] + y * S), co, "MIDDLE_CENTER")
    for y, s in [(185, "CÔNG TRÌNH :  KHÁCH SẠN KẾT HỢP NHÀ Ở"),
                 (172, "ĐỊA CHỈ :  32 DÃ TƯỢNG, PHƯỜNG VŨNG TÀU, TP. HỒ CHÍ MINH"),
                 (159, "ĐẠI DIỆN CHỦ ĐẦU TƯ : ÔNG NGUYỄN DUY HỮU NAM"),
                 (146, "ĐƠN VỊ TƯ VẤN THIẾT KẾ: CÔNG TY TNHH MTV CƠ ĐIỆN THỊNH PHÁT")]:
        tb._chu(msp, s, (G[0] + 75 * S, G[1] + y * S), 5)
    tb._chu(msp, "CHỦ ĐẦU TƯ", (G[0] + 110 * S, G[1] + 120 * S), 5, "MIDDLE_CENTER")
    tb._chu(msp, "ĐƠN VỊ TƯ VẤN THIẾT KẾ", (G[0] + 315 * S, G[1] + 120 * S), 5, "MIDDLE_CENTER")


def to_quy_mo(G):
    vung = khung(G, "KT-01")
    tang = [("Tầng 1", "KHU VỰC KỸ THUẬT", 250, 3.3)] + \
           [(f"Tầng {i}", "KHÁCH SẠN", 250, 3.1) for i in range(2, 7)] + \
           [(f"Tầng {i}", "NHÀ Ở", 250, 3.1) for i in (7, 8)] + [("Tầng tum", "ĐỂ TRỐNG", 250, 3.0)]
    _, tong = tb.bang_quy_mo(msp, (vung[0] + 10 * S, vung[3] - 70 * S), tang)
    tb.bang(msp, (vung[0] + 10 * S, vung[3] - 10 * S), [10, 32, 50, 30, 28, 30, 40],
            [["STT", "CÔNG TRÌNH", "CHIỀU CAO PCCC (m)", "KHỐI TÍCH (m3)", "NHÓM NHÀ", "BẬC CHỊU LỬA",
              "CẤP NGUY HIỂM CHÁY"],
             ["A", "CÔNG TRÌNH CHÍNH", "(H)", "(S*H)", "BẢNG 6", "BẢNG 4", "BẢNG 5"],
             ["1", "KHÁCH SẠN KẾT HỢP NHÀ Ở", "26.2", f"{tong['khoi_tich']:,.0f}", "F1.2", "II", "S0"]],
            tieu_de="QUY MÔ CÔNG TRÌNH (QCVN 06:2022/BXD VÀ SỬA ĐỔI 01:2023)", mau_vien=kh.DO)
    tb.ghi_chu(msp, (vung[0] + 220 * S, vung[3] - 15 * S), [
        "- VẬT LIỆU HOÀN THIỆN, TRANG TRÍ TƯỜNG VÀ TRẦN (BAO GỒM CẢ TẤM TRẦN TREO NẾU CÓ), VẬT LIỆU ỐP LÁT, "
        "VẬT LIỆU PHỦ SÀN TRÊN ĐƯỜNG THOÁT NẠN TUÂN THỦ YÊU CẦU TẠI BẢNG B.8 - PHỤ LỤC B - QCVN 06:2022/BXD "
        "VÀ SỬA ĐỔI 01:2023.",
        "- VẬT LIỆU HOÀN THIỆN TRONG CÁC GIAN PHÒNG CHUNG, GIAN PHÒNG RIÊNG TUÂN THỦ YÊU CẦU TẠI BẢNG B.9.",
        f"+ CHIỀU CAO CÔNG TRÌNH {tong['chieu_cao']:.1f} m", "+ CHIỀU CAO PCCC: 26.2 m",
        "+ TRỤ CẤP NƯỚC ĐÔ THỊ LƯU LƯỢNG 10 L/S, KHÔNG QUÁ CÔNG TRÌNH 200 m"],
               tieu_de="VẬT LIỆU HOÀN THIỆN:", co=3.0, rong_mm=150)
    tb.tieu_de_to(msp, "QUY MÔ CÔNG TRÌNH", (G[0] + 190 * S, G[1] + 25 * S))


DANH_SACH = [("bia", 0, 0, lambda G: to_bia(G)), ("quy-mo", 0, 1, to_quy_mo),
             ("hm-bc", 0, 2, lambda G: tb.to_bia_hang_muc(msp, G, "HỆ THỐNG BÁO CHÁY", TL)),
             ("hm-cc", 0, 3, lambda G: tb.to_bia_hang_muc(msp, G, "HỆ THỐNG CHỮA CHÁY", TL)),
             ("hm-cs", 0, 4, lambda G: tb.to_bia_hang_muc(msp, G, "HỆ THỐNG ĐÈN CHIẾU SÁNG SỰ CỐ, ĐÈN CHỈ DẪN THOÁT NẠN", TL))]
for i, t in enumerate(["1", "2", "3-6", "7-8", "tum"]):
    DANH_SACH += [(f"bc-{t}", 1, i, lambda G, t=t, i=i: to_bao_chay(t, G, f"BC-{i + 1:02d}")),
                  (f"cc-{t}", 2, i, lambda G, t=t, i=i: to_chua_chay(t, G, f"CC-{i + 1:02d}")),
                  (f"cs-{t}", 3, i, lambda G, t=t, i=i: to_chieu_sang(t, G, f"CS-{i + 1:02d}"))]

if not CHON or "nen" in CHON:
    print("Chuyển nền kiến trúc sang xám, ẩn tên hình cũ trong block tầng...", flush=True)
    nen_kien_truc()
for ten, hang, cot, ham in DANH_SACH:
    if CHON and ten not in CHON:
        continue
    G = goc_to(hang, cot)
    truoc = msp.dem
    ham(G)
    ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(G[0], G[1]), ac.diem(G[0] + W_TO, G[1] + H_TO)))
    print(f"Xong tờ {ten}: {msp.dem - truoc} đối tượng", flush=True)
ac.goi_lai(lambda: doc.Save())
print("Đã lưu", doc.FullName)
