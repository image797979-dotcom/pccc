"""Các tờ thuyết minh theo hồ sơ mẫu KS 32 Dã Tượng (tờ 2, 12, 14, 30, 32), thay bằng số liệu khách sạn mini 34 NVM.

Nội dung chép theo hồ sơ mẫu (đã đổi font VNI sang Unicode bằng vni.py), sửa các chỗ sai của bản mẫu
(trinh-bay-ban-ve.md mục 9) và lấy mọi con số từ thiet_ke.json để thuyết minh, sơ đồ, mặt bằng khớp nhau.
Mỗi hàm vẽ một tờ A3 vào khung đã có ở góc G (model, tỷ lệ TL).
"""
import math
import sys

import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import ky_hieu as kh
import trinh_bay as tb

# ---- số liệu công trình (diện tích sàn đo trên mặt bằng kiến trúc, cao tầng theo dim mặt cắt) ----
# (mã tầng, tên, công năng, diện tích sàn m², chiều cao tầng m)
TANG = [
    ("HAM", "Tầng hầm", "BÃI XE, KHO, KỸ THUẬT, BỂ NƯỚC", 120.6, 3.0),
    ("TRET", "Tầng trệt", "SẢNH, COFFEE, CO-WORKING", 207.0, 3.7),
    ("LUNG", "Tầng lửng", "KHÁCH SẠN", 193.5, 3.3),
    ("T2", "Tầng 2", "KHÁCH SẠN", 207.0, 3.5),
    ("T3", "Tầng 3", "KHÁCH SẠN", 207.0, 3.3),
    ("T4", "Tầng 4", "KHÁCH SẠN", 179.0, 3.3),
    ("T5", "Tầng 5", "KHÁCH SẠN, GIẶT LÀ", 117.3, 3.0),
    ("T6", "Tầng 6", "KHÁCH SẠN, BẾP", 55.1, 2.4),
]
DIEN_TICH = {m: S for m, _, _, S, _ in TANG}
H_PCCC = 20.1          # m: cao độ sàn tầng 6 so với cao độ đường xe chữa cháy (giả thiết ±0,000)
H_CONG_TRINH = 22.5    # m: cao độ đỉnh mái
KHOI_TICH = sum(S * h for _, _, _, S, h in TANG)
TC_CHUNG = [
    "- QCVN 06:2022/BXD - SỬA ĐỔI 01:2023: QUY CHUẨN KỸ THUẬT QUỐC GIA VỀ AN TOÀN CHÁY CHO NHÀ VÀ CÔNG TRÌNH.",
    "- QCVN 10:2025/BCA: PHƯƠNG TIỆN PHÒNG CHÁY CHỮA CHÁY CHO NHÀ VÀ CÔNG TRÌNH - YÊU CẦU THIẾT KẾ.",
]


def _cot(msp, G, TL, x_mm, y_mm, dong, rong_mm=170, co=2.5, tieu_de=None):
    """Khối chữ tại (x_mm, y_mm) giấy tính từ góc dưới-trái tờ; trả về y giấy của dòng cuối."""
    x0, y0, _, y1 = tb.ghi_chu(msp, (G[0] + x_mm * TL, G[1] + y_mm * TL), dong, TL, tieu_de=tieu_de, co=co,
                               rong_mm=rong_mm)
    return (x0 - G[0]) / TL, (y0 - G[1]) / TL


