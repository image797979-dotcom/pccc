"""Vẽ một hệ PCCC của khách sạn mini 34 NVM vào bản vẽ riêng trong AutoCAD (COM), theo thiet_ke.json.

  python ve_acad.py bc|hong|cs [tầng ...]

- Tạo PCCC/PCCC-0x ....dwg = bản sao NVM/MBBT.dwg, mở trong AutoCAD và vẽ trực tiếp từng tầng.
- Thiết bị vẽ ở model space theo toạ độ tầng + điểm chèn block 'MBBT <tầng>' -> hiện trong các layout
  "MẶT BẰNG BỐ TRÍ ..." có sẵn (viewport 1:75). Ghi chú và bảng ký hiệu đặt ở khoảng trống bên phải nhà.
- Khung tên của đơn vị kiến trúc được thay bằng khung A3 trống; thêm tờ sơ đồ nguyên lý (và bảng bình).
"""
import json
import math
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import acad_com as ac
import acad_msp
import ky_hieu as kh
import so_do
import trinh_bay as tb
import layout_so_do
import cai_in
import thuyet_minh as tm

HE = sys.argv[1]
TL = 125
kh.TY_LE = TL
TEN_FILE = {"bc": "PCCC-01 BAO CHAY", "hong": "PCCC-02 HONG NUOC - BINH CHUA CHAY",
            "cs": "PCCC-03 CHIEU SANG SU CO - CHI DAN THOAT NAN"}[HE]
TEN_HE = {"bc": "BÁO CHÁY", "hong": "HỌNG NƯỚC VÁCH TƯỜNG + BÌNH CHỮA CHÁY",
          "cs": "CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN"}[HE]
KY = {"bc": "BC", "hong": "HN", "cs": "CS"}[HE]
GOC = os.path.abspath(r"NVM\MBBT.dwg")
os.makedirs("PCCC", exist_ok=True)
FILE = os.path.abspath(rf"PCCC\{TEN_FILE}.dwg")
TK = json.load(open("thiet_ke.json", encoding="utf-8"))
TANG_Y = {"HAM": 23000, "TRET": 0, "LUNG": -23000, "T2": -138000, "T3": -46000, "T4": -69000, "T5": -92000,
          "T6": -115000}
TEN_TANG = {"HAM": "TẦNG HẦM", "TRET": "TẦNG TRỆT", "LUNG": "TẦNG LỬNG", "T2": "TẦNG 2", "T3": "TẦNG 3",
            "T4": "TẦNG 4", "T5": "TẦNG 5", "T6": "TẦNG 6"}
LAYOUT_TANG = {"BỐ TRÍ HẦM": "HAM", "BỐ TRÍ TRỆT": "TRET", "TẦNG LỬNG": "LUNG", "TẦNG 2": "T2", "TẦNG 3": "T3",
               "TẦNG 4": "T4", "TẦNG 5": "T5", "TẦNG 6": "T6"}
CAO_DO = {"HAM": -3.0, "TRET": 0.0, "LUNG": 3.7, "T2": 7.0, "T3": 10.5, "T4": 13.8, "T5": 17.1, "T6": 20.1}
TT = {"phat_hanh": "Thiết kế sơ bộ", "cong_ty": [" "], "dia_chi_cty": "", "mst": "", "giam_doc": "", "chu_tri": "",
      "thiet_ke": "", "du_an": "KHÁCH SẠN MINI 34 NVM", "dia_chi": "", "ngay": "....../..../2026"}
CHI_CON = sys.argv[2:]
XG = 24600   # mép trái vùng ghi chú (khoảng trống phía đông nhà, trong viewport 1:125)
VP_TAM = (18875, 8190)  # tâm nhìn viewport tầng (toạ độ tầng): nhà dồn sang trái
VP_CAO = 188.0          # mm giấy: 23,5 m model, vừa một tầng (các block tầng cách nhau 23 m)


def dich(p, t):
    return (p[0], p[1] + TANG_Y[t])


def dg_dich(dg, t):
    return [dich(q, t) for q in dg]


# ---------- mở bản vẽ (bản sao mới mỗi lần chạy) ----------
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
    TAM = FILE[:-4] + f"__moi{os.getpid()}.dwg"
    shutil.copyfile(GOC, TAM)
    doc = ac.goi_lai(lambda: acad.Documents.Open(TAM))
    ac.cho_san_sang(acad)
    ac.goi_lai(lambda: cu.Close(False))
    ac.cho_san_sang(acad)
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    ac.goi_lai(lambda: doc.SaveAs(FILE, 60))
    os.remove(TAM)
