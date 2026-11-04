"""Sơ đồ nguyên lý hệ báo cháy, chữa cháy, đèn sự cố — chỉ dẫn thoát nạn (theo hồ sơ mẫu KS 32 Dã Tượng).

Mỗi hàm vẽ một tờ A3 (khung + cột tên do trinh_bay.khung_a3 vẽ trước) lên `msp` (ezdxf hoặc
acad_msp.MSP). Toạ độ khai báo bằng mm giấy tính từ góc dưới-trái tờ, nhân tỷ lệ in.
Số lượng thiết bị lấy từ mặt bằng đã dựng: không tự chép từ bản mẫu, vì bản mẫu từng ghi số trên sơ đồ
lệch với mặt bằng (x09 đầu khói/tầng trên sơ đồ, 13 trên mặt bằng).

    so_do.bao_chay(msp, G, zones, ty_le=125)
    so_do.chua_chay(msp, G, tang, bom, ty_le=125)
    so_do.chieu_sang(msp, G, tang, ty_le=125)
"""
import math

import ky_hieu as kh
import trinh_bay as tb

# Dòng điện thiết bị (A) dùng tính ắc quy tủ trung tâm (Phụ lục C TCVN 7568-14:2025). Lấy theo hồ sơ mẫu;
# phải thay bằng số trong catalogue thiết bị thực tế.
DONG_THIET_BI = {  # loai: (tên cột, dòng tĩnh IQ, dòng báo cháy IA)
    "tu_tt": ("TỦ TRUNG TÂM\nBÁO CHÁY", 0.133, 0.282),
    "bao_khoi": ("ĐẦU BÁO KHÓI\nĐIỂM", 0.000045, 0.15),
    "bao_nhiet": ("ĐẦU BÁO NHIỆT\nĐIỂM", 0.000038, 0.15),
    "nut_an": ("NÚT NHẤN", 0.0, 0.0002),
    "den_fire": ("ĐÈN BÁO\nNGOÀI NHÀ", 0.085, 0.35),
    "chuong_den": ("CHUÔNG BÁO\nCHÁY + ĐÈN", 0.0, 0.008),
}


def tinh_ac_quy(so_luong, TQ=24.0, TA=0.5, FC=2.0):
    """C20 = 1,25[(IQ·TQ) + FC(IA·TA)]; IC = 1,25[(IQ·5) + (IA·0,5)]/24; I = IQ + IC."""
    IQ = sum(DONG_THIET_BI[k][1] * n for k, n in so_luong.items() if k in DONG_THIET_BI)
    IA = sum(DONG_THIET_BI[k][2] * n for k, n in so_luong.items() if k in DONG_THIET_BI)
    C20 = 1.25 * (IQ * TQ + FC * IA * TA)
    IC = 1.25 * (IQ * 5 + IA * 0.5) / 24
    # chọn 2 ắc quy 12 V nối tiếp, dung lượng tiêu chuẩn đủ C20
    chon = next(c for c in (7, 12, 17, 24, 30, 40, 55, 65, 100, 150, 200) if c >= C20)
    return {"IQ": IQ, "IA": IA, "C20": C20, "IC": IC, "I": IQ + IC, "chon_Ah": chon}