def to_quy_mo(msp, G):
    """Tờ 2 bản mẫu: QUY MÔ CÔNG TRÌNH + KHỐI TÍCH + vật liệu hoàn thiện + chiều cao + nguồn nước ngoài nhà."""
    TL = kh.TY_LE
    hang = [["STT", "CÔNG TRÌNH", "CHIỀU CAO\nPCCC (m)", "KHỐI TÍCH\n(m3)", "NHÓM NHÀ", "BẬC CHỊU LỬA",
             "CẤP NGUY HIỂM\nCHÁY KẾT CẤU"],
            ["", "", "(H)", "(S*H)", "QCVN 06:2022/BXD\nBẢNG 6", "QCVN 06:2022/BXD\nBẢNG 4", "QCVN 06:2022/BXD\nBẢNG 5"],
            ["1", "KHÁCH SẠN MINI\n34 NVM", f"{H_PCCC:.1f}", f"{KHOI_TICH:,.0f}", "F1.2", "II", "S0"]]
    tb.bang(msp, (G[0] + 12 * TL, G[1] + 285 * TL), [10, 40, 24, 24, 34, 34, 34], hang, TL, cao_hang_mm=9, co=2.2,
            tieu_de="QUY MÔ CÔNG TRÌNH", mau_vien=kh.DO)
    tb.bang_quy_mo(msp, (G[0] + 12 * TL, G[1] + 236 * TL), [(ten, cn, S, h) for _, ten, cn, S, h in TANG], TL)
    _cot(msp, G, TL, 225, 236, [
        "+ VẬT LIỆU HOÀN THIỆN, TRANG TRÍ TƯỜNG VÀ TRẦN (BAO GỒM CẢ TẤM TRẦN TREO NẾU CÓ), VẬT LIỆU ỐP LÁT, "
        "VẬT LIỆU PHỦ SÀN TRÊN ĐƯỜNG THOÁT NẠN TUÂN THỦ YÊU CẦU TẠI BẢNG B.8 - PHỤ LỤC B - QCVN 06:2022/BXD "
        "VÀ SỬA ĐỔI 01:2023.",
        "+ VẬT LIỆU HOÀN THIỆN, TRANG TRÍ, VẬT LIỆU ỐP LÁT VÀ VẬT LIỆU PHỦ SÀN TRONG CÁC GIAN PHÒNG CHUNG, "
        "GIAN PHÒNG RIÊNG TUÂN THỦ YÊU CẦU TẠI BẢNG B.9 - PHỤ LỤC B - QCVN 06:2022/BXD VÀ SỬA ĐỔI 01:2023.",
        f"+ CHIỀU CAO CÔNG TRÌNH: {H_CONG_TRINH:.1f} m (ĐỈNH MÁI +{H_CONG_TRINH:.3f}).",
        f"+ CHIỀU CAO PCCC: {H_PCCC:.1f} m (SÀN TẦNG 6 +{H_PCCC:.3f}, TÍNH TỪ CAO ĐỘ ĐƯỜNG XE CHỮA CHÁY ±0,000).",
        "+ SỐ TẦNG: 1 HẦM + TRỆT + LỬNG + 6 TẦNG (TẦNG 2 ĐẾN TẦNG 6).",
        "+ TRỤ CẤP NƯỚC CHỮA CHÁY ĐÔ THỊ: LƯU LƯỢNG ...... L/S, CÁCH CÔNG TRÌNH ...... m (≤ 200 m) - BỔ SUNG THEO "
        "KHẢO SÁT HIỆN TRẠNG.",
    ], rong_mm=125, co=2.6, tieu_de="-VẬT LIỆU HOÀN THIỆN VÀ CHIỀU CAO:")
    tb.tieu_de_to(msp, "QUY MÔ CÔNG TRÌNH", (G[0] + 190 * TL, G[1] + 12 * TL), TL)


