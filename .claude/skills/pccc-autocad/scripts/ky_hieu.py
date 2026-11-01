"""Bộ ký hiệu thiết bị PCCC thống nhất (một định nghĩa dùng cho mọi tờ, mọi script).

Mô phỏng theo hồ sơ mẫu đã được duyệt (KS 32 Dã Tượng, 10/2026), xem references/trinh-bay-ban-ve.md:
- Báo cháy: "S" đỏ trong vòng tròn = đầu báo khói, "H" xanh lá = đầu báo nhiệt, nút ấn và chuông-đèn
  là ô vuông bo góc xanh lá, tủ trung tâm "FACP" và đèn "FIRE" ngoài nhà là khung chữ nhật đỏ,
  đèn báo cháy phòng xanh dương.
- Chữa cháy: sprinkler là hai vòng tròn đồng tâm + dấu chéo màu đỏ, hộp họng "FHR" là khung đỏ có
  tam giác tô đặc, bình CO2 / ABC là ô bo góc đỏ có vòng tròn ghi chữ, tủ dụng cụ phá dỡ.
- Chiếu sáng sự cố: EXIT xanh lá, đèn sự cố hai bóng đỏ, sơ đồ thoát nạn phòng SDTNP tím.

Hình học block tính bằng **mm trên giấy**; khi chèn, block được phóng theo tỷ lệ in (1:100 → ×100 với
bản vẽ đơn vị mm). Nhờ vậy ký hiệu in ra luôn cùng cỡ dù tờ in 1:100 hay 1:125. Màu đặt trực tiếp
trong block (giống bản mẫu: S đỏ, H xanh), layer chỉ để lọc và thống kê.

    import ky_hieu as kh
    kh.TY_LE = 125                          # tỷ lệ in của tờ (mặc định 100)
    kh.dam_bao_tat_ca(doc)                  # tạo kiểu chữ, layer, block (ezdxf)
    kh.chen(msp, "sprinkler", (x, y))       # chèn đúng block + layer + tỷ lệ
    kh.ve_bang(msp, (x0, y0), ["sprinkler", ...])  # bảng "GHI CHÚ:" ký hiệu
"""
import math

KIEU_CHU = "PCCC_ARIAL"          # Arial: ghi chú, bảng, chữ trong ký hiệu
KIEU_CHU_HEP = "PCCC_ARIALN"     # Arial Narrow: chữ dim (bản mẫu dùng font condensed)
CO_CHU = 150                     # chữ ghi chú thường trong model (mm) khi in 1:100 = 1,5 mm
TY_LE = 100                      # tỷ lệ in mặc định; đổi trước khi chèn nếu tờ in tỷ lệ khác
DON_VI_MM = True                 # bản vẽ đơn vị mm (False: đơn vị m)

# Màu ACI theo bản mẫu (RGB đo từ PDF → ACI gần nhất)
DO, XANH_LA, XANH_DUONG, TIM, XANH_NHAT, XAM = 1, 3, 5, 6, 4, 8
TIM_DIM = 173                    # nét dim xanh tím (91,91,184)

