"""Vẽ một hệ PCCC của khách sạn YERSIN vào bản vẽ riêng trong AutoCAD (COM), theo thiet_ke.json.

  python ve_acad.py bc|spr|hong|cs

- Tạo YERSIN/PCCC-0x ....dwg = bản sao 4.MBBT.dwg (xref kiến trúc giữ nguyên đường dẫn tương đối),
  mở trong AutoCAD và vẽ trực tiếp: người dùng thấy từng tầng hiện ra.
- Thiết bị vẽ ở model space theo cao độ model của tầng → hiện trong các layout "MẶT BẰNG ... TẦNG x" có sẵn
  (viewport 1:80). Ký hiệu theo hồ sơ mẫu, tỷ lệ 1:80.
- Khung tên của đơn vị kiến trúc trong layout được thay bằng khung A3 trống (người dùng chốt để trống).
- Sơ đồ nguyên lý vẽ ở model space bên phải (x ≥ 60 m), thêm layout riêng.
"""
import json
import math
import os
import shutil
import sys

sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac
import acad_msp
import ky_hieu as kh
import ong as ONG
import so_do
import trinh_bay as tb
import layout_so_do
import cai_in

HE = sys.argv[1]
TL = 80
kh.TY_LE = TL
TEN_FILE = {"bc": "PCCC-01 BAO CHAY", "spr": "PCCC-02 SPRINKLER", "hong": "PCCC-03 HONG NUOC - BINH CHUA CHAY",
            "cs": "PCCC-04 CHIEU SANG SU CO - CHI DAN THOAT NAN"}[HE]
TEN_HE = {"bc": "BÁO CHÁY", "spr": "CHỮA CHÁY TỰ ĐỘNG SPRINKLER", "hong": "HỌNG NƯỚC VÁCH TƯỜNG + BÌNH CHỮA CHÁY",
          "cs": "CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN"}[HE]
KY = {"bc": "BC", "spr": "SP", "hong": "HN", "cs": "CS"}[HE]
GOC = os.path.abspath(r"YERSIN\4.MBBT.dwg")
FILE = os.path.abspath(rf"YERSIN\{TEN_FILE}.dwg")
TK = json.load(open("thiet_ke.json", encoding="utf-8"))
TANG_Y = {"HAM": 0, "TRET": 23440, "LUNG": 46880, "T2": 70320, "T3": 93760, "T4": 117200, "T5": 140640,
          "T6": 164080, "T7": 187520, "SAN_THUONG": 210960}
TEN_TANG = {"HAM": "TẦNG HẦM", "TRET": "TẦNG TRỆT", "LUNG": "TẦNG LỬNG", "T2": "TẦNG 2", "T3": "TẦNG 3",
            "T4": "TẦNG 4", "T5": "TẦNG 5", "T6": "TẦNG 6", "T7": "TẦNG 7", "SAN_THUONG": "TẦNG SÂN THƯỢNG"}
LAYOUT_TANG = {"TẦNG HẦM": "HAM", "TẦNG TRỆT": "TRET", "TẦNG LỬNG": "LUNG", "TẦNG 2": "T2", "TẦNG 3": "T3",
               "TẦNG 4": "T4", "TẦNG 5": "T5", "TẦNG 6": "T6", "TẦNG 7": "T7", "SÂN THƯỢNG": "SAN_THUONG"}
TT = {"phat_hanh": "Thiết kế sơ bộ", "cong_ty": [" "], "dia_chi_cty": "", "mst": "", "giam_doc": "", "chu_tri": "",
      "thiet_ke": "", "du_an": "KHÁCH SẠN MV YERSIN", "dia_chi": "7 Yersin, Bến Thành, Hồ Chí Minh",
      "ngay": "....../..../2026"}
CHI_CON = sys.argv[2:]  # tuỳ chọn: chỉ vẽ các tầng này (thử)


def dich(p, t):
    return (p[0], p[1] + TANG_Y[t])


def dg_dich(dg, t):
    return [dich(q, t) for q in dg]