def to_tm_bao_chay(msp, G, TK, aq):
    """Thuyết minh báo cháy: tiêu chuẩn, cấu hình hệ, số lượng thiết bị, ắc quy, ghi chú lắp đặt (tờ 12 bản mẫu)."""
    TL = kh.TY_LE
    dem = {k: sum(len(T["bc"].get(k, [])) for T in TK["tang"].values())
           for k in ("bao_khoi", "bao_nhiet", "nut_an", "chuong_den", "tu_tt", "den_fire")}
    so_zone = len(TK["tang"])
    _, y = _cot(msp, G, TL, 12, 285, [
        "1. TIÊU CHUẨN ÁP DỤNG:"] + TC_CHUNG + [
        "- TCVN 7568-1:2025: HỆ THỐNG BÁO CHÁY - BỐ TRÍ ĐẦU BÁO CHÁY (MỤC 5.9).",
        "- TCVN 7568-14:2025: HỆ THỐNG BÁO CHÁY - THIẾT KẾ, LẮP ĐẶT, VẬN HÀNH; PHỤ LỤC C TÍNH NGUỒN ẮC QUY.",
        "2. CẤU HÌNH HỆ THỐNG:",
        f"- TRUNG TÂM BÁO CHÁY THƯỜNG 10 KÊNH (ZONE), SỬ DỤNG {so_zone} KÊNH: MỖI TẦNG 01 KÊNH TỪ TẦNG HẦM "
        "ĐẾN TẦNG 6, 02 KÊNH DỰ PHÒNG. TỦ ĐẶT TẠI SẢNH LỄ TÂN TẦNG TRỆT, CÓ NGƯỜI TRỰC 24/24.",
        f"- ĐẦU BÁO KHÓI: {dem['bao_khoi']} CÁI; ĐẦU BÁO NHIỆT (BẾP, BÃI XE): {dem['bao_nhiet']} CÁI; "
        f"NÚT NHẤN KHẨN: {dem['nut_an']} CÁI; CHUÔNG + ĐÈN: {dem['chuong_den']} BỘ; "
        f"ĐÈN BÁO CHÁY NGOÀI NHÀ: {dem['den_fire']} CÁI.",
        "- TRẦN ≤ 3,5 m: ĐẦU BÁO KHÓI BẢO VỆ ≤ 85 m², CÁCH NHAU ≤ 9 m, CÁCH TƯỜNG ≤ 4,5 m; ĐẦU BÁO NHIỆT "
        "≤ 25 m², CÁCH NHAU ≤ 5 m, CÁCH TƯỜNG ≤ 2,5 m.",
        "- KHÔNG BỐ TRÍ ĐẦU BÁO TRONG WC, BUỒNG THANG BỘ, GIẾNG THANG MÁY, THANG XOẮN. KHÔNG BỐ TRÍ CÁP ĐIỆN "
        "TRÊN TRẦN NHÀ WC.",
        "- CÁP TÍN HIỆU 2C x 1,5 mm² CHỐNG CHÁY 30 PHÚT ĐI TRONG ỐNG PVC Ø20; CÁP DẪN VỀ TRUNG TÂM 2C x 1 mm² "
        "CHỐNG CHÁY.",
        "- TÍN HIỆU BÁO CHÁY ĐƯỢC TRUYỀN VỀ HỆ THỐNG GIÁM SÁT PCCC & CNCH, ĐIỀU KHIỂN TỦ BƠM CHỮA CHÁY VÀ NGẮT "
        "ĐIỆN SINH HOẠT, GIỮ NGUỒN CHO CÁC HỆ THỐNG PCCC.",
        "3. NGUỒN ĐIỆN:",
        "- NGUỒN CHÍNH 220 V AC TỪ TỦ ĐIỆN TỔNG; NGUỒN DỰ PHÒNG ẮC QUY 24 V DC.",
        f"- ẮC QUY TÍNH THEO PHỤ LỤC C TCVN 7568-14:2025 (24 h THƯỜNG TRỰC + 30 PHÚT BÁO CHÁY): "
        f"C20 = {aq['C20']:.2f} Ah -> CHỌN 02 ẮC QUY 12 V - {aq['chon_Ah']} Ah NỐI TIẾP. "
        "DÒNG THIẾT BỊ LẤY THEO HỒ SƠ MẪU, CẬP NHẬT THEO CATALOGUE THIẾT BỊ THỰC TẾ.",
    ], rong_mm=160, co=2.7, tieu_de="THUYẾT MINH HỆ THỐNG BÁO CHÁY TỰ ĐỘNG")
    _cot(msp, G, TL, 205, 285, [
        "TỦ TRUNG TÂM BÁO CHÁY:",
        "- KHOẢNG CÁCH GIỮA TRUNG TÂM BÁO CHÁY VÀ TRẦN NHÀ BẰNG VẬT LIỆU CHÁY KHÔNG NHỎ HƠN 1,0 m "
        "(TCVN 7568-14:2025).",
        "- LẮP ĐẶT TRÊN TƯỜNG, CÓ KHÔNG GIAN TRỐNG XUNG QUANH; CÁCH SÀN TỪ ≥ 0,75 m ĐẾN ≤ 1,85 m; "
        "KHÔNG GIAN TRỐNG MẶT TRƯỚC TỦ ≥ 1,5 m.",
        "ĐÈN BÁO CHÁY NGOÀI NHÀ:",
        "- CHỮ \"FIRE\" ĐẶT CẠNH ĐÈN CHỈ THỊ, CHIỀU CAO CHỮ 100 mm, NỀN VÀNG CHỮ ĐỎ; ĐÈN KẾT NỐI VỚI TỦ "
        "TRUNG TÂM.",
        "NÚT NHẤN, CHUÔNG ĐÈN:",
        "- ĐẶT TẠI HÀNH LANG, SẢNH CẠNH LỐI VÀO THANG BỘ VÀ LỐI RA NGOÀI NHÀ; KHOẢNG CÁCH GIỮA CÁC NÚT NHẤN "
        "≤ 45 m; TÂM NÚT NHẤN CAO 1,2-1,5 m.",
        "ĐẦU BÁO CHÁY:",
        "- ĐẦU BÁO LẮP DƯỚI TRẦN GIẢ; KHÔNG GIAN TRÊN TRẦN TREO CHỈ CÓ CÁP CHIẾU SÁNG, THÔNG TIN NÊN KHÔNG "
        "PHẢI TRANG BỊ ĐẦU BÁO (CHÚ THÍCH (2) - BẢNG A.2 PHỤ LỤC A QCVN 10:2025/BCA).",
        "- KHOẢNG CÁCH TỪ ĐẦU BÁO KHÓI ĐẾN MÉP CỬA CẤP KHÔNG KHÍ ≥ 0,4 m (TCVN 7568-1:2025 MỤC 5.9.1.1.4 b); "
        "ĐẦU BÁO NHIỆT ≥ 0,6 m (MỤC 5.9.2.1.4 b).",
        "- ĐẦU BÁO CÁCH THIẾT BỊ ĐIỆN, ĐÈN CHIẾU SÁNG ≥ 0,5 m.",
        "CHỐNG CHÁY LAN:",
        "- ỐNG KỸ THUẬT, THANG MÁNG CÁP XUYÊN TƯỜNG, SÀN ĐƯỢC CHÈN KÍN BẰNG HỢP CHẤT NGĂN CHÁY LAN, "
        "BÔNG KHOÁNG VÀ LỚP VỮA HOÀN THIỆN.",
    ], rong_mm=140, co=2.7, tieu_de="GHI CHÚ LẮP ĐẶT:")
    tb.tieu_de_to(msp, "THUYẾT MINH HỆ THỐNG BÁO CHÁY", (G[0] + 190 * TL, G[1] + 12 * TL), TL)