# loai: (tên block, layer, màu layer, mô tả trong bảng ký hiệu, hình học [mm giấy])
# Hình học:
#   ("tron", r, mau) | ("tron_dac", r, mau) | ("cheo", r, mau) [hai nét chéo trong vòng r]
#   ("hcn", w, h, mau[, (cx, cy)[, bo_goc]]) | ("dac", [(x, y), ...], mau) [đa giác tô đặc]
#   ("net", (x1, y1), (x2, y2), mau) | ("chu", s, cao, mau[, (x, y)[, "dam"]])
#   ("van", w, h, mau) [hai tam giác đối đỉnh]
KY_HIEU = {
    # --- Chữa cháy tự động ---
    "sprinkler":  ("PCCC_SPR", "PCCC-SPR", DO, "ĐẦU PHUN SPRINKLER 68°C, K=80 (5.6)",
                   [("tron", 1.75, DO), ("tron", 0.8, DO), ("cheo", 1.75, DO)]),
    "truc_spr":   ("PCCC_TRUC_SPR", "PCCC-ONG-SPR", DO, "TRỤC ĐỨNG CẤP NƯỚC CHỮA CHÁY",
                   [("tron_dac", 0.9, DO)]),
    "van_spr":    ("PCCC_VAN_SPR", "PCCC-ONG-SPR", DO, "VAN KHOÁ + CÔNG TẮC DÒNG CHẢY",
                   [("van", 3.0, 1.8, DO), ("hcn", 1.6, 1.2, DO, (0, 1.8)), ("chu", "FS", 0.7, DO, (0, 1.8))]),
    # --- Họng nước, bình, dụng cụ ---
    "hong":       ("PCCC_FHR", "PCCC-HONG", DO,
                   "HỌNG NƯỚC CHỮA CHÁY GỒM: 01 VAN GÓC DN50, 01 CUỘN VÒI DN50 DÀI 20 m, 01 LĂNG PHUN D13",
                   [("hcn", 6.0, 2.2, DO), ("dac", [(-3.0, 1.1), (3.0, 1.1), (3.0, -0.5)], DO),
                    ("chu", "FHR", 0.9, DO, (1.6, -0.6))]),
    "truc_hong":  ("PCCC_TRUC_HONG", "PCCC-ONG-HONG", DO, "TRỤC ĐỨNG CẤP NƯỚC HỌNG CHỮA CHÁY",
                   [("tron_dac", 0.9, DO)]),
    "binh":       ("PCCC_ABC", "PCCC-BINH", DO, "BÌNH CHỮA CHÁY BỘT ABC 8 KG",
                   [("hcn", 2.6, 2.6, DO, (0, 0), 0.4), ("tron", 1.0, DO), ("chu", "ABC", 0.55, DO)]),
    "binh_co2":   ("PCCC_CO2", "PCCC-BINH", DO, "BÌNH CHỮA CHÁY CO2 5 KG",
                   [("hcn", 2.6, 2.6, DO, (0, 0), 0.4), ("tron", 1.0, DO), ("chu", "CO2", 0.55, DO)]),
    "tu_dung_cu": ("PCCC_TU_DC", "PCCC-BINH", DO, "TỦ DỤNG CỤ PHÁ DỠ THÔNG THƯỜNG",
                   [("hcn", 4.0, 2.6, DO), ("net", (-1.2, -0.9), (1.0, 0.9), DO),
                    ("dac", [(0.4, 1.0), (1.4, 0.4), (1.1, 0.1), (0.2, 0.6)], DO),
                    ("net", (1.2, -0.9), (-0.6, 0.9), DO)]),
    "hong_tiep":  ("PCCC_HONG_TIEP", "PCCC-HONG", DO, "HỌNG TIẾP NƯỚC NGOÀI NHÀ 2 CỬA DN65",
                   [("dac", [(-1.2, 0), (-0.85, 0.85), (0, 1.2), (0.85, 0.85), (1.2, 0)], DO),
                    ("net", (-1.2, 0), (1.2, 0), DO), ("tron", 0.45, DO, ), ]),
    # --- Báo cháy ---
    "bao_khoi":   ("PCCC_DBK", "PCCC-BAO-KHOI", DO, "ĐẦU BÁO CHÁY KHÓI",
                   [("tron", 1.7, DO), ("chu", "S", 2.0, DO, (0, 0), "dam")]),
    "bao_nhiet":  ("PCCC_DBN", "PCCC-BAO-NHIET", XANH_LA, "ĐẦU BÁO CHÁY NHIỆT",
                   [("tron", 1.7, XANH_LA), ("chu", "H", 2.0, XANH_LA, (0, 0), "dam")]),
    "nut_an":     ("PCCC_NA", "PCCC-NUT-AN", XANH_LA, "NÚT NHẤN KHẨN",
                   [("hcn", 3.0, 3.0, XANH_LA, (0, 0), 0.5), ("hcn", 2.2, 2.2, XANH_LA),
                    ("chu", "FIRE", 0.55, XANH_LA, (0, 0.6)),
                    ("net", (-0.8, -0.8), (-0.4, 0.0), XANH_LA), ("net", (-0.2, -0.8), (0.2, 0.0), XANH_LA),
                    ("net", (0.4, -0.8), (0.8, 0.0), XANH_LA)]),
    "chuong_den": ("PCCC_CD", "PCCC-CHUONG-DEN", XANH_LA, "CHUÔNG BÁO CHÁY + ĐÈN",
                   [("hcn", 3.0, 3.0, XANH_LA, (0, 0), 0.5), ("hcn", 1.4, 0.5, XANH_LA, (0, 1.0)),
                    ("tron", 0.9, XANH_LA, (0, -0.3)),
                    ("net", (-0.9, -0.3), (0.9, -0.3), XANH_LA), ("net", (0, -1.2), (0, 0.6), XANH_LA),
                    ("net", (-0.64, -0.94), (0.64, 0.34), XANH_LA), ("net", (-0.64, 0.34), (0.64, -0.94), XANH_LA)]),
    "tu_tt":      ("PCCC_FACP", "PCCC-TU-BC", DO, "TỦ BÁO CHÁY TRUNG TÂM",
                   [("hcn", 8.0, 2.4, DO), ("chu", "FACP", 1.4, XANH_NHAT)]),
    "den_fire":   ("PCCC_FIRE", "PCCC-TU-BC", DO, "ĐÈN BÁO CHÁY FIRE NGOÀI NHÀ",
                   [("hcn", 6.0, 2.2, DO), ("chu", "FIRE", 1.3, DO, (0, 0), "dam")]),
    "den_phong":  ("PCCC_DEN_PHONG", "PCCC-CHUONG-DEN", XANH_DUONG, "ĐÈN BÁO CHÁY PHÒNG",
                   [("hcn", 2.4, 3.2, XANH_DUONG), ("net", (0.5, -1.6), (0.5, 1.6), XANH_DUONG),
                    ("tron", 0.55, XANH_DUONG, (0.5, 0)), ("net", (-0.1, 0), (-0.9, 0), XANH_DUONG),
                    ("net", (0.1, 0.55), (-0.6, 1.1), XANH_DUONG), ("net", (0.1, -0.55), (-0.6, -1.1), XANH_DUONG)]),
    # --- Chiếu sáng sự cố, chỉ dẫn thoát nạn ---
    "exit":       ("PCCC_EXIT", "PCCC-EXIT", XANH_LA, "ĐÈN EXIT, ẮC QUY DỰ PHÒNG HOẠT ĐỘNG 2 GIỜ",
                   [("hcn", 4.0, 1.6, XANH_LA), ("chu", "EXIT", 0.9, XANH_LA)]),
    "exit_huong": ("PCCC_EXIT_HUONG", "PCCC-EXIT", XANH_LA, "ĐÈN CHỈ HƯỚNG EXIT, ẮC QUY DỰ PHÒNG 2 GIỜ",
                   [("hcn", 4.0, 1.6, XANH_LA), ("chu", "EXIT", 0.9, XANH_LA, (-0.5, 0)),
                    ("dac", [(1.1, 0.5), (1.7, 0), (1.1, -0.5)], XANH_LA)]),
    "den_su_co":  ("PCCC_DEN_SC", "PCCC-EXIT", DO, "ĐÈN CHIẾU SÁNG SỰ CỐ, ẮC QUY DỰ PHÒNG 2 GIỜ",
                   [("tron", 0.6, DO, (-0.8, 0.2)), ("tron", 0.6, DO, (0.8, 0.2)),
                    ("cheo", 0.6, DO, (-0.8, 0.2)), ("cheo", 0.6, DO, (0.8, 0.2)),
                    ("hcn", 3.2, 0.5, DO, (0, -0.75))]),
    "sdtnp":      ("PCCC_SDTNP", "PCCC-EXIT", TIM, "SƠ ĐỒ CHỈ DẪN THOÁT NẠN PHÒNG",
                   [("hcn", 4.0, 1.6, TIM), ("chu", "SDTNP", 0.8, TIM)]),
    "sdtn":       ("PCCC_SDTN", "PCCC-EXIT", DO, "SƠ ĐỒ CHỈ DẪN THOÁT NẠN TẦNG",
                   [("hcn", 4.0, 1.6, DO)]),
    "mat_na":     ("PCCC_MAT_NA", "PCCC-EXIT", DO, "HỘP MẶT NẠ PHÒNG ĐỘC",
                   [("hcn", 3.2, 1.6, DO), ("dac", [(-0.9, 0.0), (-0.5, 0.5), (0.0, 0.3), (0.5, 0.5),
                                                    (0.9, 0.0), (0.5, -0.5), (-0.5, -0.5)], DO)]),
    # --- Ký hiệu sơ đồ nguyên lý (so_do.py) ---
    "sd_van":     ("PCCC_SD_VAN", "PCCC-SO-DO", 7, "VAN CỔNG / VAN KHOÁ",
                   [("van", 3.0, 1.8, DO), ("net", (0, 0), (0, 1.6), DO), ("net", (-0.7, 1.6), (0.7, 1.6), DO)]),
    "sd_van_1c":  ("PCCC_SD_VAN_1C", "PCCC-SO-DO", 7, "VAN 1 CHIỀU",
                   [("van", 3.0, 1.8, DO), ("dac", [(-1.5, -0.9), (0, 0), (-1.5, 0.9)], DO),
                    ("net", (0, -1.1), (0, 1.1), DO)]),
    "sd_y_loc":   ("PCCC_SD_Y_LOC", "PCCC-SO-DO", 7, "Y LỌC",
                   [("net", (-1.5, 0), (1.5, 0), DO), ("net", (-0.6, 0), (0.6, -1.2), DO),
                    ("net", (0.2, -1.6), (1.0, -0.8), DO)]),
    "sd_khop_mem": ("PCCC_SD_KHOP_MEM", "PCCC-SO-DO", 7, "KHỚP NỐI MỀM",
                   [("net", (-1.5, -0.8), (-0.75, 0.8), DO), ("net", (-0.75, 0.8), (0, -0.8), DO),
                    ("net", (0, -0.8), (0.75, 0.8), DO), ("net", (0.75, 0.8), (1.5, -0.8), DO)]),
    "sd_dong_ho": ("PCCC_SD_DONG_HO", "PCCC-SO-DO", 7, "ĐỒNG HỒ ÁP",
                   [("net", (0, 0), (0, 1.0), DO), ("tron", 0.8, DO, (0, 1.8)), ("net", (0, 1.8), (0.5, 2.3), DO)]),
    "sd_cong_tac_ap": ("PCCC_SD_CTA", "PCCC-SO-DO", 7, "CÔNG TẮC ÁP LỰC",
                   [("net", (0, 0), (0, 1.0), DO), ("hcn", 1.8, 1.4, DO, (0, 1.7)), ("chu", "P", 0.9, DO, (0, 1.7))]),
    "sd_van_an_toan": ("PCCC_SD_VAT", "PCCC-SO-DO", 7, "VAN AN TOÀN",
                   [("dac", [(-0.8, 0), (0.8, 0), (0, 1.2)], DO), ("net", (0, 1.2), (-0.5, 1.6), DO),
                    ("net", (-0.5, 1.6), (0.5, 2.0), DO), ("net", (0.5, 2.0), (-0.5, 2.4), DO)]),
    "sd_bom":     ("PCCC_SD_BOM", "PCCC-SO-DO", 7, "BƠM CHỮA CHÁY",
                   [("tron", 2.0, DO), ("net", (-1.0, 1.73), (2.0, 0), DO), ("net", (-1.0, -1.73), (2.0, 0), DO)]),
    "sd_van_phao": ("PCCC_SD_VAN_PHAO", "PCCC-SO-DO", 7, "VAN PHAO",
                   [("van", 2.4, 1.4, DO), ("net", (0, 0), (0, -1.6), DO), ("tron", 0.6, DO, (0, -2.2))]),
    "sd_cong_tac_dong": ("PCCC_SD_FS", "PCCC-SO-DO", 7, "CÔNG TẮC DÒNG CHẢY",
                   [("hcn", 2.2, 1.6, DO), ("chu", "FS", 0.9, DO)]),
    "sd_van_xa_khi": ("PCCC_SD_AAV", "PCCC-SO-DO", 7, "VAN XẢ KHÍ",
                   [("hcn", 2.0, 1.4, DO), ("chu", "AAV", 0.6, DO)]),
    "sd_van_bao_dong": ("PCCC_SD_AV", "PCCC-SO-DO", 7, "CỤM VAN BÁO ĐỘNG",
                   [("tron", 1.4, DO), ("chu", "AV", 0.9, DO)]),
    "sd_dau_phun": ("PCCC_SD_DAU_PHUN", "PCCC-SO-DO", 7, "ĐẦU PHUN SPRINKLER 68°C (SƠ ĐỒ)",
                   [("net", (0, 0), (0, -0.8), DO), ("dac", [(-0.7, -0.8), (0.7, -0.8), (0, -1.9)], DO)]),
    "sd_tu_hong": ("PCCC_SD_TU_HONG", "PCCC-SO-DO", 7, "TỦ CHỮA CHÁY VÁCH TƯỜNG",
                   [("hcn", 3.6, 2.2, XANH_LA), ("dac", [(-1.4, -0.8), (1.4, 0.8), (1.4, -0.8), (-1.4, 0.8)], XANH_LA)]),
    "sd_eol":     ("PCCC_SD_EOL", "PCCC-SO-DO", 7, "ĐIỆN TRỞ CUỐI LINE (EOL)",
                   [("hcn", 2.4, 1.0, DO), ("net", (-2.0, 0), (-1.2, 0), DO), ("net", (1.2, 0), (2.0, 0), DO)]),
    "sd_ac_quy":  ("PCCC_SD_AC_QUY", "PCCC-SO-DO", 7, "ẮC QUY",
                   [("net", (-1.2, 0.6), (1.2, 0.6), 7), ("net", (-0.6, -0.2), (0.6, -0.2), 7),
                    ("net", (0, 0.6), (0, 1.4), 7), ("net", (0, -0.2), (0, -1.0), 7)]),
}