class _Ve:
    """Vẽ theo mm giấy trên tờ có góc dưới-trái G."""

    def __init__(self, msp, G, ty_le):
        self.msp, self.G, self.s = msp, G, kh.he_so_chen(ty_le)
        self.ty_le = ty_le

    def p(self, x, y):
        return (self.G[0] + x * self.s, self.G[1] + y * self.s)

    def net(self, pts, layer="PCCC-SO-DO", mau=None, net=None):
        a = {"layer": layer}
        if mau is not None:
            a["color"] = mau
        if net:
            a["linetype"] = net
            a["ltscale"] = 30
        if len(pts) == 2:
            return self.msp.add_line(self.p(*pts[0]), self.p(*pts[1]), dxfattribs=a)
        return self.msp.add_lwpolyline([self.p(*q) for q in pts], dxfattribs=a)

    def hcn(self, x0, y0, x1, y1, mau=None, layer="PCCC-SO-DO"):
        return self.net([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], layer, mau)

    def chu(self, s, x, y, co=2.2, can="MIDDLE_LEFT", mau=None, dam=False):
        return tb._chu(self.msp, s, self.p(x, y), co, can, self.ty_le, mau=mau,
                       kieu=kh.KIEU_CHU + "_B" if dam else None)

    def ky(self, loai, x, y, goc=0):
        return kh.chen(self.msp, loai, self.p(x, y), self.ty_le, goc)

    def tieu_de(self, s, x=190, y=9):
        self.chu(s, x, y, 6.0, "MIDDLE_CENTER", dam=True)
        L = len(s) * 6.0 * 0.66
        self.net([(x - L / 2, y - 4.2), (x + L / 2, y - 4.2)], layer=kh.LAYER_TEXT[0])


# ============================== BÁO CHÁY ==============================