def to_tm_chua_chay(msp, G, TK):
    """Tờ 14 bản mẫu: thuyết minh chữa cháy (không có sprinkler: bỏ mục chữa cháy tự động)."""
    TL = kh.TY_LE
    tl = TK["thuy_luc"]
    q, H, V = tl["Q_hong_l_s"], tl["H_bom_m"], tl["V_be_chon_m3"]
    thanh_phan = tl["thanh_phan_hong"]
    _, y = _cot(msp, G, TL, 12, 285, [
        "1. TIÊU CHUẨN ÁP DỤNG:"] + TC_CHUNG + [
        "- TCVN 2622:1995: PHÒNG CHÁY, CHỐNG CHÁY CHO NHÀ VÀ CÔNG TRÌNH - YÊU CẦU THIẾT KẾ (PHẦN CÒN HIỆU LỰC).",
        "- TCVN 4513:1998: CẤP NƯỚC BÊN TRONG - YÊU CẦU THIẾT KẾ.",
        "2. ĐƯỜNG ỐNG SƠN MÀU ĐỎ VÀ ĐÁNH SỐ 1; CÁC ỐNG CHỮA CHÁY THI CÔNG BẰNG ỐNG THÉP TRÁNG KẼM (STK).",
        "3. HỆ THỐNG CHỮA CHÁY CỦA CÔNG TRÌNH BAO GỒM:",
        "- HỆ THỐNG MÁY BƠM CHỮA CHÁY ĐẶT TẠI PHÒNG KỸ THUẬT TẦNG HẦM.",
        "- HỆ THỐNG CHỮA CHÁY VÁCH TƯỜNG: TỦ CHỮA CHÁY TRONG NHÀ, HỌNG CHỜ TIẾP NƯỚC XE CHỮA CHÁY.",
        "- BÌNH CHỮA CHÁY XÁCH TAY (BỘT ABC 8 kg, CO2 5 kg).",
        "- CÔNG TRÌNH KHÔNG TRANG BỊ HỆ THỐNG CHỮA CHÁY TỰ ĐỘNG SPRINKLER (THEO PHÂN LOẠI CỦA CHỦ ĐẦU TƯ, "
        "KỸ SƯ PCCC ĐỐI CHIẾU PHỤ LỤC QCVN 10:2025/BCA).",
        "4. HỆ THỐNG MÁY BƠM ĐƯỢC CẤP NGUỒN TỪ LƯỚI ĐIỆN QUỐC GIA; BƠM DỰ PHÒNG CHẠY DẦU DIESEL.",
        "- HỆ THỐNG BƠM HOẠT ĐỘNG Ở 02 CHẾ ĐỘ: TAY VÀ TỰ ĐỘNG; THỜI GIAN KHỞI ĐỘNG BƠM KHÔNG QUÁ 30 GIÂY.",
        "- CHẾ ĐỘ TAY ĐIỀU KHIỂN BẰNG NÚT NHẤN ON/OFF VÀ VAN KHÓA; CHẾ ĐỘ TỰ ĐỘNG ĐIỀU KHIỂN BẰNG CÔNG TẮC "
        "ÁP LỰC.",
        "5. HỆ CHỮA CHÁY VÁCH TƯỜNG:",
        "- LƯU LƯỢNG NƯỚC HỌNG CHỮA CHÁY TRONG NHÀ XÁC ĐỊNH THEO PHỤ LỤC H, BẢNG H.5 QCVN 10:2025/BCA.",
        "- TỦ CHỮA CHÁY VÁCH TƯỜNG KT (600 x 400 x 220 mm) LẮP Ở ĐỘ CAO +1,25 m (TÍNH TỪ NỀN HOÀN THIỆN TỚI TÂM "
        "HỌNG), GỒM 01 VAN ĐÓNG MỞ DN50, 01 VAN GIẢM ÁP DN50, 01 LĂNG PHUN D13 mm, 01 CUỘN VÒI DN50 x 20 m. "
        "MỖI TỦ KÈM 01 BÌNH BỘT ABC 8 kg + 01 BÌNH CO2 5 kg.",
        f"- MỖI TẦNG 01 TỦ ĐẶT TẠI SẢNH TRƯỚC THANG MÁY, CẠNH THANG BỘ (TỔNG {sum(len(T['hong']) for T in TK['tang'].values())} TỦ); "
        "TRỤC ĐỨNG DN100, NHÁNH VÀO TỦ DN50.",
        "- MỖI ĐIỂM TRONG NHÀ ĐƯỢC ÍT NHẤT 01 TIA PHUN TỚI (PHỤ LỤC H, BẢNG H.5 QCVN 10:2025/BCA).",
        "- ÁP LỰC ĐẦU LĂNG KHI MỞ HỌNG ĐẠT 2,5 kg/cm² HOẶC CỘT NƯỚC ĐẶC ĐẠT 12 m TÍNH TỪ ĐẦU LĂNG "
        "(PHỤ LỤC H, BẢNG H.7 QCVN 10:2025/BCA).",
        f"- LƯU LƯỢNG NƯỚC CHỮA CHÁY TRONG NHÀ TÍNH CHO 01 HỌNG HOẠT ĐỘNG {q} L/S.",
        "- HỌNG CHỜ TIẾP NƯỚC LOẠI 2 CỬA DN65, ĐẶT MẶT NGOÀI PHÍA ĐÔNG TẦNG TRỆT, CÁCH SÀN HOÀN THIỆN 1,25 m.",
    ], rong_mm=160, co=2.7, tieu_de="THUYẾT MINH: HỆ THỐNG CHỮA CHÁY")
    ap = [f"  + {k.upper()}: {v:.2f} bar" for k, v in thanh_phan.items()]
    _cot(msp, G, TL, 210, 285, [
        "6. BỂ NƯỚC CHỮA CHÁY:",
        f"- BỂ NƯỚC CHỮA CHÁY ĐẶT TẠI PHÒNG KỸ THUẬT TẦNG HẦM, KHỐI TÍCH TỐI THIỂU {V} m³, CẤP TỪ NGUỒN NƯỚC "
        "THỦY CỤC, ĐIỀU KHIỂN BẰNG VAN PHAO. KHI BƠM HOẠT ĐỘNG LÀM GIẢM MỰC NƯỚC, NƯỚC THỦY CỤC CẤP BỔ SUNG LIÊN "
        "TỤC; PHỤC HỒI NƯỚC TRONG 24 h; CÓ BIỂN CHỈ DẪN VỊ TRÍ.",
        "7. TÍNH TOÁN TRẠM BƠM CHỮA CHÁY:",
        f"- LƯU LƯỢNG HỌNG VÁCH TƯỜNG (PHỤ LỤC H, BẢNG H.5 QCVN 10:2025/BCA): Qvt = 1 x {q} = {q} L/S.",
        "8. LƯU LƯỢNG MÁY BƠM (KHÔNG CÓ SPRINKLER):",
        f"- Qb = Qvt = {q} L/S.",
        "9. XÁC ĐỊNH CỘT ÁP BƠM:",
        "- VỊ TRÍ TÍNH TOÁN BẤT LỢI NHẤT: TỦ HỌNG TẦNG 6 (+20,100), XA VÀ CAO NHẤT SO VỚI BƠM ĐẶT TẠI TẦNG HẦM "
        "(-3,000, GIẢ THIẾT). ÁP LỰC CẦN TẠI BƠM GỒM:",
    ] + ap + [
        f"- TỔNG {tl['P_hong_bar']:.2f} bar; NHÂN HỆ SỐ DỰ TRỮ 1,1 -> CHỌN CỘT ÁP H = {H} m.",
        "- VẬY CHỌN HỆ THỐNG MÁY BƠM CÓ THÔNG SỐ NHƯ SAU:",
        f"  + BƠM ĐIỆN (EP-01) Q = {q} L/S, H = {H} m (BƠM CHÍNH).",
        f"  + BƠM DIESEL (DP-02) Q = {q} L/S, H = {H} m (BƠM DỰ PHÒNG).",
        f"  + BƠM BÙ ÁP (JP) Q = 1,0 L/S, H = {H + 5} m.",
        "10. XÁC ĐỊNH THỂ TÍCH BỂ NƯỚC CHỮA CHÁY:",
        f"- NƯỚC CHO HỌNG VÁCH TƯỜNG TRONG 3 GIỜ: V = {q} x 3 x 3,6 = {q * 3 * 3.6:.1f} m³.",
        f"- THỂ TÍCH BỂ NƯỚC CHỮA CHÁY TỐI THIỂU: {V} m³ (CHƯA GỒM NƯỚC CHỮA CHÁY NGOÀI NHÀ, LẤY TỪ TRỤ CẤP "
        "NƯỚC ĐÔ THỊ).",
        "- SỐ LIỆU TÍNH SƠ BỘ; KIỂM TRA LẠI THEO THIẾT BỊ VÀ TUYẾN ỐNG THỰC TẾ.",
    ], rong_mm=140, co=2.7)
    tb.tieu_de_to(msp, "THUYẾT MINH HỆ THỐNG CHỮA CHÁY", (G[0] + 190 * TL, G[1] + 12 * TL), TL)


