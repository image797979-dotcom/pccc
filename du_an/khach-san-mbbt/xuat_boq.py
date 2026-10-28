"""Bảng khối lượng (BOQ) PCCC khách sạn MV YERSIN từ khối lượng đọc trên bản vẽ (khoi_luong_ban_ve.json)
và thông số thiết kế (thiet_ke.json).

  python xuat_boq.py   ->  BOQ_PCCC_YERSIN.xlsx

Tờ:
  TỔNG HỢP     – bảng khối lượng theo 4 hệ: KL bản vẽ (liên kết tờ theo tầng) × hệ số = KL đề xuất
  BC/SP/HN/CS  – khối lượng từng tầng (số đọc trên bản vẽ), cột TỔNG là công thức
  THÔNG SỐ     – cao độ tầng, hệ số hao hụt, giả thiết trục đứng (ô chữ xanh: sửa được)
  ĐỐI CHIẾU    – số trên bản vẽ so với số thiết kế
  GHI CHÚ      – nguồn số liệu, giả thiết, phần chưa bóc
"""
import json
import sys

sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

import ky_hieu as kh

KL = json.load(open("khoi_luong_ban_ve.json", encoding="utf-8"))
TK = json.load(open("thiet_ke.json", encoding="utf-8"))
TANG = ["HAM", "TRET", "LUNG", "T2", "T3", "T4", "T5", "T6", "T7", "SAN_THUONG"]
TEN = {"HAM": "Tầng hầm", "TRET": "Tầng trệt", "LUNG": "Tầng lửng", "T2": "Tầng 2", "T3": "Tầng 3",
       "T4": "Tầng 4", "T5": "Tầng 5", "T6": "Tầng 6", "T7": "Tầng 7", "SAN_THUONG": "Sân thượng"}
MO_TA = {v[0]: v[3] for v in kh.KY_HIEU.values()}
FONT = "Arial"
f_thuong, f_dam = Font(name=FONT, size=10), Font(name=FONT, size=10, bold=True)
f_nhap = Font(name=FONT, size=10, color="0000FF")          # số nhập tay / giả thiết
f_lien_ket = Font(name=FONT, size=10, color="008000")      # liên kết tờ khác
nen_td, nen_nhom = PatternFill("solid", fgColor="DDEBF7"), PatternFill("solid", fgColor="F2F2F2")
vien = Border(*(Side(style="thin", color="999999"),) * 4)
can_giua = Alignment(horizontal="center", vertical="center", wrap_text=True)
can_trai = Alignment(vertical="center", wrap_text=True)

wb = Workbook()
wb.calculation.fullCalcOnLoad = True  # Excel tính lại công thức khi mở


def o(ws, r, c, v, font=f_thuong, fmt=None, al=can_trai, fill=None):
    cell = ws.cell(r, c, v)
    cell.font, cell.border, cell.alignment = font, vien, al
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = fill
    return cell


def tieu_de(ws, r, cot):
    for c, v in enumerate(cot, 1):
        o(ws, r, c, v, f_dam, al=can_giua, fill=nen_td)


# ================= THÔNG SỐ =================
ts = wb.active
ts.title = "THÔNG SỐ"
o(ts, 1, 1, "THÔNG SỐ, GIẢ THIẾT (chữ xanh = nhập tay, sửa được; các tờ khác tự cập nhật)", f_dam, al=can_trai)
tieu_de(ts, 3, ["Tầng", "Cao độ sàn (m)", "Ghi chú"])
for i, t in enumerate(TANG):
    o(ts, 4 + i, 1, TEN[t])
    o(ts, 4 + i, 2, 3.5 * (i - 1), f_nhap, "0.00")
    o(ts, 4 + i, 3, "Chiều cao tầng 3,5 m (người dùng cung cấp); sàn trệt ±0,00" if i == 0 else "")