# Đường kẻ (cáp, ống): (layer, màu, kiểu nét, độ dày in mm, mô tả)
LAYER_CAP_BC = ("PCCC-CAP-BC", TIM, "DASHED", 0.30, "DÂY CHỐNG CHÁY 30 PHÚT 2x1,5 mm²")
# Ống theo đường kính: DN ≥ 50 vẽ hai nét (đỏ, đậm), DN < 50 một nét (tím, mảnh) như bản mẫu
LAYER_ONG = {"spr": ("PCCC-ONG-SPR", DO, "ỐNG THÉP TRÁNG KẼM CẤP NƯỚC CHỮA CHÁY (DN GHI TRÊN ỐNG)"),
             "hong": ("PCCC-ONG-HONG", DO, "ỐNG THÉP TRÁNG KẼM CẤP NƯỚC HỌNG CHỮA CHÁY (DN GHI TRÊN ỐNG)")}
LAYER_VIEN_ONG = ("PCCC-VIEN-ONG", DO, "CONTINUOUS", 0.50)   # nét viền ống lớn (không đếm chiều dài)
LAYER_TEXT = ("PCCC-TEXT", 7)
LAYER_DN = ("PCCC-TEXT-DN", TIM)


def he_so_chen(ty_le=None):
    """Hệ số phóng block (mm giấy → đơn vị bản vẽ)."""
    return (ty_le or TY_LE) * (1.0 if DON_VI_MM else 0.001)