def bao_chay(msp, G, zones, ty_le=125, so_zone_tu=12, ten_tu="12 ZONES", tang_dat_tu="TẦNG 1"):
    """zones: [(tên zone, {loai: số lượng})] từ tầng thấp lên cao (loai: bao_khoi, bao_nhiet,
    nut_an, chuong_den, den_fire, den_phong). Trả về kết quả tính ắc quy."""
    v = _Ve(msp, G, ty_le)
    tong = {}
    for _, d in zones:
        for k, n in d.items():
            tong[k] = tong.get(k, 0) + n
    tong["tu_tt"] = 1
    aq = tinh_ac_quy(tong)

    # --- Bảng tính nguồn tủ trung tâm (góc trên-trái) ---
    cot = [k for k in DONG_THIET_BI if tong.get(k)]
    hang = [["THIẾT BỊ"] + [DONG_THIET_BI[k][0] for k in cot],
            ["SỐ LƯỢNG"] + [str(tong[k]) for k in cot],
            ["DÒNG TĨNH IQ (A)"] + [f"{DONG_THIET_BI[k][1]:.6f}".rstrip("0").rstrip(".") for k in cot],
            ["DÒNG BÁO CHÁY IA (A)"] + [f"{DONG_THIET_BI[k][2]:g}" for k in cot],
            ["TỔNG DÒNG TĨNH (A)"] + [f"{DONG_THIET_BI[k][1] * tong[k]:.6f}".rstrip("0").rstrip(".") for k in cot],
            ["TỔNG DÒNG BÁO CHÁY (A)"] + [f"{DONG_THIET_BI[k][2] * tong[k]:.6g}" for k in cot]]
    rong = [44] + [round(150 / len(cot), 1)] * len(cot)
    b = tb.bang(msp, v.p(12, 287), rong, hang, ty_le, cao_hang_mm=6.5, co=1.9, mau_vien=kh.XANH_NHAT,
                tieu_de="BẢNG TÍNH TOÁN NGUỒN ĐIỆN TỦ TRUNG TÂM BÁO CHÁY (TQ = 24h, TA = 0,5h, FC = 2) - "
                        "PHỤ LỤC C TCVN 7568-14:2025")
    y = (b[1] - G[1]) / v.s - 1
    for s in [f"TỔNG DÒNG TĨNH IQ = {aq['IQ']:.4f} A;  TỔNG DÒNG BÁO CHÁY IA = {aq['IA']:.3f} A",
              f"DUNG LƯỢNG ẮC QUY C20 = 1,25[(IQ x TQ) + FC(IA x TA)] = {aq['C20']:.2f} Ah",
              f"DÒNG ĐIỆN NẠP IC = 1,25[(IQ x 5) + (IA x 0,5)]/24 = {aq['IC']:.3f} A;  DÒNG TỔNG I = IQ + IC = {aq['I']:.3f} A",
              f"KẾT LUẬN: SỬ DỤNG 2 ẮC QUY 12V-{aq['chon_Ah']}Ah NỐI TIẾP (24 VDC), DÒNG NẠP TỐI THIỂU {aq['IC']:.2f} A, "
              "ĐẢM BẢO HOẠT ĐỘNG 24h THƯỜNG TRỰC + 30 PHÚT KHI CÓ CHÁY"]:
        y -= 4.2
        v.chu(s, 13, y, 2.0, mau=kh.XANH_NHAT)

    # --- Tủ trung tâm, nguồn, kết nối ---
    fx0, fx1, fy0, fy1 = 70, 112, 48, 118
    v.hcn(fx0, fy0, fx1, fy1)
    v.net([(fx1, fy0 - 1.2), (fx1 + 1.2, fy0 - 1.2), (fx1 + 1.2, fy1 - 1.2)], mau=kh.DO)
    for i, (s, co, m) in enumerate([(ten_tu, 2.4, kh.XANH_LA), ("FACP", 2.4, kh.XANH_LA),
                                    ("FIRE ALARM", 2.2, kh.DO), ("CONTROL PANEL", 2.2, kh.DO),
                                    ("TRUNG TÂM BÁO CHÁY", 1.9, 8), (f"(ĐẶT TẠI {tang_dat_tu} PHÒNG", 1.9, 8),
                                    ("AN NINH CÓ NGƯỜI", 1.9, 8), ("THƯỜNG TRỰC 24/24)", 1.9, 8)]):
        v.chu(s, (fx0 + fx1) / 2, fy1 - 7 - i * 7.5, co, "MIDDLE_CENTER", mau=m)
    v.hcn(56, 18, 78, 32)
    v.ky("sd_ac_quy", 60, 25)
    for i, s in enumerate(["24 VDC", "BATTERY", "backup 24Hr"]):
        v.chu(s, 70, 29 - i * 4, 1.9, "MIDDLE_CENTER", mau=kh.XANH_LA)
    v.net([(78, 25), (88, 25), (88, fy0)])
    v.chu("220V/50Hz", 40, 27, 2.0, mau=kh.XANH_LA)
    v.chu("AC", 44, 23, 2.0, mau=kh.XANH_LA)
    v.net([(52, 25), (56, 25)])
    v.net([(100, fy0), (100, 38), (98, 38)])
    v.chu("R<=10 Ohm", 92, 35, 2.0, mau=kh.XANH_LA)
    for i, s in enumerate(["TRUYỀN TIN BÁO CHÁY ĐẾN PCCC & CNCH", "ĐIỀU KHIỂN TỦ BƠM CHỮA CHÁY",
                           "GIÁM SÁT TRẠNG THÁI VAN, BƠM CHỮA CHÁY", "NGẮT HỆ THỐNG TỦ ĐIỆN TRUNG TÂM"]):
        yy = 112 - i * 13
        v.hcn(14, yy - 4, 58, yy + 4)
        v.chu(s, 36, yy, 1.6, "MIDDLE_CENTER")
        v.net([(58, yy), (fx0, yy)])
    v.chu("CÁP 2C x 1,5mm² (CHỐNG CHÁY) ĐI TRONG ỐNG PVC Ø20", 14, 122, 1.9, mau=kh.XANH_LA)

    # --- Zone theo tầng ---
    n = len(zones)
    y_tren, y_duoi = 198, 62
    buoc = (y_tren - y_duoi) / max(n, 1)
    x_bus = fx1 + 6
    x_na, x_s, x_h, x_eol, x_cd = 205, 245, 270, 300, 340
    du_phong = so_zone_tu - n
    v.chu(f"ZONE {n + 1:02d} - {so_zone_tu:02d} DỰ PHÒNG", 140, y_tren + buoc * 0.9, 2.2)
    v.net([(x_bus - 2, y_tren + buoc * 0.6), (370, y_tren + buoc * 0.6)], mau=kh.XANH_LA)
    for i, (ten, d) in enumerate(zones):
        y = y_duoi + i * buoc
        yf = fy0 + 4 + i * (fy1 - fy0 - 8) / max(n - 1, 1)
        xb = x_bus + i * 1.0
        v.net([(fx1, yf), (xb, yf), (xb, y), (x_na - 4, y)], mau=kh.XANH_LA)
        v.chu(f"ZONE {i + 1:02d} - {ten}", 140, y + 2.2, 2.2)
        x = x_na
        for loai, xx in (("nut_an", x_na), ("bao_khoi", x_s), ("bao_nhiet", x_h)):
            if d.get(loai):
                v.ky(loai, xx, y)
                v.chu(f"x{d[loai]:02d}", xx, y + 4.0, 2.4, "MIDDLE_CENTER", mau=kh.DO)
                if xx > x + 1:
                    v.net([(x + 2, y), (xx - 2, y)], mau=kh.DO)
                x = xx
        v.net([(x + 2, y), (x_eol - 2, y)], mau=kh.DO)
        v.ky("sd_eol", x_eol, y)
        if d.get("chuong_den"):
            v.ky("chuong_den", x_cd, y)
            v.chu(f"x{d['chuong_den']}", x_cd + 4, y, 2.4, mau=kh.DO)
            v.net([(x_cd + 9, y), (360, y)], mau=kh.DO)
        if d.get("den_fire"):
            for k in range(d["den_fire"]):
                v.ky("den_fire", 225 + k * 22, y - buoc * 0.55)
            v.chu("ĐÈN BÁO CHỈ THỊ CHÁY NGOÀI NHÀ", 250, y - buoc * 0.55 - 4.5, 2.2, "MIDDLE_CENTER")
    # mạch chuông riêng: bus bên phải về tủ
    v.net([(360, y_duoi), (360, y_duoi + (n - 1) * buoc)], mau=kh.DO)
    v.net([(360, y_duoi), (360, 40), (fx1 + 1.2, 40), (fx1 + 1.2, fy0)], mau=kh.DO)
    v.chu("CÁP 2C x 1,5mm² (CHỐNG CHÁY) ĐI TRONG ỐNG PVC Ø20 - MẠCH CHUÔNG, ĐÈN", 200, 43, 1.9, "MIDDLE_CENTER",
          mau=kh.XANH_LA)
    v.chu("DẪN VỀ TRUNG TÂM BÁO CHÁY: CÁP 2C x 1mm² (CHỐNG CHÁY) ĐI TRONG ỐNG PVC Ø20", 122, 56, 1.9,
          mau=kh.XANH_LA)
    kh.ve_bang(msp, v.p(12, 132), ["bao_khoi", "bao_nhiet", "nut_an", "chuong_den", "den_fire", "sd_eol"],
               tieu_de="KÝ HIỆU:", ty_le=ty_le, rong_mm=56)
    v.tieu_de("SƠ ĐỒ NGUYÊN LÝ HỆ THỐNG BÁO CHÁY TỰ ĐỘNG")
    return aq