R_TS = 15
dong_ts = [
    ("Chiều cao trần treo (m)", 3.2, "Người dùng cung cấp"),
    ("Ống cấp ngang từ trạm bơm tới chân trục (m)", 15.0, "Giả thiết, trạm bơm ở tầng hầm – đo lại khi có mặt bằng trạm bơm"),
    ("Cao tâm họng trên sàn (m)", 1.25, "Thuyết minh: tâm họng cao +1,25 m"),
    ("Cáp ngang mỗi zone từ trục tới tủ trung tâm (m)", 15.0, "Giả thiết, tủ đặt tại lễ tân tầng trệt"),
    ("Hệ số hao hụt ống thép", 1.05, "Giả thiết 5 %"),
    ("Hệ số hao hụt cáp, ống luồn", 1.10, "Giả thiết 10 %"),
    ("Hệ số thiết bị", 1.00, "Thiết bị đếm trên bản vẽ, không cộng dự phòng"),
]
tieu_de(ts, R_TS - 1, ["Thông số", "Giá trị", "Nguồn / ghi chú"])
for i, (a, b, c) in enumerate(dong_ts):
    o(ts, R_TS + i, 1, a)
    o(ts, R_TS + i, 2, b, f_nhap, "0.00")
    o(ts, R_TS + i, 3, c)
TS = {k: f"'THÔNG SỐ'!$B${R_TS + i}" for i, k in enumerate(["tran", "ngang_bom", "tam_hong", "cap_ngang",
                                                              "hs_ong", "hs_cap", "hs_tb"])}
CAO = lambda t: f"'THÔNG SỐ'!$B${4 + TANG.index(t)}"
ts.column_dimensions["A"].width, ts.column_dimensions["B"].width, ts.column_dimensions["C"].width = 46, 12, 70

# ================= TỜ THEO TẦNG =================
# mỗi dòng: (khoá, tên, quy cách, ĐVT, giá trị theo tầng (dict) hoặc None nếu công thức riêng)
def dem(he, blk):
    return {t: KL[he]["block"].get(t, {}).get(blk, 0) for t in TANG}


def dai(he, layer):
    return {t: round(KL[he]["dai_mm"].get(t, {}).get(layer, 0) / 1000, 2) for t in TANG}