def layer_ong(he, dn):
    """Layer ống theo hệ và đường kính, ví dụ PCCC-ONG-SPR-D25 (để thống kê theo DN)."""
    return f"{LAYER_ONG[he][0]}-D{int(dn)}"


def mau_ong(dn):
    return DO if dn >= 50 else TIM


def dam_bao_kieu_chu(doc):
    if KIEU_CHU not in doc.styles:
        doc.styles.new(KIEU_CHU, dxfattribs={"font": "arial.ttf"})
    if KIEU_CHU_HEP not in doc.styles:
        doc.styles.new(KIEU_CHU_HEP, dxfattribs={"font": "arialn.ttf"})
    if KIEU_CHU + "_B" not in doc.styles:
        doc.styles.new(KIEU_CHU + "_B", dxfattribs={"font": "arialbd.ttf"})


def _hcn_bo(cx, cy, w, h, r):
    """Đỉnh LWPOLYLINE hình chữ nhật bo góc (x, y, sw, ew, bulge)."""
    if r <= 0:
        return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    b = math.tan(math.pi / 8)  # cung 90°
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0 + r, y0, 0, 0, 0), (x1 - r, y0, 0, 0, b), (x1, y0 + r, 0, 0, 0), (x1, y1 - r, 0, 0, b),
            (x1 - r, y1, 0, 0, 0), (x0 + r, y1, 0, 0, b), (x0, y1 - r, 0, 0, 0), (x0, y0 + r, 0, 0, b)]