ac.cho_san_sang(acad)
ac.goi_lai(lambda: setattr(acad, "ActiveDocument", doc))
doc = acad_msp.nap_thu_vien(doc, TL, layer_them=[("PCCC-SO-DO", 7)], acad=acad)
msp = acad_msp.MSP(doc)
ac.goi_lai(lambda: setattr(doc, "ActiveSpace", 1))
# chữ số dim 2,5 mm, đường dim lệch 4 mm khỏi tâm thiết bị (người dùng chốt ở dự án YERSIN)
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

# nền kiến trúc xám: layer trong block tầng (tiền tố '...$0$'), không đụng layer PCCC
lays = ac.goi_lai(lambda: doc.Layers)
for i in range(ac.goi_lai(lambda: lays.Count)):
    L = ac.goi_lai(lambda: lays.Item(i))
    ten = ac.goi_lai(lambda: L.Name)
    if "$0$" in ten and not ten.upper().startswith("PCCC"):
        try:
            ac.goi_lai(lambda: setattr(L, "Color", 8), so_lan=3)
        except Exception:
            pass


def chu(s, p, co=2.5, can="MIDDLE_LEFT", mau=None):
    tb._chu(msp, s, p, co, can, TL, mau=mau)


# ---------- vẽ từng tầng ----------
thu_tu = list(TK["tang"])
dem_tong = {}
for t, T in TK["tang"].items():
    if CHI_CON and t not in CHI_CON:
        continue
    y = TANG_Y[t]
    ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(-3500, y - 3600), ac.diem(41300, y + 19950)))
    co_loai = set()
    if HE == "bc":
        for loai in ("bao_khoi", "bao_nhiet"):
            for p in T["bc"].get(loai, []):
                kh.chen(msp, loai, dich(p, t))
                co_loai.add(loai)
        for p in T["bc"].get("nut_an", []):
            kh.chen(msp, "nut_an", dich((p[0] - 230, p[1]), t))
            kh.chen(msp, "chuong_den", dich((p[0] + 230, p[1]), t))
            co_loai |= {"nut_an", "chuong_den"}
        for loai in ("tu_tt", "den_fire"):
            for p in T["bc"].get(loai, []):
                kh.chen(msp, loai, dich(p, t))
                co_loai.add(loai)
        for c in T["cap"]:
            msp.add_lwpolyline([dich(q, t) for q in c], dxfattribs={"layer": kh.LAYER_CAP_BC[0]})
        for dg_m, ds in T["bc_manh"]:
            ds = [(l, dich(p, t)) for l, p in ds]
            if ds:
                tb.dim_bao_chay_phong(msp, dg_dich(dg_m, t), ds, 1000.0)
        so_zone = thu_tu.index(t) + 1
        chu(f"{TEN_TANG[t]} KẾT NỐI VỀ ZONE {so_zone},", dich((XG, 11600), t), 2.5)
        chu("TỦ TRUNG TÂM BÁO CHÁY ĐẶT TẠI SẢNH LỄ TÂN TẦNG TRỆT", dich((XG, 11000), t), 2.5)
        dem_tong[t] = {k: len(v) for k, v in T["bc"].items()}
        ghi = tb.GHI_CHU_BAO_CHAY + ["- Không bố trí đầu báo trong WC, buồng thang bộ, thang máy, thang xoắn.",
                                     "- Trần ≤ 3,5 m: đầu báo khói ≤ 85 m², cách nhau ≤ 9 m, cách tường ≤ 4,5 m; "
                                     "đầu báo nhiệt (bếp, bãi xe) ≤ 25 m², cách nhau ≤ 5 m, cách tường ≤ 2,5 m."]
        hop = tb.GHI_CHU_TC_BAO_CHAY
        cap = True
    elif HE == "hong":
        for p in T["hong"]:
            kh.chen(msp, "hong", dich(p, t))
            kh.chen(msp, "binh", dich((p[0] - 340, p[1] + 520), t))
            kh.chen(msp, "binh_co2", dich((p[0] + 340, p[1] + 520), t))
            kh.chen(msp, "truc_hong", dich((p[0] - 620, p[1] + 100), t))
            kh.ve_ong(msp, [dich((p[0] - 620, p[1] + 100), t), dich((p[0] - 420, p[1] + 100), t)], "hong", 50, ghi_dn=False)
            chu("TRỤC ĐỨNG HỌNG DN100", dich((p[0] - 450, p[1] + (1800 if t == "HAM" else 1000)), t), 2.0, mau=kh.DO)
            tb.vong_phuc_vu(msp, dich(p, t), 20000)
            co_loai |= {"hong", "binh", "binh_co2", "truc_hong"}
        for p in T["binh"]:
            kh.chen(msp, "binh", dich((p[0] - 220, p[1]), t))
            kh.chen(msp, "binh_co2", dich((p[0] + 220, p[1]), t))
            co_loai |= {"binh", "binh_co2"}
        if t == "TRET":
            kh.chen(msp, "hong_tiep", dich((15300, 6200), t))
            chu("HỌNG TIẾP NƯỚC XE CHỮA CHÁY", dich((15600, 6700), t), 2.0, mau=kh.DO)
            co_loai.add("hong_tiep")
        if t == "HAM":
            chu("TRẠM BƠM + BỂ NƯỚC CHỮA CHÁY", dich((9600, 7600), t), 2.2, mau=kh.DO)
            chu(f"(BỂ ≥ {TK['thuy_luc']['V_be_chon_m3']} m³)", dich((9600, 7150), t), 2.0, mau=kh.DO)
            kh.ve_ong(msp, [dich((9400, 9800), t), dich((7580, 9800), t), dich((7580, 8580), t)], "hong", 100)  # trạm bơm -> chân trục
        dem_tong[t] = {"hong": len(T["hong"]), "binh_abc": len(T["hong"]) + len(T["binh"]),
                       "binh_co2": len(T["hong"]) + len(T["binh"])}
        ghi = [f"- Họng nước vách tường: 1 họng × {TK['thuy_luc']['Q_hong_l_s']} l/s (QCVN 10:2025/BCA, Phụ lục H, Bảng H.5).",
               "- Tủ 600×400×220, tâm họng cao +1,25 m; van góc DN50, vòi DN50 dài 20 m, lăng D13.",
               "- Mỗi hộp họng kèm 01 bình bột ABC 8 kg + 01 bình CO2 5 kg; bình bố trí theo TCVN 7435-1:2004.",
               "- Vòng nét đứt: bán kính phục vụ 20 m của cuộn vòi."]
        hop = ["TRỤC ĐỨNG HỌNG NƯỚC DN100, NHÁNH VÀO HỘP DN50.", "BÌNH ĐẶT NƠI DỄ THẤY, DỄ LẤY, CAO ≤ 1,5 m.",
               f"BƠM SƠ BỘ {TK['thuy_luc']['Q_bom_l_s']} l/s, CỘT ÁP {TK['thuy_luc']['H_bom_m']} m."]
        cap = False
    else:  # cs
        for loai, ds in T["cs"].items():
            for p in ds:
                kh.chen(msp, loai, dich((p[0], p[1] + (350 if loai == "exit" else 0)), t))
                co_loai.add(loai)
        dem_tong[t] = {k: len(v) for k, v in T["cs"].items()}
        ghi = tb.GHI_CHU_CHIEU_SANG + ["- Đèn EXIT đặt trên cửa ra buồng thang bộ và cửa ra ngoài nhà.",
                                       "- Sơ đồ thoát nạn phòng (SDTNP) đặt trong mỗi phòng ngủ, cạnh cửa ra."]
        hop = []
        cap = False
    # ---- trình bày: ghi chú trên, hộp tiêu chuẩn giữa, bảng ký hiệu dưới (khoảng trống phía đông nhà) ----
    tb.ghi_chu(msp, dich((XG, 18800), t), ghi, rong_mm=128, co=2.5)
    if hop:
        tb.hop_ghi_chu(msp, dich((XG, 5000), t), hop, rong_mm=128, co=2.1)
    ds_loai = [l for l in kh.KY_HIEU if l in co_loai]
    if ds_loai:
        kh.ve_bang(msp, dich((XG, -3300), t), ds_loai, co_cap=cap,
                   ong=(("hong",) if HE == "hong" else ()), rong_mm=90)
    print(t, "xong", dem_tong[t], "đối tượng:", msp.dem, flush=True)
    ac.goi_lai(lambda: doc.Save())