TO = {
    "BC": ("BÁO CHÁY", [
        ("dbk", MO_TA["PCCC_DBK"], "Đầu báo khói quang điện, loại thường", "cái", dem("bc", "PCCC_DBK")),
        ("dbn", MO_TA["PCCC_DBN"], "Đầu báo nhiệt cố định, loại thường", "cái", dem("bc", "PCCC_DBN")),
        ("na", MO_TA["PCCC_NA"], "Nút ấn báo cháy, loại thường", "cái", dem("bc", "PCCC_NA")),
        ("cd", MO_TA["PCCC_CD"], "Chuông 24 VDC + đèn chớp", "bộ", dem("bc", "PCCC_CD")),
        ("facp", MO_TA["PCCC_FACP"], "Tủ trung tâm 12 zone, 24 VDC", "tủ", dem("bc", "PCCC_FACP")),
        ("fire", MO_TA["PCCC_FIRE"], "Đèn chớp chỉ thị ngoài nhà", "cái", dem("bc", "PCCC_FIRE")),
        ("cap", "CÁP TÍN HIỆU BÁO CHÁY TRÊN MẶT BẰNG", "Cáp chống cháy 2x1,5 mm² (30 phút)", "m", dai("bc", "PCCC-CAP-BC")),
    ]),
    "SP": ("CHỮA CHÁY TỰ ĐỘNG SPRINKLER", [
        ("spr", MO_TA["PCCC_SPR"], "Đầu phun hướng xuống, 68°C, K=80, DN15", "cái", dem("spr", "PCCC_SPR")),
        ("van_spr", MO_TA["PCCC_VAN_SPR"], "Van khoá DN80 + công tắc dòng chảy, mỗi tầng 1 bộ", "bộ", dem("spr", "PCCC_VAN_SPR")),
    ] + [(f"ong{d}", f"ỐNG THÉP TRÁNG KẼM DN{d} (MẶT BẰNG)", "Ống STK sơn đỏ", "m", dai("spr", f"PCCC-ONG-SPR-D{d}"))
         for d in (25, 32, 40, 50, 65, 80)]),
    "HN": ("HỌNG NƯỚC VÁCH TƯỜNG + BÌNH CHỮA CHÁY", [
        ("fhr", "TỦ HỌNG NƯỚC CHỮA CHÁY VÁCH TƯỜNG", "Tủ 600x400x220; van góc DN50, vòi DN50 dài 20 m, lăng D13", "bộ", dem("hong", "PCCC_FHR")),
        ("abc", MO_TA["PCCC_ABC"], "Bình bột ABC 8 kg (MFZL8)", "bình", dem("hong", "PCCC_ABC")),
        ("co2", MO_TA["PCCC_CO2"], "Bình khí CO2 5 kg (MT5)", "bình", dem("hong", "PCCC_CO2")),
        ("tiep", MO_TA["PCCC_HONG_TIEP"], "Họng tiếp nước xe chữa cháy 2 cửa DN65", "bộ", dem("hong", "PCCC_HONG_TIEP")),
        ("nhanh50", "ỐNG NHÁNH DN50 VÀO TỦ HỌNG (MẶT BẰNG)", "Ống STK sơn đỏ", "m", dai("hong", "PCCC-ONG-HONG-D50")),
    ]),
    "CS": ("CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN", [
        ("exit", MO_TA["PCCC_EXIT"], "Đèn EXIT 1 mặt, pin 2 h", "bộ", dem("cs", "PCCC_EXIT")),
        ("exith", MO_TA["PCCC_EXIT_HUONG"], "Đèn EXIT chỉ hướng, pin 2 h", "bộ", dem("cs", "PCCC_EXIT_HUONG")),
        ("dsc", MO_TA["PCCC_DEN_SC"], "Đèn sự cố 2 bóng, pin 2 h", "bộ", dem("cs", "PCCC_DEN_SC")),
        ("sdtn", MO_TA["PCCC_SDTN"], "Sơ đồ thoát nạn tầng 600x400 mm", "tấm", dem("cs", "PCCC_SDTN")),
        ("sdtnp", MO_TA["PCCC_SDTNP"], "Sơ đồ thoát nạn phòng 400x300 mm", "tấm", dem("cs", "PCCC_SDTNP")),
    ]),
}
REF = {}  # khoá -> ô tổng trên tờ theo tầng
for ky, (ten_he, dong) in TO.items():
    ws = wb.create_sheet(ky)
    o(ws, 1, 1, f"KHỐI LƯỢNG {ten_he} THEO TẦNG (đọc trên bản vẽ {ky})", f_dam, al=can_trai)
    tieu_de(ws, 3, ["STT", "Hạng mục", "Quy cách", "ĐVT"] + [TEN[t] for t in TANG] + ["TỔNG"])
    for i, (k, ten, qc, dvt, gt) in enumerate(dong):
        r = 4 + i
        o(ws, r, 1, i + 1, al=can_giua)
        o(ws, r, 2, ten)
        o(ws, r, 3, qc)
        o(ws, r, 4, dvt, al=can_giua)
        fmt = "0.0" if dvt == "m" else "0"
        for j, t in enumerate(TANG):
            o(ws, r, 5 + j, gt[t], f_nhap, fmt, can_giua)
        c_tong = 5 + len(TANG)
        o(ws, r, c_tong, f"=SUM({L(5)}{r}:{L(c_tong - 1)}{r})", f_dam, fmt, can_giua)
        REF[k] = f"'{ky}'!${L(c_tong)}${r}" if " " in ky else f"{ky}!${L(c_tong)}${r}"
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 5, 44
    ws.column_dimensions["C"].width, ws.column_dimensions["D"].width = 34, 6
    for j in range(len(TANG) + 1):
        ws.column_dimensions[L(5 + j)].width = 10
    ws.freeze_panes = "E4"
    o(ws, 5 + len(dong), 2, "Số chữ xanh: đọc trực tiếp trên bản vẽ (block, chiều dài tim ống/cáp theo layer).",
      Font(name=FONT, size=9, italic=True))