# ---------- mở bản vẽ ----------
acad = ac.ket_noi()
cu = None
for i in range(ac.goi_lai(lambda: acad.Documents.Count)):
    d = ac.goi_lai(lambda: acad.Documents.Item(i))
    if ac.goi_lai(lambda: d.FullName).lower() == FILE.lower():
        cu = d
if cu is None:
    shutil.copyfile(GOC, FILE)
    doc = ac.goi_lai(lambda: acad.Documents.Open(FILE))
else:
    # mở bản mới trước rồi mới đóng bản cũ (đóng bản đang kích hoạt trước làm AutoCAD mất ngữ cảnh: Open báo lỗi)
    TAM = FILE[:-4] + f"__moi{os.getpid()}.dwg"  # tên riêng mỗi lần chạy
    shutil.copyfile(GOC, TAM)
    doc = ac.goi_lai(lambda: acad.Documents.Open(TAM))
    ac.cho_san_sang(acad)
    ac.goi_lai(lambda: cu.Close(False))
    ac.cho_san_sang(acad)
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    ac.goi_lai(lambda: doc.SaveAs(FILE, 60))
    os.remove(TAM)
# đóng các bản tạm còn sót của lần chạy bị dừng (bản đang kích hoạt là bản mới nên đóng an toàn)
for i in range(ac.goi_lai(lambda: acad.Documents.Count) - 1, -1, -1):
    d = ac.goi_lai(lambda: acad.Documents.Item(i))
    if "__moi" in ac.goi_lai(lambda: d.Name):
        f_cu = ac.goi_lai(lambda: d.FullName)
        ac.goi_lai(lambda: d.Close(False))
        try:
            os.remove(f_cu)
        except OSError:
            pass
ac.cho_san_sang(acad)
ac.goi_lai(lambda: setattr(acad, "ActiveDocument", doc))
doc = acad_msp.nap_thu_vien(doc, TL, layer_them=[("PCCC-SO-DO", 7)], acad=acad)
msp = acad_msp.MSP(doc)
ac.goi_lai(lambda: setattr(doc, "ActiveSpace", 1))  # model space (bản gốc lưu đang ở layout)
if True:
    # Mọi hệ (người dùng yêu cầu 28/10/2026): chữ số dim nhỏ hơn (2,5 mm thay 4,2 mm) và đường dim
    # dời khỏi tâm thiết bị 4 mm giấy cho dễ đọc
    from pythoncom import VT_R8
    from win32com.client import VARIANT
    ac.dam_bao_dimstyle(doc, "PCCC_BC", TL, 0)
    ac.goi_lai(lambda: doc.SetVariable("DIMTXT", VARIANT(VT_R8, 2.5)))
    ac.goi_lai(lambda: doc.SetVariable("DIMASZ", VARIANT(VT_R8, 1.4)))
    ac.goi_lai(lambda: doc.SetVariable("DIMTXSTY", kh.KIEU_CHU_HEP))
    ds_bc = ac.goi_lai(lambda: doc.DimStyles.Item("PCCC_BC"))
    ac.goi_lai(lambda: ds_bc.CopyFrom(doc))
    tb.DIMSTYLE = "PCCC_BC"
    tb.LECH_DIM_DAU_BAO = 4.0
print("Đã mở", FILE, flush=True)

# nền kiến trúc xám (chỉ layer xref, không đụng layer PCCC)
lays = ac.goi_lai(lambda: doc.Layers)
for i in range(ac.goi_lai(lambda: lays.Count)):
    L = ac.goi_lai(lambda: lays.Item(i))
    ten = ac.goi_lai(lambda: L.Name)
    if "|" in ten and not ten.upper().startswith("PCCC"):
        try:
            ac.goi_lai(lambda: setattr(L, "Color", 8), so_lan=3)
        except Exception:
            pass


def zoom_tang(t):
    y = TANG_Y[t]
    ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(-3000, y - 2000), ac.diem(25000, y + 21500)))


def chu(s, p, co=2.5, can="MIDDLE_LEFT", mau=None):
    tb._chu(msp, s, p, co, can, TL, mau=mau)