def to_tm_chieu_sang(msp, G, TK):
    """Tờ 30 bản mẫu: thuyết minh chiếu sáng sự cố, chỉ dẫn thoát nạn + thông số đèn, sơ đồ thoát nạn."""
    TL = kh.TY_LE
    dem = {k: sum(len(T["cs"].get(k, [])) for T in TK["tang"].values())
           for k in ("exit", "exit_huong", "den_su_co", "sdtn", "sdtnp")}
    _cot(msp, G, TL, 12, 285, [
        "TIÊU CHUẨN THIẾT KẾ:",
        "- QCVN 10:2025/BCA - QUY CHUẨN KỸ THUẬT QUỐC GIA VỀ TRANG BỊ, BỐ TRÍ PHƯƠNG TIỆN PCCC, CNCH CHO NHÀ "
        "VÀ CÔNG TRÌNH.",
        "- TCVN 13456:2022 - PHÒNG CHÁY CHỮA CHÁY - PHƯƠNG TIỆN CHIẾU SÁNG SỰ CỐ VÀ CHỈ DẪN THOÁT NẠN.",
        "- TCVN 7435-1:2004 (ISO 11602-1:2000) - BÌNH CHỮA CHÁY XÁCH TAY VÀ XE ĐẨY CHỮA CHÁY.",
        "- KHOẢNG CÁCH DI CHUYỂN XA NHẤT ĐẾN BÌNH CHỮA CHÁY ≤ 15 m.",
        "- KHOẢNG CÁCH GIỮA CÁC ĐÈN CHIẾU SÁNG SỰ CỐ ≤ 30 m; GIỮA CÁC ĐÈN CHỈ DẪN THOÁT NẠN ≤ 25 m.",
        "- KHOẢNG CÁCH GIỮA CÁC NÚT ẤN KHẨN CẤP BÁO CHÁY ≤ 45 m.",
        "THUYẾT MINH:",
        "- ĐÈN CHIẾU SÁNG SỰ CỐ VÀ CHỈ DẪN THOÁT NẠN CÓ NGUỒN ĐIỆN DỰ PHÒNG ĐẢM BẢO HOẠT ĐỘNG TỐI THIỂU 2 GIỜ.",
        "- ĐÈN CHIẾU SÁNG SỰ CỐ CÓ CƯỜNG ĐỘ CHIẾU SÁNG BAN ĐẦU TRUNG BÌNH 10 lux, CƯỜNG ĐỘ NHỎ NHẤT TẠI BẤT KỲ "
        "THỜI ĐIỂM NÀO DỌC THEO ĐƯỜNG THOÁT NẠN KHÔNG NHỎ HƠN 1 lux.",
        "- ĐÈN CHỈ DẪN THOÁT NẠN NHÌN THẤY RÕ CHỮ \"LỐI RA\" HOẶC \"EXIT\" TỪ KHOẢNG CÁCH TỐI THIỂU 25 m TRONG "
        "ĐIỀU KIỆN CHIẾU SÁNG BÌNH THƯỜNG (300 lux) HOẶC KHI CÓ SỰ CỐ (10 lux).",
        "- ĐÈN ĐƯỢC LẮP TẠI CÁC CỬA RA VÀO, HÀNH LANG THOÁT NẠN, LỐI RẼ TRÊN ĐƯỜNG THOÁT NẠN, BUỒNG THANG BỘ, "
        "ĐẢM BẢO NHÌN THẤY LỐI THOÁT NẠN.",
        "- BIỂN BÁO AN TOÀN NỀN XANH LÁ CÂY, CHỮ VÀ KÝ HIỆU MÀU TRẮNG, ĐƯỢC CHIẾU SÁNG BÊN TRONG.",
        "- SƠ ĐỒ CHỈ DẪN THOÁT NẠN GỒM PHẦN KÝ HIỆU HÌNH HỌC (MẶT BẰNG TẦNG, LỐI RA, HƯỚNG THOÁT NẠN, THANG BỘ, "
        "VỊ TRÍ SƠ ĐỒ, PHƯƠNG TIỆN CHỮA CHÁY - KÝ HIỆU THEO TCVN 4879:1989, TCVN 5053:1990) VÀ PHẦN CHỈ DẪN BẰNG "
        "CHỮ (NỘI DUNG, TRÌNH TỰ XỬ LÝ KHI CÓ CHÁY); NIÊM YẾT Ở NƠI DỄ THẤY, CÓ NGƯỜI THƯỜNG XUYÊN QUA LẠI.",
        "- KÍCH THƯỚC SƠ ĐỒ ≥ 600 x 400 mm (TẠI TẦNG), ≥ 400 x 300 mm (TẠI PHÒNG); MÉP DƯỚI CAO 1,5 ± 0,2 m SO "
        "VỚI SÀN (TCVN 13456:2022 MỤC 5.2.9).",
    ], rong_mm=160, co=2.7, tieu_de="THUYẾT MINH ĐÈN CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN")
    hang = [["CHỦNG LOẠI", "THÔNG SỐ KỸ THUẬT", "SỐ LƯỢNG"],
            ["ĐÈN CHIẾU SÁNG SỰ CỐ", "CÔNG SUẤT 3 W; KT 270x75x270 mm;\nÁNH SÁNG TRẮNG; CHIẾU SÁNG 120 PHÚT",
             f"{dem['den_su_co']}"],
            ["ĐÈN EXIT", "CÔNG SUẤT 3 W; KT 350x25x145 mm; THÂN NHÔM,\nMẶT KÍNH; NỀN XANH CHỮ TRẮNG; 120 PHÚT",
             f"{dem['exit']}"],
            ["ĐÈN CHỈ HƯỚNG EXIT", "NHƯ ĐÈN EXIT, CÓ MŨI TÊN CHỈ HƯỚNG", f"{dem['exit_huong']}"],
            ["SƠ ĐỒ THOÁT NẠN TẦNG", "600x400 mm; NỀN TRẮNG; THÂN NHÔM HOẶC MIKA;\nMÉP DƯỚI CAO 1,5 ± 0,2 m",
             f"{dem['sdtn']}"],
            ["SƠ ĐỒ THOÁT NẠN PHÒNG", "400x300 mm; NHƯ TRÊN", f"{dem['sdtnp']}"],
            ["BÌNH CHỮA CHÁY", "BỘT ABC 8 kg + CO2 5 kg; ĐẶT TRÊN GIÁ HOẶC\nTREO TƯỜNG, ĐỈNH BÌNH CAO ≤ 1,5 m", "-"]]
    tb.bang(msp, (G[0] + 210 * TL, G[1] + 285 * TL), [42, 92, 22], hang, TL, cao_hang_mm=10, co=2.1,
            tieu_de="THÔNG SỐ THIẾT BỊ")
    _cot(msp, G, TL, 210, 180, [
        "- ĐÈN EXIT, ĐÈN SỰ CỐ GẮN TƯỜNG TRÊN ĐẦU CỬA, DƯỚI TRẦN 150-200 mm; HOẶC TREO DƯỚI TRẦN/SÀN BẰNG "
        "TI, XÍCH TREO M6; DÂY ĐI TRONG ỐNG PVC D20 BẢO VỆ, HỘP NỐI DÂY PVC.",
        "- BIỂN BÁO AN TOÀN TẦM THẤP ĐẶT CÁCH NHAU < 10 m, CAO ≤ 400 mm TỪ SÀN.",
        "- ĐÈN ĐƯỢC KIỂM TRA ĐỊNH KỲ (HÀNG THÁNG, HÀNG NĂM) ĐỘ SÁNG VÀ THỜI GIAN HOẠT ĐỘNG.",
    ], rong_mm=140, co=2.7, tieu_de="CHI TIẾT LẮP ĐẶT:")
    tb.tieu_de_to(msp, "THUYẾT MINH CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN", (G[0] + 190 * TL, G[1] + 12 * TL), TL)