# ================= TỔNG HỢP =================
th = wb.create_sheet("TỔNG HỢP", 0)
tl = TK["thuy_luc"]
o(th, 1, 1, "BẢNG TỔNG HỢP KHỐI LƯỢNG HỆ THỐNG PCCC – KHÁCH SẠN MV YERSIN", Font(name=FONT, size=13, bold=True))
o(th, 2, 1, "7 Yersin, Bến Thành, Hồ Chí Minh – khối lượng đọc từ 4 bản vẽ PCCC-01…04 (thiết kế sơ bộ)",
  Font(name=FONT, size=10, italic=True))
tieu_de(th, 4, ["STT", "Hạng mục / vật tư", "Quy cách", "ĐVT", "KL bản vẽ", "Hệ số", "KL đề xuất", "Ghi chú"])
r = 5


def nhom(ma, ten):
    global r
    for c in range(1, 9):
        o(th, r, c, None, fill=nen_nhom)
    o(th, r, 1, ma, f_dam, al=can_giua, fill=nen_nhom)
    o(th, r, 2, ten, f_dam, fill=nen_nhom)
    r += 1


def dong(stt, ten, qc, dvt, kl, hs, ghi="", lien_ket=True):
    """kl: công thức/giá trị; hs: tham chiếu hệ số."""
    global r
    o(th, r, 1, stt, al=can_giua)
    o(th, r, 2, ten)
    o(th, r, 3, qc)
    o(th, r, 4, dvt, al=can_giua)
    fmt = "0.0" if dvt == "m" else "0"
    o(th, r, 5, kl, f_lien_ket if lien_ket else f_nhap if not str(kl).startswith("=") else f_thuong, fmt, can_giua)
    o(th, r, 6, f"={hs}", f_lien_ket, "0.00", can_giua)
    o(th, r, 7, f"=ROUNDUP(E{r}*F{r},{1 if dvt == 'm' else 0})", f_dam, fmt, can_giua)
    o(th, r, 8, ghi)
    r += 1
    return r - 1


so_zone = len(TANG)
# ---- A. BÁO CHÁY ----
nhom("A", "HỆ THỐNG BÁO CHÁY TỰ ĐỘNG")
dong(1, "Tủ trung tâm báo cháy", "12 zone, 24 VDC, kèm bộ sạc", "tủ", f"={REF['facp']}", TS["hs_tb"], "Đặt tại lễ tân tầng trệt")
dong(2, "Ắc quy dự phòng tủ trung tâm", "12 V – 30 Ah", "bình", 2, TS["hs_tb"],
     "2 bình nối tiếp 24 VDC, theo bảng tính Phụ lục C TCVN 7568-14:2025 (tờ BC-11)", lien_ket=False)
dong(3, "Đầu báo khói", "Quang điện, loại thường", "cái", f"={REF['dbk']}", TS["hs_tb"])
dong(4, "Đầu báo nhiệt", "Cố định, loại thường", "cái", f"={REF['dbn']}", TS["hs_tb"], "Bếp BOH tầng trệt")
dong(5, "Nút ấn báo cháy", "Loại thường", "cái", f"={REF['na']}", TS["hs_tb"])
dong(6, "Chuông báo cháy + đèn", "24 VDC", "bộ", f"={REF['cd']}", TS["hs_tb"])
dong(7, "Đèn báo cháy ngoài nhà (FIRE)", "", "cái", f"={REF['fire']}", TS["hs_tb"])
dong(8, "Điện trở cuối line (EOL)", "", "cái", so_zone, TS["hs_tb"], "1 cái/zone, 10 zone (tờ BC-11)", lien_ket=False)
r_cap = dong(9, "Cáp tín hiệu báo cháy trên mặt bằng", "Cáp chống cháy 2x1,5 mm²", "m", f"={REF['cap']}", TS["hs_cap"],
             "Chiều dài tim cáp trên bản vẽ")