# ---------- vẽ từng tầng ----------
dem_tong = {}
for t, T in TK["tang"].items():
    if CHI_CON and t not in CHI_CON:
        continue
    zoom_tang(t)
    R = T["phong"]
    co_loai = set()
    if HE == "bc":
        for loai in ("bao_khoi", "bao_nhiet"):
            for p in T["bc"].get(loai, []):
                kh.chen(msp, loai, dich(p, t))
                co_loai.add(loai)
        for p in T["bc"].get("nut_an", []):
            kh.chen(msp, "nut_an", dich((p[0] - 160, p[1]), t))
            kh.chen(msp, "chuong_den", dich((p[0] + 160, p[1]), t))
            co_loai |= {"nut_an", "chuong_den"}
        for loai in ("tu_tt", "den_fire"):
            for p in T["bc"].get(loai, []):
                kh.chen(msp, loai, dich(p, t))
                co_loai.add(loai)
        for c in T["cap"]:
            msp.add_lwpolyline([dich(q, t) for q in c], dxfattribs={"layer": kh.LAYER_CAP_BC[0]})
        for r in R:  # dim theo từng mảnh phòng (đã trừ WC, buồng thang) để dim không xuyên qua WC
            for dg_m, ds in r.get("bc_manh", []):
                ds = [(l, dich(p, t)) for l, p in ds]
                if ds:
                    tb.dim_bao_chay_phong(msp, dg_dich(dg_m, t), ds, 1000.0)
        so_zone = list(TK["tang"]).index(t) + 1
        chu(f"{TEN_TANG[t]} KẾT NỐI VỀ ZONE {so_zone},", dich((4600, 5900), t), 2.5)
        chu("TỦ TRUNG TÂM BÁO CHÁY ĐẶT TẠI TẦNG TRỆT", dich((4600, 5500), t), 2.5)
        dem_tong[t] = {k: len(v) for k, v in T["bc"].items()}
        ghi = tb.GHI_CHU_BAO_CHAY + ["KHÔNG BỐ TRÍ ĐẦU BÁO TRONG WC VÀ BUỒNG THANG BỘ, KHÔNG BỐ TRÍ CÁP ĐIỆN TRÊN TRẦN WC.",
                                     f"TRẦN TREO CAO {3.2:.1f} m; ĐẦU BÁO KHÓI: KHOẢNG CÁCH ≤ 9 m, CÁCH TƯỜNG ≤ 4,5 m."]
        hop = tb.GHI_CHU_TC_BAO_CHAY
        cap = True
    elif HE == "spr":
        for p in T["spr"]:
            kh.chen(msp, "sprinkler", dich(p, t))
        if T["spr"]:
            co_loai |= {"sprinkler", "truc_spr", "van_spr"}
            for a, b, n, l in T["ong_spr"]:
                if abs(a[0] - b[0]) + abs(a[1] - b[1]) < 1:
                    continue
                kh.ve_ong(msp, [dich(a, t), dich(b, t)], "spr", ONG.dn_spr(n))
            truc = T["truc"]
            kh.chen(msp, "truc_spr", dich(truc, t))
            kh.chen(msp, "van_spr", dich((truc[0] + 450, T["y_chinh"]), t))
            chu("TRỤC ĐỨNG SPRINKLER DN100", dich((truc[0] + 300, truc[1] + 500), t), 2.0, mau=kh.DO)
            lech = tb.LECH_DIM_DAU_BAO * TL  # dời chuỗi dim khỏi tâm đầu phun
            for a, b in T["spr_dim"]:
                ngang = abs(a[1] - b[1]) < 1
                pa, pb = dich(a, t), dich(b, t)
                tb.dim(msp, pa, pb, (pa[1] if ngang else pa[0]) + lech, ngang=ngang)
        dem_tong[t] = {"sprinkler": len(T["spr"])}
        ghi = ["HỆ THỐNG CHỮA CHÁY TỰ ĐỘNG SPRINKLER THIẾT KẾ THEO TCVN 7336:2021, NHÓM NGUY HIỂM CHÁY 1.",
               "ĐẦU PHUN HƯỚNG XUỐNG 68°C, K = 80; KHOẢNG CÁCH GIỮA CÁC ĐẦU ≤ 4 m, CÁCH TƯỜNG 0,5–2 m, ≤ 12 m²/ĐẦU.",
               "KHÔNG BỐ TRÍ ĐẦU PHUN TRONG WC VÀ BUỒNG THANG BỘ.",
               "ỐNG THÉP TRÁNG KẼM SƠN ĐỎ; ĐƯỜNG KÍNH CHỌN SƠ BỘ THEO SỐ ĐẦU PHUN, PHẢI KIỂM TRA THUỶ LỰC."]
        hop = [f"LƯU LƯỢNG BƠM SƠ BỘ {TK['thuy_luc']['Q_bom_l_s']} l/s, CỘT ÁP {TK['thuy_luc']['H_bom_m']} m",
               f"BỂ NƯỚC CHỮA CHÁY ≥ {TK['thuy_luc']['V_be_chon_m3']} m³ (CHƯA GỒM NƯỚC CHỮA CHÁY NGOÀI NHÀ)"]
        cap = False
    elif HE == "hong":
        for p in T["hong"]:
            kh.chen(msp, "hong", dich((p[0], p[1]), t))
            kh.chen(msp, "binh", dich((p[0] - 220, p[1] - 330), t))
            kh.chen(msp, "binh_co2", dich((p[0] + 220, p[1] - 330), t))
            kh.chen(msp, "truc_hong", dich((p[0] - 400, p[1] + 260), t))
            kh.ve_ong(msp, [dich((p[0] - 400, p[1] + 260), t), dich((p[0] - 400, p[1] + 90), t)], "hong", 50, ghi_dn=False)
            tb.vong_phuc_vu(msp, dich(p, t), 20000)
            co_loai |= {"hong", "binh", "binh_co2", "truc_hong"}
        for p in T["binh"]:
            if T["hong"] and math.dist(p, T["hong"][0]) < 100:
                continue
            kh.chen(msp, "binh", dich((p[0] - 160, p[1]), t))
            kh.chen(msp, "binh_co2", dich((p[0] + 160, p[1]), t))
            co_loai |= {"binh", "binh_co2"}
        if t == "TRET":
            kh.chen(msp, "hong_tiep", dich((20500, 12500), t))
            chu("HỌNG TIẾP NƯỚC XE CHỮA CHÁY", dich((20500, 12000), t), 2.0, mau=kh.DO)
            co_loai.add("hong_tiep")
        dem_tong[t] = {"hong": len(T["hong"]), "binh": 2 * len(T["binh"])}
        ghi = ["HỌNG NƯỚC VÁCH TƯỜNG: 1 HỌNG × 2,5 l/s (QCVN 10:2025/BCA, PHỤ LỤC H, BẢNG H.5).",
               "TỦ 600×400×220, TÂM HỌNG CAO +1,25 m; VAN GÓC DN50, VÒI DN50 DÀI 20 m, LĂNG D13.",
               "MỖI HỘP HỌNG KÈM 01 BÌNH BỘT ABC 8 kg + 01 BÌNH CO2 5 kg; BỐ TRÍ BÌNH THEO TCVN 7435-1:2004.",
               "VÒNG NÉT ĐỨT: BÁN KÍNH PHỤC VỤ 20 m CỦA CUỘN VÒI."]
        hop = ["TRỤC ĐỨNG HỌNG NƯỚC DN100, NHÁNH VÀO HỘP DN50.", "BÌNH ĐẶT NƠI DỄ THẤY, DỄ LẤY, CAO ≤ 1,5 m."]
        cap = False
    else:  # cs
        for loai, ds in T["cs"].items():
            for p in ds:
                kh.chen(msp, loai, dich((p[0], p[1] + (250 if loai == "exit" else 0)), t))
                co_loai.add(loai)
        dem_tong[t] = {k: len(v) for k, v in T["cs"].items()}
        ghi = tb.GHI_CHU_CHIEU_SANG + ["- Đèn EXIT đặt trên cửa ra buồng thang bộ, đèn chỉ hướng dọc hành lang.",
                                       "- Sơ đồ thoát nạn phòng (SDTNP) đặt trong mỗi phòng ngủ, cạnh cửa ra."]
        hop = []
        cap = False
    # ---- trình bày: bảng ký hiệu, ghi chú (khoảng trống phía đông nam mặt bằng) ----
    ds_loai = [l for l in kh.KY_HIEU if l in co_loai]
    if ds_loai:
        kh.ve_bang(msp, dich((4600, 300), t), ds_loai, co_cap=cap, ong=(("spr",) if HE == "spr" and T["spr"] else
                   ("hong",) if HE == "hong" and T["hong"] else ()), rong_mm=75)
    # khoảng trống đông nam (x 4,6–19,8 m, y 0,3–6,2 m; phía trên là hàng bong bóng trục)
    tb.ghi_chu(msp, dich((11800, 5800), t), ghi, rong_mm=100, co=2.2)  # cột phải, trên (chữ nhỏ: không tràn)
    if hop:
        tb.hop_ghi_chu(msp, dich((11800, 300), t), hop, rong_mm=100)  # cột phải, dưới
    print(t, "xong", dem_tong[t], "đối tượng:", msp.dem, flush=True)
    ac.goi_lai(lambda: doc.Save())