def cong_suat(TK):
    """Công suất phụ tải PCCC (kW). Bơm: P = ρgQH/η (η 0,55) -> chọn động cơ chuẩn ≥ 1,5 lần."""
    tl = TK["thuy_luc"]
    p_truc = 9.81 * tl["Q_bom_l_s"] * tl["H_bom_m"] / 1000 / 0.55
    p_bom = next(p for p in (1.5, 2.2, 3.0, 4.0, 5.5, 7.5, 11, 15, 18.5, 22, 30) if p >= 1.5 * p_truc)
    so_den = sum(len(T["cs"].get(k, [])) for T in TK["tang"].values() for k in ("exit", "exit_huong", "den_su_co"))
    p_den = max(0.5, math.ceil(so_den * 3 / 100) / 10)
    return {"p_truc": p_truc, "bom": p_bom, "bao_chay": 0.5, "den": p_den, "so_den": so_den}


def to_tm_dien(msp, G, TK):
    """Tờ 32 bản mẫu: thuyết minh điện PCCC + bảng công suất (bản mẫu cộng sai: 2+18,5+2 ghi 27,5)."""
    TL = kh.TY_LE
    cs = cong_suat(TK)
    Pi = cs["bao_chay"] + cs["bom"] + cs["den"]
    _cot(msp, G, TL, 12, 285, [
        "THUYẾT MINH NÀY TRÌNH BÀY CÁC YÊU CẦU KỸ THUẬT VÀ THIẾT KẾ HỆ THỐNG ĐIỆN CHO CÁC HỆ THỐNG PCCC, TUÂN THỦ "
        "TCVN 7568-14:2025, QCVN 12:2014/BXD, TCVN 9206:2012, QUY PHẠM TRANG BỊ ĐIỆN 11TCN-18:2006. HỆ THỐNG ĐIỆN "
        "PCCC GỒM: HỆ THỐNG BÁO CHÁY TỰ ĐỘNG; HỆ THỐNG CHỮA CHÁY BẰNG NƯỚC (HỌNG VÁCH TƯỜNG); HỆ THỐNG CHIẾU SÁNG "
        "SỰ CỐ VÀ BIỂN BÁO THOÁT NẠN.",
        "1. YÊU CẦU CHUNG VỀ NGUỒN ĐIỆN: HAI NGUỒN ĐỘC LẬP.",
        "- NGUỒN CHÍNH: 220/380 V AC TỪ LƯỚI ĐIỆN, ỔN ĐỊNH TRONG KHOẢNG ±10 %.",
        "- NGUỒN DỰ PHÒNG: ẮC QUY 24 V DC (BÁO CHÁY), PIN TÍCH HỢP (ĐÈN), BƠM DIESEL (CHỮA CHÁY).",
        "- ĐẢM BẢO HOẠT ĐỘNG LIÊN TỤC, TÍCH HỢP GIÁM SÁT NGUỒN VỚI TRUNG TÂM BÁO CHÁY.",
        "2. HỆ THỐNG BÁO CHÁY: TRUNG TÂM 10 KÊNH, CẤP ĐIỆN 220 V AC VÀ ẮC QUY DỰ PHÒNG; ẮC QUY NẠP TỰ ĐỘNG, GIÁM SÁT "
        "ĐIỆN ÁP; BẢO VỆ BẰNG CẦU DAO CÁCH LY, APTOMAT HOẶC CẦU CHÌ CHUYÊN DỤNG.",
        "3. HỆ THỐNG CHỮA CHÁY: BƠM ĐIỆN CẤP TỪ LƯỚI 380 V 3 PHA, BƠM DIESEL DỰ PHÒNG. MẠCH ĐIỆN ĐỘC LẬP, CÁP CHỐNG "
        "CHÁY (FR) CHỊU 750 °C TRONG 90 PHÚT; THIẾT BỊ BẢO VỆ QUÁ TẢI CHỈ PHÁT TÍN HIỆU CẢNH BÁO, KHÔNG CẮT NGUỒN.",
        "4. CHIẾU SÁNG KHẨN CẤP VÀ BIỂN BÁO THOÁT NẠN: HOẠT ĐỘNG LIÊN TỤC 120 PHÚT KHI MẤT ĐIỆN; BẢO VỆ BẰNG APTOMAT "
        "HOẶC CẦU CHÌ; KIỂM TRA ĐỊNH KỲ. NGUỒN ẮC QUY ĐƯỢC GIÁM SÁT ĐIỆN ÁP, BÁO LỖI KHI DUNG LƯỢNG < 87,5 %.",
        "5. YÊU CẦU KỸ THUẬT BỔ SUNG:",
        "- DÂY DẪN, CÁP CẤP ĐIỆN PCCC LOẠI CHỐNG CHÁY (FR), CHỊU 750 °C TRONG 90 PHÚT, ĐI TRONG ỐNG RIÊNG, KHÔNG CHUNG "
        "VỚI MẠCH TẢI THÔNG THƯỜNG.",
        "- MẠCH CẤP ĐIỆN THIẾT BỊ AN TOÀN (BƠM, ĐÈN THOÁT NẠN) ĐỘC LẬP, TỦ ĐIỆN RIÊNG; CHUYỂN SANG NGUỒN DỰ PHÒNG "
        "TRONG VÒNG 10 GIÂY; ATS ĐƯỢC GIÁM SÁT VÀ BÁO LỖI.",
        "- HỆ THỐNG GIÁM SÁT NGUỒN TÍCH HỢP VỚI TRUNG TÂM BÁO CHÁY, BÁO LỖI TRONG VÒNG 200 GIÂY.",
        "6. TÍN HIỆU BÁO CHÁY ĐIỀU KHIỂN TỰ ĐỘNG NGẮT ĐIỆN SINH HOẠT, PHỤ TẢI THÔNG THƯỜNG VÀ DUY TRÌ NGUỒN CHO CÁC "
        "HỆ THỐNG PCCC.",
    ], rong_mm=160, co=2.7, tieu_de="THUYẾT MINH HỆ THỐNG ĐIỆN PCCC")
    hang = [["THIẾT BỊ", "SỐ LƯỢNG", "CÔNG SUẤT (kW)"],
            ["HỆ THỐNG BÁO CHÁY", "01", f"{cs['bao_chay']:.1f}"],
            [f"BƠM CHỮA CHÁY (ĐIỆN) {TK['thuy_luc']['Q_bom_l_s']} L/S - {TK['thuy_luc']['H_bom_m']} m", "01",
             f"{cs['bom']:.1f}"],
            [f"CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN\n({cs['so_den']} ĐÈN x 3 W)", "01", f"{cs['den']:.1f}"],
            ["TỔNG CÔNG SUẤT PHỤ TẢI PCCC: Pi = Ptt", "", f"{Pi:.1f}"],
            ["TỔNG CÔNG SUẤT TÍNH TOÁN: Stt = Ptt / cosφ (cosφ = 0,8)", "", f"{Pi / 0.8:.2f} kVA"]]
    tb.bang(msp, (G[0] + 210 * TL, G[1] + 285 * TL), [96, 22, 38], hang, TL, cao_hang_mm=10, co=2.2,
            tieu_de="TÍNH TOÁN CÔNG SUẤT NGUỒN CỦA HỆ THỐNG PCCC")
    hang2 = [["THIẾT BỊ", "NGUỒN DỰ PHÒNG"],
             ["BƠM CHỮA CHÁY", f"BƠM DIESEL DP-02 {TK['thuy_luc']['Q_bom_l_s']} L/S - {TK['thuy_luc']['H_bom_m']} m"],
             ["HỆ THỐNG BÁO CHÁY", "02 ẮC QUY 12 V NỐI TIẾP (24 V DC)"],
             ["CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN", "PIN TÍCH HỢP TRONG ĐÈN, 120 PHÚT"]]
    tb.bang(msp, (G[0] + 210 * TL, G[1] + 200 * TL), [70, 86], hang2, TL, cao_hang_mm=10, co=2.2,
            tieu_de="NGUỒN DỰ PHÒNG CỦA HỆ THỐNG PCCC")
    _cot(msp, G, TL, 210, 140, [
        f"- CÔNG SUẤT TRỤC BƠM P = ρ.g.Q.H / η = 9,81 x {TK['thuy_luc']['Q_bom_l_s']} x {TK['thuy_luc']['H_bom_m']}"
        f" / 0,55 = {cs['p_truc']:.2f} kW; CHỌN ĐỘNG CƠ {cs['bom']:.1f} kW (DỰ TRỮ ≥ 1,5 LẦN).",
        "- CÔNG TRÌNH KHÔNG BỐ TRÍ THANG MÁY CHỮA CHÁY, HỆ THỐNG HÚT KHÓI, TĂNG ÁP.",
        "- CÔNG SUẤT BÁO CHÁY, ĐÈN LẤY SƠ BỘ; CẬP NHẬT THEO CATALOGUE THIẾT BỊ.",
    ], rong_mm=140, co=2.7, tieu_de="GHI CHÚ:")
    tb.tieu_de_to(msp, "THUYẾT MINH HỆ THỐNG ĐIỆN PCCC", (G[0] + 190 * TL, G[1] + 12 * TL), TL)