def _ve_block(doc, loai):
    import ezdxf
    ten, _, _, _, hinh = KY_HIEU[loai]
    if ten in doc.blocks:
        doc.blocks.delete_block(ten, safe=False)
    b = doc.blocks.new(ten)
    for h in hinh:
        k = h[0]
        if k in ("tron", "tron_dac", "cheo"):
            r, mau = h[1], h[2]
            c = h[3] if len(h) > 3 else (0, 0)
            a = {"color": mau, "layer": "0"}
            if k == "cheo":
                d = r * 0.707
                b.add_line((c[0] - d, c[1] - d), (c[0] + d, c[1] + d), dxfattribs=a)
                b.add_line((c[0] - d, c[1] + d), (c[0] + d, c[1] - d), dxfattribs=a)
                continue
            b.add_circle(c, r, dxfattribs=a)
            if k == "tron_dac":
                ht = b.add_hatch(color=mau, dxfattribs={"layer": "0"})
                ht.paths.add_edge_path().add_arc(c, r, 0, 360)
        elif k == "hcn":
            w, hh, mau = h[1], h[2], h[3]
            c = h[4] if len(h) > 4 else (0, 0)
            r = h[5] if len(h) > 5 else 0
            pts = _hcn_bo(c[0], c[1], w, hh, r)
            b.add_lwpolyline(pts, format="xyseb" if r else "xy", close=True,
                             dxfattribs={"color": mau, "layer": "0"})
        elif k == "dac":
            pts, mau = h[1], h[2]
            b.add_lwpolyline(pts, close=True, dxfattribs={"color": mau, "layer": "0"})
            ht = b.add_hatch(color=mau, dxfattribs={"layer": "0"})
            ht.paths.add_polyline_path(pts, is_closed=True)
        elif k == "net":
            b.add_line(h[1], h[2], dxfattribs={"color": h[3], "layer": "0"})
        elif k == "van":
            w, d, mau = h[1] / 2, h[2] / 2, h[3]
            b.add_lwpolyline([(-w, -d), (w, d), (w, -d), (-w, d)], close=True,
                             dxfattribs={"color": mau, "layer": "0"})
        elif k == "chu":
            s, cao, mau = h[1], h[2], h[3]
            p = h[4] if len(h) > 4 else (0, 0)
            kieu = KIEU_CHU + "_B" if len(h) > 5 and h[5] == "dam" else KIEU_CHU
            b.add_text(s, height=cao, dxfattribs={"color": mau, "layer": "0", "style": kieu}).set_placement(
                p, align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)