json.dump(dem_tong, open(f"dem_{HE}.json", "w", encoding="utf-8"), ensure_ascii=False)


# ---------- sơ đồ nguyên lý / bảng: vẽ ở model space bên phải, mỗi tờ một khung A3 ----------
W, H = 420 * TL, 297 * TL
to_them = []  # [(tên layout, góc model, số tờ)]
thu_tu = [t for t in TK["tang"]]  # từ dưới lên
if not CHI_CON:
    G = (60000, 0)
    ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(*G), ac.diem(G[0] + W, G[1] + H)))
    if HE == "bc":
        tb.khung_a3(msp, G, TL, dict(TT, so_to=f"{KY}-11"))
        zones = [(TEN_TANG[t], {k: len(TK["tang"][t]["bc"].get(k, [])) for k in
                                ("bao_khoi", "bao_nhiet", "nut_an", "chuong_den", "den_fire")
                                if TK["tang"][t]["bc"].get(k)}) for t in thu_tu]
        aq = so_do.bao_chay(msp, G, zones, TL, so_zone_tu=12, ten_tu="12 ZONES")
        print("ắc quy:", aq, flush=True)
        to_them.append(("BC - SƠ ĐỒ NGUYÊN LÝ BÁO CHÁY", G, f"{KY}-11"))
    elif HE in ("spr", "hong"):
        tl_ = TK["thuy_luc"]
        tb.khung_a3(msp, G, TL, dict(TT, so_to=f"{KY}-11"))
        cao = {t: 3.5 * (i - 1) for i, t in enumerate(thu_tu)}
        so_do.chua_chay(msp, G, [(TEN_TANG[t], cao[t], len(TK["tang"][t]["spr"]), bool(TK["tang"][t]["hong"]))
                                 for t in thu_tu],
                        [("BƠM ĐIỆN CHÍNH", "EP-01", tl_["Q_bom_l_s"], tl_["H_bom_m"]),
                         ("BƠM DIESEL DỰ PHÒNG", "DP-02", tl_["Q_bom_l_s"], tl_["H_bom_m"]),
                         ("BƠM BÙ ÁP", "JP", 1.0, tl_["H_bom_m"] + 5)], TL,
                        the_tich_be=tl_["V_be_chon_m3"], dn_truc=100, dn_hong=50)
        to_them.append((f"{KY} - SƠ ĐỒ NGUYÊN LÝ CHỮA CHÁY", G, f"{KY}-11"))
        if HE == "hong":
            G2 = (60000 + W + 5000, 0)
            ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(*G2), ac.diem(G2[0] + W, G2[1] + H)))
            x0, y0, x1, y1 = tb.khung_a3(msp, G2, TL, dict(TT, so_to=f"{KY}-12"))
            tang_binh = []
            for t in thu_tu:
                S = round(sum(r["S"] for r in TK["tang"][t]["phong"] if r["loai"] in ("phong", "wc")), 1)
                tang_binh.append((TEN_TANG[t].replace("TẦNG SÂN THƯỢNG", "SÂN THƯỢNG"), S, 2 * len(TK["tang"][t]["binh"])))
            tb.bang_binh(msp, (x0 + 8 * TL, y1 - 15 * TL), tang_binh, TL)
            tb.tieu_de_to(msp, "BẢNG TÍNH SỐ LƯỢNG BÌNH CHỮA CHÁY", ((x0 + x1) / 2, y0 + 12 * TL), TL)
            to_them.append(("HN - BẢNG TÍNH BÌNH CHỮA CHÁY", G2, f"{KY}-12"))
    else:
        tb.khung_a3(msp, G, TL, dict(TT, so_to=f"{KY}-11"))
        cs = []
        for t in thu_tu:
            d = TK["tang"][t]["cs"]
            cs.append((TEN_TANG[t], {"exit": len(d.get("exit", [])), "exit_huong": len(d.get("exit_huong", [])),
                                     "den_su_co": len(d.get("den_su_co", [])), "sdtn": len(d.get("sdtn", [])),
                                     "sdtnp": len(d.get("sdtnp", [])), "mat_na": 0}))
        so_do.chieu_sang(msp, G, cs, TL)
        to_them.append(("CS - SƠ ĐỒ NGUYÊN LÝ CHIẾU SÁNG SỰ CỐ", G, f"{KY}-11"))
    ac.goi_lai(lambda: doc.Save())

