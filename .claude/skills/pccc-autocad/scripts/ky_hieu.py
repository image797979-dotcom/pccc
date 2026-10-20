"""Bộ ký hiệu thiết bị PCCC thống nhất (một định nghĩa dùng cho mọi tờ, mọi script).

Mọi ký hiệu cùng khung ~400 mm (in 1:100 ra 4 mm), cùng cỡ chữ 150 mm, cùng kiểu chữ Arial
(TrueType, hiển thị đúng tiếng Việt). Nét vẽ trong block để màu BYBLOCK nên màu ăn theo layer
của đối tượng chèn. Theo quy ước bản vẽ hiện trạng: "S" = đầu báo khói, "H" = đầu báo nhiệt.

    import ky_hieu as kh
    kh.dam_bao_tat_ca(doc)                  # tạo text style, layer, block (ezdxf)
    kh.chen(msp, "sprinkler", (x, y))       # chèn đúng block + layer
    kh.ve_bang(msp, (x0, y0), ["sprinkler", ...])  # bảng ký hiệu
"""
KIEU_CHU = "PCCC_ARIAL"
CO_CHU = 150

# loai: (tên block, layer, màu ACI, mô tả trong bảng ký hiệu, hình học)
# hình học: ("tron", r) | ("vuong", w, h) | ("cheo", r) [hai nét chéo trong hình tròn] | ("chu", s)
KY_HIEU = {
    "sprinkler":  ("PCCC_SPR",  "PCCC-SPR",        1,  "ĐẦU PHUN SPRINKLER QUAY XUỐNG DN15, 68°C",
                   [("tron", 150), ("cheo", 150)]),
    "bao_khoi":   ("PCCC_DBK",  "PCCC-BAO-KHOI",   6,  "ĐẦU BÁO CHÁY KHÓI",
                   [("tron", 200), ("chu", "S")]),
    "bao_nhiet":  ("PCCC_DBN",  "PCCC-BAO-NHIET",  30, "ĐẦU BÁO CHÁY NHIỆT",
                   [("tron", 200), ("chu", "H")]),
    "nut_an":     ("PCCC_NA",   "PCCC-NUT-AN",     6,  "NÚT ẤN BÁO CHÁY",
                   [("vuong", 400, 400), ("chu", "NA")]),
    "chuong_den": ("PCCC_CD",   "PCCC-CHUONG-DEN", 6,  "CHUÔNG + ĐÈN BÁO CHÁY",
                   [("vuong", 400, 400), ("chu", "CĐ")]),
    "tu_tt":      ("PCCC_TTBC", "PCCC-TU-BC",      6,  "TỦ TRUNG TÂM BÁO CHÁY",
                   [("vuong", 800, 400), ("chu", "TTBC")]),
    "hong":       ("PCCC_HONG", "PCCC-HONG",       5,  "HỘP HỌNG NƯỚC CHỮA CHÁY VÁCH TƯỜNG",
                   [("vuong", 800, 300), ("chu", "HN")]),
    "binh":       ("PCCC_BINH", "PCCC-BINH",       3,  "BÌNH CHỮA CHÁY XÁCH TAY (BỘT ABC 4 KG / CO2 5 KG)",
                   [("vuong", 300, 400), ("chu", "B")]),
}
LAYER_CAP_BC = ("PCCC-CAP-BC", 6, "CÁP TÍN HIỆU BÁO CHÁY")
LAYER_TEXT = ("PCCC-TEXT", 7)


def dam_bao_kieu_chu(doc):
    if KIEU_CHU not in doc.styles:
        doc.styles.new(KIEU_CHU, dxfattribs={"font": "arial.ttf"})


def _ve_block(doc, loai):
    import ezdxf
    ten, _, _, _, hinh = KY_HIEU[loai]
    if ten in doc.blocks:
        doc.blocks.delete_block(ten, safe=False)
    b = doc.blocks.new(ten)
    nen = {"color": 0, "layer": "0"}  # BYBLOCK
    for h in hinh:
        if h[0] == "tron":
            b.add_circle((0, 0), h[1], dxfattribs=nen)
        elif h[0] == "vuong":
            w, d = h[1] / 2, h[2] / 2
            b.add_lwpolyline([(-w, -d), (w, -d), (w, d), (-w, d)], close=True, dxfattribs=nen)
        elif h[0] == "cheo":
            r = h[1] * 0.707
            b.add_line((-r, -r), (r, r), dxfattribs=nen)
            b.add_line((-r, r), (r, -r), dxfattribs=nen)
        elif h[0] == "chu":
            b.add_text(h[1], height=CO_CHU, dxfattribs={**nen, "style": KIEU_CHU}).set_placement(
                (0, 0), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)


def dam_bao_tat_ca(doc, ve_lai=True):
    """Tạo kiểu chữ, layer và toàn bộ block ký hiệu (ve_lai=True: định nghĩa lại block đã có)."""
    dam_bao_kieu_chu(doc)
    for loai, (ten, layer, mau, _, _) in KY_HIEU.items():
        if layer not in doc.layers:
            doc.layers.add(layer, color=mau)
        if ve_lai or ten not in doc.blocks:
            _ve_block(doc, loai)
    for layer, mau in [LAYER_CAP_BC[:2], LAYER_TEXT]:
        if layer not in doc.layers:
            doc.layers.add(layer, color=mau)


def chen(msp, loai, diem):
    ten, layer, _, _, _ = KY_HIEU[loai]
    return msp.add_blockref(ten, diem, dxfattribs={"layer": layer})


def ve_bang(msp, goc, cac_loai, co_cap=False, tieu_de="KÝ HIỆU"):
    """Bảng ký hiệu: góc dưới-trái tại `goc`, mỗi dòng 600 mm. Dùng chính các block ở trên."""
    import ezdxf
    x0, y0 = goc
    dong = list(cac_loai) + (["_cap"] if co_cap else [])
    cao = 600 * (len(dong) + 1)
    rong = 9000
    t = {"layer": LAYER_TEXT[0], "style": KIEU_CHU}
    msp.add_lwpolyline([(x0, y0), (x0 + rong, y0), (x0 + rong, y0 + cao), (x0, y0 + cao)], close=True,
                       dxfattribs={"layer": LAYER_TEXT[0]})
    msp.add_line((x0, y0 + cao - 600), (x0 + rong, y0 + cao - 600), dxfattribs={"layer": LAYER_TEXT[0]})
    msp.add_line((x0 + 1200, y0), (x0 + 1200, y0 + cao - 600), dxfattribs={"layer": LAYER_TEXT[0]})
    msp.add_text(tieu_de, height=250, dxfattribs=t).set_placement(
        (x0 + rong / 2, y0 + cao - 300), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    for i, loai in enumerate(reversed(dong)):
        yc = y0 + 300 + 600 * i
        if loai == "_cap":
            msp.add_line((x0 + 200, yc), (x0 + 1000, yc), dxfattribs={"layer": LAYER_CAP_BC[0]})
            mo_ta = LAYER_CAP_BC[2]
        else:
            chen(msp, loai, (x0 + 600, yc))
            mo_ta = KY_HIEU[loai][3]
        msp.add_text(mo_ta, height=CO_CHU, dxfattribs=t).set_placement(
            (x0 + 1400, yc), align=ezdxf.enums.TextEntityAlignment.MIDDLE_LEFT)