def dam_bao_layer(doc, ten, mau, kieu_net="CONTINUOUS", day=None):
    if ten not in doc.layers:
        la = doc.layers.add(ten, color=mau)
        if kieu_net != "CONTINUOUS":
            if kieu_net not in doc.linetypes:
                doc.linetypes.add(kieu_net, pattern=[0.75, 0.5, -0.25], description="__ __ __")
            la.dxf.linetype = kieu_net
        if day:
            la.dxf.lineweight = int(round(day * 100))
    return doc.layers.get(ten)


def dam_bao_tat_ca(doc, ve_lai=True):
    """Tạo kiểu chữ, layer và toàn bộ block ký hiệu (ve_lai=True: định nghĩa lại block đã có)."""
    dam_bao_kieu_chu(doc)
    for loai, (ten, layer, mau, _, _) in KY_HIEU.items():
        dam_bao_layer(doc, layer, mau)
        if ve_lai or ten not in doc.blocks:
            _ve_block(doc, loai)
    dam_bao_layer(doc, LAYER_CAP_BC[0], LAYER_CAP_BC[1], LAYER_CAP_BC[2], LAYER_CAP_BC[3])
    dam_bao_layer(doc, LAYER_VIEN_ONG[0], LAYER_VIEN_ONG[1], day=LAYER_VIEN_ONG[3])
    for layer, mau in [LAYER_TEXT, LAYER_DN] + [v[:2] for v in LAYER_ONG.values()]:
        dam_bao_layer(doc, layer, mau)