# ---------- layout: khung tên trống, tên tờ, xoá tờ mái, thêm tờ sơ đồ ----------
    las = ac.goi_lai(lambda: doc.Layouts)
    mau_lay = None
    ds_lay = [ac.goi_lai(lambda: las.Item(i)) for i in range(ac.goi_lai(lambda: las.Count))]
    for lay in ds_lay:
        ten = ac.goi_lai(lambda: lay.Name)
        if ten == "Model":
            continue
        if "MÁI" in ten:
            ac.goi_lai(lambda: lay.Delete())
            continue
        t = next((v for k, v in LAYOUT_TANG.items() if ten.endswith(k)), None)
        if t is None:
            continue
        mau_lay = mau_lay or lay
        so = thu_tu.index(t) + 1
        blk = ac.goi_lai(lambda: lay.Block)
        for j in range(ac.goi_lai(lambda: blk.Count) - 1, -1, -1):
            e = ac.goi_lai(lambda: blk.Item(j))
            if ac.goi_lai(lambda: e.ObjectName) != "AcDbBlockReference":
                continue
            ten_b = ac.goi_lai(lambda: e.EffectiveName)
            if ten_b == "khung A3":
                ac.goi_lai(lambda: e.Delete())
            elif ac.goi_lai(lambda: e.HasAttributes):
                for a in ac.goi_lai(lambda: e.GetAttributes()):
                    tag = ac.goi_lai(lambda: a.TagString)
                    if tag == "TENBV":
                        ac.goi_lai(lambda: setattr(a, "TextString", f"MẶT BẰNG {TEN_HE} {TEN_TANG[t]}"))
                    elif tag == "NUMBER":
                        ac.goi_lai(lambda: setattr(a, "TextString", str(so)))
        ps = acad_msp.MSP(doc)
        ps.ms = blk
        tb.khung_a3(ps, (-795, 889), 1, dict(TT, so_to=f"{KY}-{so:02d}"))
        ac.goi_lai(lambda: setattr(lay, "Name", f"{KY}-{so:02d} {TEN_TANG[t]}"))
    mau_ten = ac.goi_lai(lambda: mau_lay.Name) if mau_lay is not None else None
    for ten, G, so_to in to_them:
        doc = layout_so_do.them_layout(acad, ten, G, TL, mau_ten)
        print("thêm layout", ten, flush=True)
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    cai_in.cai_dat(acad, doc)
    ac.goi_lai(lambda: setattr(doc, "ActiveSpace", 1))
    ac.goi_lai(lambda: acad.ZoomExtents())
    ac.goi_lai(lambda: doc.Save())
print("XONG", FILE, "– đối tượng mới:", msp.dem, flush=True)