json.dump(dem_tong, open(f"dem_{HE}.json", "w", encoding="utf-8"), ensure_ascii=False)

# ---------- sơ đồ nguyên lý / bảng ở model space bên phải ----------
W, H = 420 * TL, 297 * TL
to_them = []
if not CHI_CON:
    G = (60000, 0)
    ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(*G), ac.diem(G[0] + W, G[1] + H)))
    tb.khung_a3(msp, G, TL, dict(TT, so_to=f"{KY}-{len(thu_tu) + 1:02d}"))

    def to_moi(k):
        """Khung A3 thứ k (k = 1, 2, ...) bên phải tờ sơ đồ; trả về góc tờ và ký hiệu tờ."""
        Gk = (60000 + k * (W + 5000), 0)
        ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(*Gk), ac.diem(Gk[0] + W, Gk[1] + H)))
        so = f"{KY}-{len(thu_tu) + 1 + k:02d}"
        tb.khung_a3(msp, Gk, TL, dict(TT, so_to=so))
        return Gk
    if HE == "bc":
        zones = [(TEN_TANG[t], {k: len(TK["tang"][t]["bc"].get(k, [])) for k in
                                ("bao_khoi", "bao_nhiet", "nut_an", "chuong_den", "den_fire")
                                if TK["tang"][t]["bc"].get(k)}) for t in thu_tu]
        aq = so_do.bao_chay(msp, G, zones, TL, so_zone_tu=10, ten_tu="10 ZONES", tang_dat_tu="TẦNG TRỆT")
        print("ắc quy:", aq, flush=True)
        to_them.append(("BC - SƠ ĐỒ NGUYÊN LÝ BÁO CHÁY", G))
        G2 = to_moi(1)
        tm.to_quy_mo(msp, G2)
        to_them.append(("BC - QUY MÔ CÔNG TRÌNH", G2))
        G3 = to_moi(2)
        tm.to_tm_bao_chay(msp, G3, TK, aq)
        to_them.append(("BC - THUYẾT MINH BÁO CHÁY", G3))
    elif HE == "hong":
        tl_ = TK["thuy_luc"]
        so_do.chua_chay(msp, G, [(TEN_TANG[t], CAO_DO[t], 0, bool(TK["tang"][t]["hong"])) for t in thu_tu],
                        [("BƠM ĐIỆN CHÍNH", "EP-01", tl_["Q_bom_l_s"], tl_["H_bom_m"]),
                         ("BƠM DIESEL DỰ PHÒNG", "DP-02", tl_["Q_bom_l_s"], tl_["H_bom_m"]),
                         ("BƠM BÙ ÁP", "JP", 1.0, tl_["H_bom_m"] + 5)], TL,
                        the_tich_be=tl_["V_be_chon_m3"], dn_truc=100, dn_hong=50,
                        phong_bom="PHÒNG BƠM TẦNG HẦM")
        to_them.append(("HN - SƠ ĐỒ NGUYÊN LÝ CHỮA CHÁY", G))
        G2 = (60000 + W + 5000, 0)
        ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(*G2), ac.diem(G2[0] + W, G2[1] + H)))
        x0, y0, x1, y1 = tb.khung_a3(msp, G2, TL, dict(TT, so_to=f"{KY}-{len(thu_tu) + 2:02d}"))
        G3 = to_moi(2)
        tm.to_tm_chua_chay(msp, G3, TK)
        to_them.append(("HN - THUYẾT MINH CHỮA CHÁY", G3))
        tang_binh = []
        for t in thu_tu:
            S = tm.DIEN_TICH[t]  # diện tích sàn (như bảng khối tích), không phải tổng diện tích phòng
            tang_binh.append((TEN_TANG[t], S, 2 * (len(TK["tang"][t]["hong"]) + len(TK["tang"][t]["binh"]))))
        tb.bang_binh(msp, (x0 + 8 * TL, y1 - 15 * TL), tang_binh, TL)
        tb.tieu_de_to(msp, "BẢNG TÍNH SỐ LƯỢNG BÌNH CHỮA CHÁY", ((x0 + x1) / 2, y0 + 12 * TL), TL)
        to_them.append(("HN - BẢNG TÍNH BÌNH CHỮA CHÁY", G2))
    else:
        cs = []
        for t in thu_tu:
            d = TK["tang"][t]["cs"]
            cs.append((TEN_TANG[t], {"exit": len(d.get("exit", [])), "exit_huong": len(d.get("exit_huong", [])),
                                     "den_su_co": len(d.get("den_su_co", [])), "sdtn": len(d.get("sdtn", [])),
                                     "sdtnp": len(d.get("sdtnp", [])), "mat_na": 0}))
        so_do.chieu_sang(msp, G, cs, TL)
        to_them.append(("CS - SƠ ĐỒ NGUYÊN LÝ CHIẾU SÁNG SỰ CỐ", G))
        G2 = to_moi(1)
        tm.to_tm_chieu_sang(msp, G2, TK)
        to_them.append(("CS - THUYẾT MINH CHIẾU SÁNG SỰ CỐ", G2))
        G3 = to_moi(2)
        tm.to_tm_dien(msp, G3, TK)
        to_them.append(("CS - THUYẾT MINH ĐIỆN PCCC", G3))
    ac.goi_lai(lambda: doc.Save())