def chen(msp, loai, diem, ty_le=None, goc=0):
    ten, layer, _, _, _ = KY_HIEU[loai]
    s = he_so_chen(ty_le)
    return msp.add_blockref(ten, diem, dxfattribs={"layer": layer, "xscale": s, "yscale": s, "rotation": goc})


def ve_ong(msp, diem, he, dn, ty_le=None, ghi_dn=True, t_dn=0.5):
    """Vẽ một đoạn ống theo quy cách bản mẫu.

    - Đường tim luôn vẽ trên layer theo DN (PCCC-ONG-SPR-D25…) để thống kê chiều dài.
    - DN ≥ 50: thêm hai nét viền đỏ đậm cách nhau ~2,8 mm giấy (ống chính như bản mẫu).
    - DN < 50: một nét tím mảnh.
    - Ghi "DNxx" cỡ 1,8 mm giấy, màu tím, xoay theo ống, lệch sang một bên, tại vị trí t_dn (0–1)
      dọc đoạn dài nhất. Nhánh nối giữa ống chính thì vẽ thành hai nửa để mỗi nửa có nhãn riêng.
    """
    import ezdxf
    s = he_so_chen(ty_le)
    layer = layer_ong(he, dn)
    if layer not in msp.doc.layers:
        dam_bao_layer(msp.doc, layer, mau_ong(dn), day=0.13 if dn < 50 else 0.18)
    msp.add_lwpolyline(diem, dxfattribs={"layer": layer})
    if dn >= 50:
        nua = 1.4 * s
        for p1, p2 in zip(diem, diem[1:]):
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L * nua, dx / L * nua
            for k in (1, -1):
                msp.add_line((p1[0] + k * nx, p1[1] + k * ny), (p2[0] + k * nx, p2[1] + k * ny),
                             dxfattribs={"layer": LAYER_VIEN_ONG[0]})
            for p in ((p1,) if p1 == diem[0] else ()) + ((p2,) if p2 == diem[-1] else ()):
                msp.add_line((p[0] + nx, p[1] + ny), (p[0] - nx, p[1] - ny), dxfattribs={"layer": LAYER_VIEN_ONG[0]})
    if ghi_dn:
        (x1, y1), (x2, y2) = max(zip(diem, diem[1:]), key=lambda d: math.dist(*d))
        goc = math.degrees(math.atan2(y2 - y1, x2 - x1))
        if goc > 90 or goc <= -90:
            goc += 180
        lech = (2.6 if dn >= 50 else 1.2) * s
        nx, ny = -math.sin(math.radians(goc)) * lech, math.cos(math.radians(goc)) * lech
        msp.add_text(f"DN{int(dn)}", height=1.8 * s, rotation=goc,
                     dxfattribs={"layer": LAYER_DN[0], "style": KIEU_CHU, "color": mau_ong(dn) if dn < 50 else TIM}
                     ).set_placement((x1 + (x2 - x1) * t_dn - nx, y1 + (y2 - y1) * t_dn - ny),
                                     align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)