# ============================== CHỮA CHÁY ==============================

def chua_chay(msp, G, tang, bom, ty_le=125, the_tich_be=24, dn_truc=80, dn_hong=50, phong_bom="PHÒNG BƠM TẦNG 1"):
    """tang: [(tên, cao độ m, số đầu phun, có họng)] từ dưới lên. bom: [(loại, ký hiệu, Q l/s, H m)]."""
    v = _Ve(msp, G, ty_le)
    xr = 230                      # trục đứng
    y0, y1 = 70, 262
    n = len(tang)
    buoc = (y1 - y0) / n
    # trục đứng + van xả khí
    v.net([(xr, y0 - 12), (xr, y1 + 6)], layer=kh.layer_ong("spr", dn_truc), mau=kh.DO)
    v.ky("sd_van_xa_khi", xr, y1 + 8)
    v.chu(f"TRỤC ĐỨNG DN{dn_truc}", xr + 2.5, y1 + 2, 1.8, mau=kh.TIM)
    for i, (ten, cao, so_dau, co_hong) in enumerate(tang):
        y = y0 + i * buoc
        v.net([(150, y), (348, y)], layer=kh.LAYER_TEXT[0], mau=8)
        v.net([(342, y), (348, y), (345, y - 2.2), (342, y)], layer=kh.LAYER_TEXT[0])
        v.chu(ten, 350, y + 2.5, 2.2)
        v.chu(f"{'+' if cao >= 0 else ''}{cao:.3f}", 350, y - 2.2, 1.9, mau=8)
        # nhánh sprinkler: van khoá + công tắc dòng chảy, ống DN80, 5 đầu phun đại diện
        yb = y + buoc * 0.62
        if so_dau:
            v.net([(xr, yb), (322, yb)], layer=kh.layer_ong("spr", dn_truc), mau=kh.DO)
            v.ky("sd_van", xr + 6, yb)
            v.ky("sd_cong_tac_dong", xr + 12, yb + 2.4)
            v.chu(f"DN{dn_truc}", xr + 22, yb + 1.6, 1.6, mau=kh.TIM)
            for k in range(5):
                xx = 262 + k * 13
                v.ky("sd_dau_phun", xx, yb)
                v.chu("DN25", xx - 3, yb - 3.2, 1.3, "MIDDLE_CENTER", mau=kh.TIM)
            v.chu(f"x{so_dau:02d} ĐẦU PHUN", 324, yb, 2.0, mau=kh.DO)
        if co_hong:
            yh = y + buoc * 0.25
            v.net([(xr, yh), (xr - 13, yh)], layer=kh.layer_ong("hong", dn_hong), mau=kh.DO)
            v.ky("sd_van", xr - 6, yh)
            v.ky("sd_tu_hong", xr - 16, yh)
            v.chu("+1.250", xr - 16, yh - 3, 1.6, "MIDDLE_CENTER", mau=8)
            v.chu(f"STK DN{dn_hong}", xr - 8, yh + 2, 1.4, "MIDDLE_CENTER", mau=kh.TIM)
    # đầu phun bất lợi + đồng hồ áp tầng trên cùng
    co_spr = any(t_[2] for t_ in tang)  # không có sprinkler: bỏ nhánh, đồng hồ đầu bất lợi, ký hiệu đầu phun
    if co_spr:
        v.ky("sd_dong_ho", 322, y0 + (n - 1) * buoc + buoc * 0.62)
    # --- trạm bơm ---
    yd = y0 - 12                  # cao độ ống góp đẩy nối vào chân trục đứng
    v.hcn(128, 22, 166, 40, mau=kh.XANH_NHAT)
    v.net([(128, 37), (166, 37)], mau=kh.XANH_NHAT)
    v.chu(f"BỂ NƯỚC NGẦM CHỮA CHÁY {the_tich_be} m³", 147, 19, 1.8, "MIDDLE_CENTER")
    v.chu("PHỤC HỒI NƯỚC TRONG 24H, CÓ BIỂN CHỈ DẪN VỊ TRÍ", 147, 16, 1.5, "MIDDLE_CENTER")
    v.ky("sd_van_phao", 134, 40)
    v.net([(108, 45), (134, 45), (134, 41)], mau=kh.XANH_NHAT)
    v.chu("NỐI MẠNG CẤP NƯỚC THÀNH PHỐ", 108, 47.5, 1.5)
    x_gop = xr - 22
    for k, (loai, ky, Q, H) in enumerate(bom):
        yk = 26 + k * 7
        v.net([(160 - k * 6, 24), (160 - k * 6, yk), (180, yk)], mau=kh.DO)
        v.ky("sd_y_loc", 172, yk)
        v.ky("sd_bom", 183, yk)
        v.chu(ky, 183, yk + 3.4, 1.4, "MIDDLE_CENTER")
        v.net([(185, yk), (x_gop, yk)], mau=kh.DO)
        v.ky("sd_khop_mem", 190, yk)
        v.ky("sd_van_1c", 196, yk)
        v.ky("sd_van", x_gop - 4, yk)
    v.net([(x_gop, 26), (x_gop, yd), (xr, yd)], mau=kh.DO)
    v.ky("sd_cong_tac_ap", x_gop + 6, yd)
    v.ky("sd_dong_ho", x_gop + 11, yd)
    v.ky("sd_van_an_toan", x_gop + 16, yd)
    v.chu(f"DN{dn_truc}", x_gop + 1, yd - 2, 1.5, mau=kh.TIM)
    v.chu(phong_bom, 128, 52, 1.9)
    v.net([(xr, yd), (xr, 45)], mau=kh.DO)
    # họng tiếp nước / lấy nước ngoài nhà
    v.net([(xr, yd), (300, yd), (300, 40)], mau=kh.DO)
    v.ky("sd_van_1c", 265, yd)
    v.ky("hong_tiep", 300, 39)
    v.chu("HỌNG TIẾP NƯỚC NGOÀI NHÀ 2 CỬA DN65", 304, 39, 1.8)
    v.net([(xr, yd), (xr, 33), (300, 33)], mau=kh.DO)
    v.ky("hong_tiep", 300, 32)
    v.chu("HỌNG LẤY NƯỚC NGOÀI NHÀ 2 CỬA DN65", 304, 32, 1.8)
    # tủ điều khiển bơm, tín hiệu
    for k, s_ in enumerate(["TỦ ĐK BƠM EP-01", "TỦ ĐK BƠM DP-02", "TỦ BÁO CHÁY"]):
        v.hcn(232 + k * 22, 18, 252 + k * 22, 25)
        v.chu(s_, 242 + k * 22, 21.5, 1.3, "MIDDLE_CENTER")
    v.chu("TÍN HIỆU BÁO CHÁY VỀ PHÒNG BƠM - CÁP CHỐNG CHÁY", 265, 15, 1.5, "MIDDLE_CENTER")
    # --- ký hiệu + bảng bơm ---
    kh.ve_bang(msp, v.p(12, 118), ["sd_van", "sd_van_1c", "sd_y_loc", "sd_khop_mem", "sd_dong_ho", "sd_cong_tac_ap",
                                   "sd_van_an_toan", "sd_bom", "sd_van_phao"] +
               (["sd_cong_tac_dong", "sd_van_xa_khi", "sd_dau_phun"] if co_spr else ["sd_van_xa_khi"]) +
               ["sd_tu_hong", "hong_tiep"],
               tieu_de="KÝ HIỆU :", ty_le=ty_le, rong_mm=82)
    tb.bang(msp, v.p(12, 285), [10, 34, 18, 24, 22],
            [["STT", "LOẠI BƠM", "KÝ HIỆU", "LƯU LƯỢNG", "CỘT ÁP\n(mH2O)"]] +
            [[str(k + 1), loai, ky, f"{Q:g} L/s", f"{H:g}"] for k, (loai, ky, Q, H) in enumerate(bom)],
            ty_le, cao_hang_mm=6.5, co=2.0, tieu_de="THÔNG SỐ KỸ THUẬT BƠM PCCC")
    v.tieu_de("SƠ ĐỒ NGUYÊN LÝ HỆ THỐNG CHỮA CHÁY")


