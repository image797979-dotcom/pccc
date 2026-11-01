"""Thêm 3 tờ sơ đồ nguyên lý (báo cháy, chữa cháy, đèn sự cố) vào bản vẽ KS 8 tầng đang mở trong AutoCAD.

  python ve_so_do.py <thư mục scripts skill> du_lieu.json

Số lượng thiết bị đếm từ mặt bằng (du_lieu.json); tầng 3-6 và 7-8 nhân theo số tầng.
Tờ đặt ở cột thứ 6 của các hàng báo cháy / chữa cháy / chiếu sáng (BC-06, CC-06, CS-06).
"""
import json
import sys

sys.path.insert(0, sys.argv[1])
import acad_com as ac
import acad_msp
import ky_hieu as kh
import so_do
import trinh_bay as tb

DL = json.load(open(sys.argv[2], encoding="utf-8"))
TL = 125
kh.TY_LE = TL
W, H = 420 * TL, 297 * TL
TT = {"phat_hanh": "Thiết kế sơ bộ", "cong_ty": ["CÔNG TY TNHH", "MTV CƠ ĐIỆN", "THỊNH PHÁT"],
      "dia_chi_cty": "AD: 8/8 Nguyễn Đình Khơi, Phường 8, Q.Tân Bình", "mst": "0317979017",
      "giam_doc": "DƯƠNG THỊ THANH XUÂN", "chu_tri": "Bùi Mạnh Cường", "thiet_ke": "Nguyễn Thanh Thế",
      "du_an": "KHÁCH SẠN KẾT HỢP NHÀ Ở", "dia_chi": "32 Dã Tượng, Phường Vũng Tàu, Hồ Chí Minh",
      "ngay": "....../10/2026"}
TANG = [("TẦNG 1", "1", 0.0), ("TẦNG 2", "2", 3.3)] + [(f"TẦNG {i}", "3-6", 3.3 + 3.1 * (i - 2)) for i in range(3, 7)] + \
       [(f"TẦNG {i}", "7-8", 3.3 + 3.1 * (i - 2)) for i in (7, 8)] + [("TẦNG TUM", "tum", 25.0)]


def dem(nhom, keys):
    return {k: len(DL[nhom[0]][nhom[1]][k]) for k in keys if DL[nhom[0]][nhom[1]].get(k)}


acad = ac.ket_noi()
doc = ac.goi_lai(lambda: acad.ActiveDocument)
assert "KS32_PCCC_DUNG_LAI" in doc.Name, doc.Name
doc = acad_msp.nap_thu_vien(doc, TL, acad=acad)
msp = acad_msp.MSP(doc)


def goc(hang):
    return (-200000 + 5 * (W + 5000), -330000 - hang * (H + 5000))


# --- báo cháy ---
zones = []
for ten, k, _ in TANG:
    d = {x: len(DL[k]["bao_chay"][x]) for x in ("bao_khoi", "bao_nhiet", "nut_an", "chuong_den", "den_fire")
         if DL[k]["bao_chay"][x]}
    zones.append((ten, d))
G = goc(1)
tb.khung_a3(msp, G, TL, dict(TT, so_to="BC-06"))
aq = so_do.bao_chay(msp, G, zones, TL)
ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(*G), ac.diem(G[0] + W, G[1] + H)))
print("BC-06 xong, ắc quy:", {k: round(v, 3) for k, v in aq.items()}, flush=True)

# --- chữa cháy ---
G = goc(2)
tb.khung_a3(msp, G, TL, dict(TT, so_to="CC-06"))
so_do.chua_chay(msp, G, [(ten, cao, len(DL[k]["chua_chay"]["sprinkler"]), bool(DL[k]["chua_chay"]["hong"]))
                         for ten, k, cao in TANG],
                [("ĐIỆN CHÍNH", "EP-01", 12.6, 55), ("ĐIỆN DIESEL", "DP-02", 12.6, 55), ("BƠM BÙ", "JP", 0.7, 60)], TL)
ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(*G), ac.diem(G[0] + W, G[1] + H)))
print("CC-06 xong", flush=True)

# --- đèn sự cố, chỉ dẫn thoát nạn ---
G = goc(3)
tb.khung_a3(msp, G, TL, dict(TT, so_to="CS-06"))
cs = []
for ten, k, _ in TANG:
    d = DL[k]["chieu_sang"]
    huong = sum(1 for e in d["exit"] if e["huong"])
    cs.append((ten, {"exit": len(d["exit"]) - huong, "exit_huong": huong, "den_su_co": len(d["den_su_co"]),
                     "sdtn": len(d["sdtn"]), "sdtnp": len(d["sdtnp"]), "mat_na": len(d["mat_na"])}))
so_do.chieu_sang(msp, G, cs, TL)
ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(*G), ac.diem(G[0] + W, G[1] + H)))
print("CS-06 xong", flush=True)
ac.goi_lai(lambda: doc.Save())
print("Đã lưu", doc.FullName, "- tổng đối tượng mới:", msp.dem)