def _ngat_dong(chu, toi_da):
    dong, cur = [], ""
    for tu in chu.split():
        if cur and len(cur) + 1 + len(tu) > toi_da:
            dong.append(cur)
            cur = tu
        else:
            cur = f"{cur} {tu}".strip()
    return dong + ([cur] if cur else [])


def ve_bang(msp, goc, cac_loai, co_cap=False, tieu_de="GHI CHÚ:", ong=(), ty_le=None, rong_mm=75.0):
    """Bảng ký hiệu kiểu bản mẫu: tiêu đề "GHI CHÚ:" gạch chân phía trên, bảng 2 cột
    (ô ký hiệu 10 mm | mô tả chữ in hoa 2,4 mm), mỗi dòng 6,3 mm giấy (mô tả dài tự xuống dòng,
    dòng cao thêm). Góc dưới-trái tại `goc`; trả về khung bao (x0, y0, x1, y1).
    `ong`: các loại ống cần đưa vào bảng, khoá trong LAYER_ONG ("spr", "hong")."""
    import ezdxf
    s = he_so_chen(ty_le)
    x0, y0 = goc
    dong = list(cac_loai) + (["_cap"] if co_cap else []) + [f"_ong_{k}" for k in ong]
    rong, cot, co = rong_mm * s, 10.0 * s, 2.4
    toi_da = int((rong_mm - 10 - 4) / (co * 0.74))  # chữ in hoa Arial rộng ~0,74 cỡ chữ
    mo_ta = {}
    for loai in dong:
        if loai == "_cap":
            mo_ta[loai] = LAYER_CAP_BC[4]
        elif loai.startswith("_ong_"):
            mo_ta[loai] = LAYER_ONG[loai[5:]][2]
        else:
            mo_ta[loai] = KY_HIEU[loai][3]
    cao_dong = [max(6.3, 3.6 * len(_ngat_dong(mo_ta[l], toi_da)) + 2.2) * s for l in dong]
    cao = sum(cao_dong)
    t = {"layer": LAYER_TEXT[0], "style": KIEU_CHU}
    L = {"layer": LAYER_TEXT[0]}
    msp.add_lwpolyline([(x0, y0), (x0 + rong, y0), (x0 + rong, y0 + cao), (x0, y0 + cao)], close=True, dxfattribs=L)
    msp.add_line((x0 + cot, y0), (x0 + cot, y0 + cao), dxfattribs=L)
    tt = msp.add_text(tieu_de, height=3.0 * s, dxfattribs=t)
    tt.set_placement((x0, y0 + cao + 1.8 * s), align=ezdxf.enums.TextEntityAlignment.BOTTOM_LEFT)
    msp.add_line((x0, y0 + cao + 1.2 * s), (x0 + 0.62 * 3.0 * s * len(tieu_de), y0 + cao + 1.2 * s), dxfattribs=L)
    y_tren = y0 + cao
    for loai, h_dong in zip(dong, cao_dong):
        yc = y_tren - h_dong / 2
        xc = x0 + cot / 2
        if loai == "_cap":
            msp.add_line((xc - 3.5 * s, yc), (xc + 3.5 * s, yc), dxfattribs={"layer": LAYER_CAP_BC[0]})
        elif loai.startswith("_ong_"):
            for k in (1, -1):
                msp.add_line((xc - 3.5 * s, yc + k * 0.7 * s), (xc + 3.5 * s, yc + k * 0.7 * s),
                             dxfattribs={"layer": LAYER_VIEN_ONG[0]})
        else:
            chen(msp, loai, (xc, yc), ty_le)
        cac_dong = _ngat_dong(mo_ta[loai], toi_da)
        for j, d in enumerate(cac_dong):
            msp.add_text(d, height=co * s, dxfattribs=t).set_placement(
                (x0 + cot + 2.0 * s, yc + (len(cac_dong) / 2 - j - 0.5) * 3.6 * s),
                align=ezdxf.enums.TextEntityAlignment.MIDDLE_LEFT)
        y_tren -= h_dong
        if y_tren > y0 + 1e-6:
            msp.add_line((x0, y_tren), (x0 + rong, y_tren), dxfattribs=L)
    return (x0, y0, x0 + rong, y0 + cao + 5 * s)