# ============================== ĐÈN SỰ CỐ, CHỈ DẪN THOÁT NẠN ==============================

def chieu_sang(msp, G, tang, ty_le=125):
    """tang: [(tên, {exit, exit_huong, den_su_co, sdtn, sdtnp, mat_na})] từ dưới lên."""
    v = _Ve(msp, G, ty_le)
    n = len(tang)
    y0, y1 = 55, 195
    buoc = (y1 - y0) / max(n - 1, 1)
    # tủ nguồn
    v.hcn(40, 100, 92, 150)
    for i, s in enumerate(["TỦ ĐIỆN CHIẾU SÁNG", "SỰ CỐ - CHỈ DẪN", "THOÁT NẠN", "(NGUỒN ƯU TIÊN TỪ", "TỦ MSB / MÁY PHÁT)"]):
        v.chu(s, 66, 142 - i * 8, 2.0, "MIDDLE_CENTER", mau=kh.XANH_LA if i < 3 else 8)
    v.net([(66, 100), (66, 86)])
    v.chu("TỪ TỦ ĐIỆN MSB (MCCB-1P, MẠCH EM)", 66, 82, 1.9, "MIDDLE_CENTER")
    xb = 100
    for i, (ten, d) in enumerate(tang):
        y = y0 + i * buoc
        yf = 104 + i * (42 / max(n - 1, 1))
        v.net([(92, yf), (xb + i * 1.0, yf), (xb + i * 1.0, y), (150, y)], mau=kh.DO)
        v.chu(f"MCB 1P-10A - {ten}", 152, y + 2.4, 2.0)
        x_cuoi = 152
        for loai, x in (("exit", 215), ("exit_huong", 247), ("den_su_co", 279)):  # cột cố định
            if d.get(loai):
                v.ky(loai, x, y)
                v.chu(f"x{d[loai]:02d}", x, y + 3.6, 2.2, "MIDDLE_CENTER", mau=kh.DO)
                x_cuoi = x + 3
        v.net([(152, y), (x_cuoi, y)], mau=kh.DO)
        o = [f"SĐTN TẦNG x{d.get('sdtn', 0)}"]
        if d.get("sdtnp"):
            o.append(f"SĐTN PHÒNG x{d['sdtnp']}")
        if d.get("mat_na"):
            o.append(f"HỘP MẶT NẠ x{d['mat_na']}")
        v.chu(";  ".join(o), 305, y, 1.9)
    v.chu("CÁP Cu/FR 2x1,5mm² (CHỐNG CHÁY) ĐI TRONG ỐNG PVC Ø20", 152, y0 - 10, 1.9, mau=kh.XANH_LA)
    v.chu("ĐÈN EXIT, ĐÈN SỰ CỐ CÓ ẮC QUY TÍCH HỢP, THỜI GIAN HOẠT ĐỘNG ≥ 2h", 152, y0 - 15, 1.9, mau=kh.XANH_LA)
    v.chu("SƠ ĐỒ CHỈ DẪN THOÁT NẠN, HỘP MẶT NẠ: KHÔNG DÙNG ĐIỆN (THỐNG KÊ ĐỂ THAM KHẢO)", 152, y0 - 20, 1.9, mau=8)
    # bảng thống kê
    tong = {}
    for _, d in tang:
        for k, c in d.items():
            tong[k] = tong.get(k, 0) + c
    cot = ["exit", "exit_huong", "den_su_co", "sdtn", "sdtnp", "mat_na"]
    ten_cot = ["EXIT", "EXIT CHỈ\nHƯỚNG", "ĐÈN SỰ\nCỐ", "SĐTN\nTẦNG", "SĐTN\nPHÒNG", "HỘP\nMẶT NẠ"]
    tb.bang(msp, v.p(12, 285), [24] + [17] * len(cot),
            [["TẦNG"] + ten_cot] + [[t] + [str(d.get(k, 0)) for k in cot] for t, d in tang] +
            [["TỔNG"] + [str(tong.get(k, 0)) for k in cot]],
            ty_le, cao_hang_mm=5.6, co=1.9, tieu_de="BẢNG THỐNG KÊ THIẾT BỊ")
    kh.ve_bang(msp, v.p(12, 22), ["exit", "exit_huong", "den_su_co"], tieu_de="KÝ HIỆU:", ty_le=ty_le, rong_mm=95)
    v.tieu_de("SƠ ĐỒ NGUYÊN LÝ HỆ THỐNG ĐÈN CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN")