cao_tret = CAO("TRET")
truc_cap = "+".join(f"ABS({CAO(t)}-{cao_tret})" for t in TANG)
r_truc = dong(10, "Cáp trục từ các zone về tủ trung tâm", "Cáp chống cháy 2x1,5 mm²", "m",
              f"=({truc_cap})+{so_zone}*{TS['cap_ngang']}", TS["hs_cap"],
              "Tính: Σ chênh cao mỗi tầng tới tầng trệt + cáp ngang mỗi zone (tờ THÔNG SỐ)", lien_ket=False)
dong(11, "Ống luồn cáp PVC Ø20", "PVC cứng Ø20 + phụ kiện", "m", f"=E{r_cap}+E{r_truc}", TS["hs_cap"],
     "Cáp đi trong ống PVC Ø20 (sơ đồ nguyên lý)", lien_ket=False)

# ---- B. SPRINKLER ----
nhom("B", "HỆ THỐNG CHỮA CHÁY TỰ ĐỘNG SPRINKLER")
dong(1, "Đầu phun sprinkler", "Hướng xuống, 68°C, K=80, DN15", "cái", f"={REF['spr']}", TS["hs_tb"], "Nhóm nguy hiểm 1")
dong(2, "Van khoá + công tắc dòng chảy tầng", "DN80", "bộ", f"={REF['van_spr']}", TS["hs_tb"], "Mỗi tầng 1 bộ")
dong(3, "Cụm van báo động (trạm kiểm tra)", "DN100", "bộ", 1, TS["hs_tb"], "Tại trạm bơm (sơ đồ nguyên lý)", lien_ket=False)
for i, d in enumerate((25, 32, 40, 50, 65, 80)):
    dong(4 + i, f"Ống thép tráng kẽm DN{d}", "STK sơn đỏ", "m", f"={REF[f'ong{d}']}", TS["hs_ong"], "Mặt bằng, chọn DN sơ bộ")
r_truc_spr = dong(10, "Ống thép tráng kẽm DN100 – trục đứng + ống cấp", "STK sơn đỏ", "m",
                  f"=({CAO('SAN_THUONG')}-{CAO('HAM')})+{TS['tran']}+{TS['ngang_bom']}", TS["hs_ong"],
                  "Tính: chênh cao hầm → sân thượng + trần + ống cấp ngang (tờ THÔNG SỐ)", lien_ket=False)

# ---- C. HỌNG NƯỚC + BÌNH ----
nhom("C", "HỆ THỐNG HỌNG NƯỚC VÁCH TƯỜNG, BÌNH CHỮA CHÁY")
dong(1, "Tủ họng nước chữa cháy vách tường", "600x400x220; van góc DN50, vòi DN50-20 m, lăng D13", "bộ",
     f"={REF['fhr']}", TS["hs_tb"], "1 họng × 2,5 l/s (QCVN 10:2025/BCA, Bảng H.5)")
dong(2, "Bình chữa cháy bột ABC 8 kg", "MFZL8", "bình", f"={REF['abc']}", TS["hs_tb"], "Kèm tủ họng + cửa thang")
dong(3, "Bình chữa cháy CO2 5 kg", "MT5", "bình", f"={REF['co2']}", TS["hs_tb"])
dong(4, "Họng tiếp nước xe chữa cháy", "2 cửa DN65", "bộ", f"={REF['tiep']}", TS["hs_tb"], "Mặt ngoài tầng trệt")
dong(5, "Ống thép tráng kẽm DN50 – nhánh vào tủ họng", "STK sơn đỏ", "m", f"={REF['nhanh50']}", TS["hs_ong"])
dong(6, "Ống thép tráng kẽm DN100 – trục đứng họng + ống cấp", "STK sơn đỏ", "m",
     f"=({CAO('T7')}-{CAO('HAM')})+{TS['tam_hong']}+{TS['ngang_bom']}", TS["hs_ong"],
     "Tính: chênh cao hầm → tầng 7 + tâm họng + ống cấp ngang", lien_ket=False)