# ---------- layout: khung tên trống, tên tờ, thêm tờ sơ đồ ----------
if True:
    las = ac.goi_lai(lambda: doc.Layouts)
    mau_lay = None
    ds_lay = [ac.goi_lai(lambda: las.Item(i)) for i in range(ac.goi_lai(lambda: las.Count))]
    for lay in ds_lay:
        ten = ac.goi_lai(lambda: lay.Name)
        t = next((v for k, v in LAYOUT_TANG.items() if ten.endswith(k)), None)
        if ten == "Model" or t is None or (CHI_CON and t not in CHI_CON):
            continue
        mau_lay = mau_lay or lay
        so = thu_tu.index(t) + 1
        blk = ac.goi_lai(lambda: lay.Block)
        for j in range(ac.goi_lai(lambda: blk.Count) - 1, -1, -1):
            e = ac.goi_lai(lambda: blk.Item(j))
            if ac.goi_lai(lambda: e.ObjectName) != "AcDbBlockReference":
                continue
            ten_b = ac.goi_lai(lambda: e.EffectiveName)
            if ten_b in ("khung A3", "KY HIEU MC") or "Mặt cắt" in ten_b:
                ac.goi_lai(lambda: e.Delete())   # khung tên + ký hiệu tham chiếu tờ kiến trúc
            elif ac.goi_lai(lambda: e.HasAttributes):
                for a in ac.goi_lai(lambda: e.GetAttributes()):
                    tag = ac.goi_lai(lambda: a.TagString)
                    if tag == "TENBV":
                        ac.goi_lai(lambda: setattr(a, "TextString", f"MẶT BẰNG {TEN_HE} {TEN_TANG[t]}"))
                    elif tag == "NUMBER":
                        ac.goi_lai(lambda: setattr(a, "TextString", str(so)))
                    elif tag == "TYLE":
                        ac.goi_lai(lambda: setattr(a, "TextString", "1:125"))
        vps = []
        for j in range(ac.goi_lai(lambda: blk.Count) - 1, -1, -1):
            e = ac.goi_lai(lambda: blk.Item(j))
            on = ac.goi_lai(lambda: e.ObjectName)
            if on == "AcDbViewport" and abs(ac.goi_lai(lambda: e.CustomScale) - 1 / 75) < 1e-5:
                vps.append(e)
            elif "Dimension" in on or (on == "AcDbLine" and ac.goi_lai(lambda: e.Layer) == "21. BO - DIM DETAIL"):
                ac.goi_lai(lambda: e.Delete())
        for vp in vps:
            ac.goi_lai(lambda: setattr(doc, "ActiveLayout", lay))
            ac.cho_san_sang(acad)
            doc = ac.goi_lai(lambda: acad.ActiveDocument)
            ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(-5, -9), ac.diem(425, 306)))
            ac.goi_lai(lambda: setattr(vp, "Height", VP_CAO))
            ac.goi_lai(lambda: setattr(vp, "Center", ac.diem(189.0, 152.0)))
            ac.goi_lai(lambda: setattr(doc, "MSpace", True))
            ac.goi_lai(lambda: setattr(doc, "ActivePViewport", vp))
            hv = VP_CAO * TL
            ac.goi_lai(lambda: acad.ZoomCenter(ac.diem(VP_TAM[0], VP_TAM[1] + TANG_Y[t]), float(hv)))
            ac.goi_lai(lambda: setattr(doc, "MSpace", False))
            ac.goi_lai(lambda: setattr(vp, "DisplayLocked", True))
        ps = acad_msp.MSP(doc)
        ps.ms = blk
        tb.khung_a3(ps, (0, 0), 1, dict(TT, so_to=f"{KY}-{so:02d}"))
        ac.goi_lai(lambda: setattr(lay, "Name", f"{KY}-{so:02d} {TEN_TANG[t]}"))
    mau_ten = ac.goi_lai(lambda: mau_lay.Name) if mau_lay is not None else None
    for ten, G in to_them:
        doc = layout_so_do.them_layout(acad, ten, G, TL, mau_ten)
        print("thêm layout", ten, flush=True)
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    cai_in.cai_dat(acad, doc)
    ac.goi_lai(lambda: setattr(doc, "ActiveSpace", 1))
    ac.goi_lai(lambda: acad.ZoomExtents())
    ac.goi_lai(lambda: doc.Save())
print("XONG", FILE, "– đối tượng mới:", msp.dem, flush=True)