# ---- D. TRẠM BƠM, BỂ ----
nhom("D", "TRẠM BƠM, BỂ NƯỚC CHỮA CHÁY")
dong(1, "Bơm chữa cháy động cơ điện", f"Q = {tl['Q_bom_l_s']} l/s; H = {tl['H_bom_m']} m", "bộ", 1, TS["hs_tb"],
     "Thông số sơ bộ (thuỷ lực sơ bộ, tờ sơ đồ nguyên lý)", lien_ket=False)
dong(2, "Bơm chữa cháy động cơ diesel (dự phòng)", f"Q = {tl['Q_bom_l_s']} l/s; H = {tl['H_bom_m']} m", "bộ", 1,
     TS["hs_tb"], lien_ket=False)
dong(3, "Bơm bù áp", f"Q = 1,0 l/s; H = {tl['H_bom_m'] + 5} m", "bộ", 1, TS["hs_tb"], lien_ket=False)
dong(4, "Tủ điều khiển bơm chữa cháy", "Tự động / bằng tay, khởi động ≤ 30 s", "tủ", 1, TS["hs_tb"], lien_ket=False)
dong(5, "Bể nước chữa cháy", f"≥ {tl['V_be_chon_m3']} m³", "bể", 1, TS["hs_tb"],
     "Chưa gồm nước chữa cháy ngoài nhà; xây dựng theo hồ sơ kết cấu", lien_ket=False)

# ---- E. CHIẾU SÁNG ----
nhom("E", "CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN")
dong(1, "Đèn EXIT", "1 mặt, pin 2 h", "bộ", f"={REF['exit']}", TS["hs_tb"], "Trên cửa ra buồng thang")
dong(2, "Đèn EXIT chỉ hướng", "Pin 2 h", "bộ", f"={REF['exith']}", TS["hs_tb"])
dong(3, "Đèn chiếu sáng sự cố", "2 bóng, pin 2 h", "bộ", f"={REF['dsc']}", TS["hs_tb"])
dong(4, "Sơ đồ chỉ dẫn thoát nạn tầng", "600x400 mm", "tấm", f"={REF['sdtn']}", TS["hs_tb"])
dong(5, "Sơ đồ chỉ dẫn thoát nạn phòng", "400x300 mm", "tấm", f"={REF['sdtnp']}", TS["hs_tb"])

o(th, r + 1, 2, "Chữ xanh lá: liên kết tờ khối lượng theo tầng; chữ xanh dương: số nhập tay/tính từ giả thiết (xem tờ "
  "THÔNG SỐ, GHI CHÚ). KL đề xuất = KL bản vẽ × hệ số, làm tròn lên.", Font(name=FONT, size=9, italic=True))
th.merge_cells(start_row=r + 1, start_column=2, end_row=r + 1, end_column=8)
for c, w in zip("ABCDEFGH", (6, 46, 40, 7, 12, 8, 12, 56)):
    th.column_dimensions[c].width = w
th.freeze_panes = "A5"
th.print_title_rows = "4:4"
th.page_setup.orientation, th.page_setup.fitToWidth = "landscape", 1

# ================= ĐỐI CHIẾU =================
dc = wb.create_sheet("ĐỐI CHIẾU")
o(dc, 1, 1, "ĐỐI CHIẾU SỐ LƯỢNG ĐỌC TRÊN BẢN VẼ VỚI SỐ LIỆU THIẾT KẾ (thiet_ke.json)", f_dam)
tieu_de(dc, 3, ["Thiết bị", "Bản vẽ", "Thiết kế", "Chênh lệch"])
s = lambda f: sum(f(T) for T in TK["tang"].values())
doi = [("Đầu báo khói", "dbk", s(lambda T: len(T["bc"].get("bao_khoi", [])))),
       ("Đầu báo nhiệt", "dbn", s(lambda T: len(T["bc"].get("bao_nhiet", [])))),
       ("Nút ấn", "na", s(lambda T: len(T["bc"].get("nut_an", [])))),
       ("Chuông + đèn", "cd", s(lambda T: len(T["bc"].get("chuong_den", [])))),
       ("Đầu phun sprinkler", "spr", s(lambda T: len(T["spr"]))),
       ("Tủ họng", "fhr", s(lambda T: len(T["hong"]))),
       ("Bình ABC", "abc", s(lambda T: len(T["binh"]))),
       ("Bình CO2", "co2", s(lambda T: len(T["binh"]))),
       ("Đèn EXIT", "exit", s(lambda T: len(T["cs"].get("exit", [])))),
       ("Đèn EXIT chỉ hướng", "exith", s(lambda T: len(T["cs"].get("exit_huong", [])))),
       ("Đèn sự cố", "dsc", s(lambda T: len(T["cs"].get("den_su_co", [])))),
       ("Sơ đồ thoát nạn tầng", "sdtn", s(lambda T: len(T["cs"].get("sdtn", [])))),
       ("Sơ đồ thoát nạn phòng", "sdtnp", s(lambda T: len(T["cs"].get("sdtnp", []))))]
for i, (ten, k, so_tk) in enumerate(doi):
    rr = 4 + i
    o(dc, rr, 1, ten)
    o(dc, rr, 2, f"={REF[k]}", f_lien_ket, "0", can_giua)
    o(dc, rr, 3, so_tk, f_nhap, "0", can_giua)
    o(dc, rr, 4, f"=B{rr}-C{rr}", f_dam, "0;-0;\"khớp\"", can_giua)
dc.column_dimensions["A"].width = 30
for c in "BCD":
    dc.column_dimensions[c].width = 12

# ================= GHI CHÚ =================
gc = wb.create_sheet("GHI CHÚ")
ghi = [
    "NGUỒN SỐ LIỆU",
    "- Thiết bị, chiều dài ống và cáp đọc trực tiếp từ 4 bản vẽ YERSIN/PCCC-01…04 (model space, layer PCCC*): đếm block, "
    "cộng chiều dài tim ống/cáp theo layer, chia tầng theo cao độ model. Bỏ block mẫu trong bảng ký hiệu và tờ sơ đồ.",
    "- Thông số bơm, bể: thuỷ lực sơ bộ (nhóm 1, cường độ 0,08 l/s.m², diện tích tính toán 60 m², đầu phun K80, "
    "áp tối thiểu 0,5 bar; họng 1 × 2,5 l/s). Phải tính lại theo TCVN 7336:2021 trước khi đặt hàng.",
    "GIẢ THIẾT (sửa ở tờ THÔNG SỐ)",
    "- Trục đứng sprinkler, họng và cáp trục báo cháy không vẽ trên mặt bằng: tính từ cao độ tầng 3,5 m, cộng ống cấp "
    "ngang 15 m từ trạm bơm và 15 m cáp ngang mỗi zone.",
    "- Hao hụt: ống thép 5 %, cáp và ống luồn 10 %; thiết bị không cộng dự phòng.",
    "CHƯA BÓC (cần bổ sung khi triển khai thi công)",
    "- Phụ kiện ống (cút, tê, côn, măng sông), giá treo, sơn, van xả, van xả khí, đồng hồ áp, khớp nối mềm trạm bơm.",
    "- Ống hút/đẩy trong trạm bơm, ống tràn, van phao bể.",
    "- Cáp cấp nguồn cho tủ trung tâm, tủ bơm, đèn sự cố/EXIT; hộp nối, đế đầu báo nếu tách riêng.",
    "- Công tác lắp đặt, thử áp, nghiệm thu.",
    "LƯU Ý",
    "- Số liệu thiết kế sơ bộ; kỹ sư PCCC có chứng chỉ cần kiểm tra trước khi thẩm duyệt và lập dự toán.",
]
for i, d in enumerate(ghi):
    o(gc, 1 + i, 1, d, f_dam if d.isupper() or d == d.upper() else f_thuong)
gc.column_dimensions["A"].width = 140

wb.save("BOQ_PCCC_YERSIN.xlsx")
print("đã lưu BOQ_PCCC_YERSIN.xlsx")
