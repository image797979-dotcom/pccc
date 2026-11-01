"""Quy cách trình bày tờ bản vẽ PCCC theo hồ sơ mẫu đã duyệt (KS 32 Dã Tượng, 10/2026).

Mọi kích thước khai báo bằng **mm trên giấy** rồi nhân với tỷ lệ in, nên đổi tỷ lệ tờ (1:100, 1:125…)
không phải sửa gì. Chi tiết quy cách và lý do: references/trinh-bay-ban-ve.md.

    import ky_hieu as kh, trinh_bay as tb
    tb.dam_bao(doc, ty_le=125)                       # kiểu chữ, layer, block, dim style "PCCC"
    vung = tb.khung_a3(msp, (0, 0), 125, THONG_TIN)  # khung + cột tên bên phải; trả về vùng vẽ
    tb.dim_theo_truc(msp, truc_x, x_dau_phun, y_dat=..., ngang=True)
    tb.dim_goc_xa(msp, dau_bao, polygon_phong)       # dim chéo tới góc xa nhất (đầu báo)
    tb.vong_phuc_vu(msp, tam_hong, 20000)            # vòng bán kính phục vụ họng nước
    tb.tieu_de_to(msp, "MẶT BẰNG TẦNG 1", (x, y))
"""
import math

import ky_hieu as kh

LAYER_DIM = ("PCCC-DIM", kh.TIM_DIM)
LAYER_KHUNG = ("PCCC-KHUNG", 7)
LAYER_BAN_KINH = ("PCCC-BAN-KINH", kh.TIM_DIM)
DIMSTYLE = "PCCC"

# Kiểu dim của bản mẫu: chữ đỏ Arial Narrow 4,2 mm, nét dim + gạch chéo xanh tím, chữ nằm trên đường dim
KIEU_DIM = {
    "dimtxt": 4.2, "dimasz": 1.8, "dimblk": "OBLIQUE", "dimexo": 0.6, "dimexe": 1.2, "dimgap": 0.8,
    "dimtad": 1, "dimtih": 0, "dimtoh": 0, "dimdec": 0, "dimtmove": 2, "dimatfit": 3, "dimtix": 1,
    "dimclrt": kh.DO, "dimclrd": kh.TIM_DIM, "dimclre": kh.TIM_DIM, "dimlwd": 30, "dimlwe": 13,
}

# Cỡ chữ (mm giấy) đo từ bản mẫu
CO = {"tieu_de_to": 5.35, "ghi_chu_lon": 3.7, "ghi_chu_hop": 2.3, "bang": 2.4, "ten_phong": 2.4,
      "dn": 1.8, "tieu_de_bang": 2.8}

# Khổ A3 ngang và cột thông tin bên phải (mm giấy)
A3 = (420.0, 297.0)
LE = (5.0, 4.0)                  # lề trái/phải 5 mm, trên/dưới 4 mm
RONG_COT_TEN = 41.6
# (chiều cao mm, nội dung) từ trên xuống, đo từ bản mẫu
O_COT_TEN = [(26, "phat_hanh"), (43, "chu_dau_tu"), (44, "don_vi"), (31, "giam_doc"), (32, "chu_tri"),
             (31, "thiet_ke"), (33, "du_an"), (4, "ngay"), (34, "sua_doi"), (11, "so_to")]

# Ghi chú mẫu (lấy từ hồ sơ đã duyệt, sửa lại cho từng công trình)
GHI_CHU_BAO_CHAY = [
    "- Trên trần treo kỹ thuật chỉ bố trí cáp, dây dẫn điện của hệ thống chiếu sáng, hệ thống thông tin",
    "--> không thuộc diện phải trang bị đầu báo cháy trên không gian trần treo theo Chú thích (2) - Bảng A.2 "
    "Phụ lục A QCVN 10:2025/BCA.",
    "- Không bố trí trần dạng hở.",
]
GHI_CHU_TC_BAO_CHAY = [
    "GHI CHÚ 1:",
    "- THEO TCVN 7568-1:2025 ĐIỀU 5.9.1.1.4 điểm b) NÊU \"KHOẢNG CÁCH TỪ ĐẦU BÁO CHÁY KIỂU ĐIỂM ĐẾN MÉP "
    "NGOÀI GẦN NHẤT CỦA CỬA CẤP KHÔNG KHÍ KHÔNG NHỎ HƠN 0,4M.",
    "- KHÔNG BỐ TRÍ CÁP ĐIỆN TRÊN TRẦN NHÀ WC.",
    "GHI CHÚ 2:",
    "- THEO TCVN 7568-1:2025 ĐIỀU 5.9.2.1.4 ĐIỂM b) NÊU \"KHOẢNG CÁCH TỪ ĐẦU BÁO CHÁY NHIỆT ĐẾN MÉP NGOÀI "
    "LỖ MỞ CẤP KHÔNG KHÍ KHÔNG NHỎ HƠN 0,6M\".",
]
GHI_CHU_CHUNG = [
    "Ghi chú :",
    "- Kho tại các tầng chứa dụng cụ vệ sinh, chủ yếu vật dụng không cháy.",
    "- Hàng hóa, nội thất trong phòng có chiều cao tối đa là 2,2m.",
    "- Trên đường thoát nạn không có bố trí giật cấp, không có thiết bị nhô ra khỏi mặt phẳng dưới 2m trên tường",
    "- Trong không gian tầng không có tủ điện có khối tích > 1m3.",
]
GHI_CHU_CHIEU_SANG = [
    "Lưu ý:",
    "- Đèn chiếu sáng sự cố và đèn Exit lối thoát có pin dự phòng tối thiểu 2h.",
    "- Đèn chiếu sáng sự cố trung bình 10 lux, nhỏ nhất 1 lux tại mọi điểm trên đường thoát nạn.",
    "- Đèn chỉ dẫn thoát nạn phải nhìn thấy rõ chữ \"Lối thoát\" từ khoảng cách tối thiểu 30m.",
    "- Nguồn điện sử dụng là 2 nguồn độc lập: 1 nguồn từ tủ phân phối tại hạng mục công trình và 1 nguồn "
    "từ acquy dự phòng đảm bảo hoạt động 2h.",
    "- Sơ đồ chỉ dẫn thoát nạn có kích thước 600x400mm đối với sơ đồ tại tầng và 400x300mm đối với sơ đồ tại phòng.",
    "- Sơ đồ chỉ dẫn thoát nạn được gắn sao cho mép dưới của sơ đồ nằm ở cao độ 1,5 ± 0,2m so với mặt sàn.",
    "- Lắp đặt đảm bảo theo điều 5.2.9 TCVN 13456:2022.",
]


def _s(ty_le=None):
    return kh.he_so_chen(ty_le)


def dam_bao(doc, ty_le=None):
    """Kiểu chữ, layer, block ký hiệu và dim style PCCC cho tỷ lệ in `ty_le`."""
    if ty_le:
        kh.TY_LE = ty_le
    kh.dam_bao_tat_ca(doc)
    for ten, mau in (LAYER_DIM, LAYER_KHUNG):
        kh.dam_bao_layer(doc, ten, mau)
    kh.dam_bao_layer(doc, LAYER_BAN_KINH[0], LAYER_BAN_KINH[1], "DASHED", 0.13)
    attrs = dict(KIEU_DIM, dimscale=_s(), dimtxsty=kh.KIEU_CHU_HEP)
    if not kh.DON_VI_MM:
        attrs["dimdec"] = 2
    blk = attrs.pop("dimblk")
    if DIMSTYLE in doc.dimstyles:
        ds = doc.dimstyles.get(DIMSTYLE)
        for k, v in attrs.items():
            ds.dxf.set(k, v)
    else:
        ds = doc.dimstyles.new(DIMSTYLE, dxfattribs=attrs)
    ds.set_arrows(blk=blk)
    return ds


def lam_mo_kien_truc(doc, mau=kh.XAM, giu=("PCCC-", "DEFPOINTS", "0")):
    """Nền kiến trúc xám mảnh như bản mẫu: mọi layer không phải PCCC chuyển màu xám, nét mảnh nhất."""
    for la in doc.layers:
        if la.dxf.name.upper().startswith(tuple(g.upper() for g in giu)):
            continue
        la.color = mau
        la.dxf.lineweight = 0


# ---------------- Kích thước ----------------

def dim(msp, p1, p2, vi_tri=None, ngang=None, ty_le=None):
    """Dim thẳng (ngang/dọc) giữa p1, p2; đường dim tại `vi_tri` (toạ độ y nếu ngang, x nếu dọc)."""
    if ngang is None:
        ngang = abs(p2[1] - p1[1]) < abs(p2[0] - p1[0])
    if vi_tri is None:
        vi_tri = p1[1] if ngang else p1[0]
    base = (p1[0], vi_tri) if ngang else (vi_tri, p1[1])
    d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=0 if ngang else 90, dimstyle=DIMSTYLE,
                           dxfattribs={"layer": LAYER_DIM[0]})
    d.render()
    return d


def dim_thang(msp, p1, p2, lech=0.0):
    """Dim chéo (aligned) — dùng cho khoảng cách đầu báo tới góc phòng. Chữ luôn đọc xuôi."""
    if (p2[0], p2[1]) < (p1[0], p1[1]):
        p1, p2 = p2, p1
    d = msp.add_aligned_dim(p1=p1, p2=p2, distance=lech, dimstyle=DIMSTYLE, dxfattribs={"layer": LAYER_DIM[0]})
    d.render()
    return d


def dim_chuoi(msp, toa_do, co_dinh, vi_tri, ngang=True, toi_thieu=1.0):
    """Chuỗi dim nối tiếp qua các toạ độ (x nếu ngang, y nếu dọc) đo trên đường co_dinh,
    đường dim đặt tại vi_tri. Bỏ đoạn ngắn hơn `toi_thieu`."""
    ds = sorted(set(round(t, 3) for t in toa_do))
    gon = [ds[0]] if ds else []
    for t in ds[1:]:
        if t - gon[-1] >= toi_thieu:
            gon.append(t)
    for a, b in zip(gon, gon[1:]):
        if ngang:
            dim(msp, (a, co_dinh), (b, co_dinh), vi_tri, True)
        else:
            dim(msp, (co_dinh, a), (co_dinh, b), vi_tri, False)
    return gon


def dim_theo_truc(msp, truc, thiet_bi, vi_tri, ngang=True, co_dinh=None, gop=150):
    """Chuỗi dim kiểu bản mẫu cho sprinkler: trục lưới → thiết bị → … → trục lưới.

    `truc`: toạ độ các trục lưới (x nếu ngang); `thiet_bi`: toạ độ x (hoặc y) của các cột (hàng)
    thiết bị. Lấy từ trục gần nhất bên ngoài thiết bị đầu tiên tới trục gần nhất bên ngoài thiết bị
    cuối cùng, chèn mọi trục ở giữa. Đặt chuỗi ngoài nhà, giữa hàng dim trục kiến trúc và mép nhà.
    """
    tb = sorted(set(round(t, 3) for t in thiet_bi))
    if not tb:
        return []
    truc = sorted(truc)
    dau = max((t for t in truc if t <= tb[0]), default=tb[0])
    cuoi = min((t for t in truc if t >= tb[-1]), default=tb[-1])
    # trục nằm sát thiết bị (< gop mm) thì bỏ trục, giữ thiết bị: tránh dim vụn kiểu "51"
    ds = [t for t in truc if dau <= t <= cuoi and all(abs(t - x) >= gop for x in tb)] + tb
    return dim_chuoi(msp, ds, vi_tri if co_dinh is None else co_dinh, vi_tri, ngang, toi_thieu=gop)


def _tia(dg, p, huong):
    """Khoảng cách từ p theo hướng (dx, dy) đơn vị tới cạnh gần nhất của đa giác dg."""
    best = None
    for i in range(len(dg)):
        (x1, y1), (x2, y2) = dg[i], dg[(i + 1) % len(dg)]
        ex, ey = x2 - x1, y2 - y1
        den = huong[0] * ey - huong[1] * ex
        if abs(den) < 1e-12:
            continue
        t = ((x1 - p[0]) * ey - (y1 - p[1]) * ex) / den
        u = ((x1 - p[0]) * huong[1] - (y1 - p[1]) * huong[0]) / den
        if t > 1e-9 and -1e-9 <= u <= 1 + 1e-9 and (best is None or t < best):
            best = t
    return best


def _trong(dg, x, y):
    ben_trong = False
    for i in range(len(dg)):
        (x1, y1), (x2, y2) = dg[i], dg[(i + 1) % len(dg)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ben_trong = not ben_trong
    return ben_trong


def _nhin_thay(dg, p, q, so_diem=40):
    """Đoạn p→q nằm trong phòng (không cắt qua góc lõm của phòng chữ L/U)."""
    return all(_trong(dg, p[0] + (q[0] - p[0]) * k / so_diem, p[1] + (q[1] - p[1]) * k / so_diem)
               for k in range(1, so_diem))


def dim_toi_tuong(msp, p, dg, huong=("trai", "tren"), lech=0.0):
    """Dim vuông góc từ thiết bị tới tường theo các hướng chọn (trai/phai/tren/duoi).
    `lech`: dời đường dim song song khỏi tâm thiết bị (đơn vị bản vẽ; dim ngang dời lên, dim dọc dời phải)."""
    vec = {"trai": (-1, 0), "phai": (1, 0), "tren": (0, 1), "duoi": (0, -1)}
    for h in huong:
        v = vec[h]
        t = _tia(dg, p, v)
        if t:
            q = (p[0] + v[0] * t, p[1] + v[1] * t)
            ngang = v[1] == 0
            dim(msp, p, q, (p[1] if ngang else p[0]) + lech, ngang=ngang)


# Khoảng cách lớn nhất từ đầu báo tới góc phòng được phép ghi dim chéo (m), theo hình khoảng cách lớn
# nhất giữa các đầu báo trên bề mặt phẳng (TCVN 7568-1:2025, Hình 2 và Hình 7): khói 7,2 m, nhiệt 5,1 m.
DIM_GOC_MAX_M = {"bao_khoi": 7.2, "bao_nhiet": 5.1}

# Độ lệch đường dim khỏi tâm đầu báo (mm giấy). 0 = đường dim đi qua tâm như bản mẫu; đặt > 0 để đường dim
# nằm cạnh ký hiệu (chỉ còn đường gióng ngắn về tâm), chữ số không đè lên đầu báo.
LECH_DIM_DAU_BAO = 0.0


def _lech():
    return LECH_DIM_DAU_BAO * _s()


def dim_dau_bao(msp, p, dg, loai="bao_khoi", don_vi=1000.0):
    """Bộ dim cho một đầu báo, đúng kiểu bản mẫu:
    - hai dim vuông góc tới bức tường gần nhất theo phương ngang và phương dọc;
    - một dim chéo tới góc phòng: chỉ ghi khi khoảng cách ≤ DIM_GOC_MAX_M[loai] (khói 7,2 m,
      nhiệt 5,1 m). Chọn góc xa nhất trong giới hạn đó, ưu tiên góc phía đối diện hai dim vuông góc
      (chữ không chồng nhau). Không góc nào thoả thì không ghi dim chéo.
    `don_vi`: số đơn vị bản vẽ trong 1 m (1000 với bản vẽ mm).
    Trả về (chiều dài dim chéo đã ghi hoặc None, khoảng cách tới góc xa nhất) theo đơn vị bản vẽ."""
    vec = {"trai": (-1, 0), "phai": (1, 0), "tren": (0, 1), "duoi": (0, -1)}
    kc = {h: _tia(dg, p, v) for h, v in vec.items()}
    ngang = min(("trai", "phai"), key=lambda h: kc[h] if kc[h] else math.inf)
    doc_ = min(("tren", "duoi"), key=lambda h: kc[h] if kc[h] else math.inf)
    dim_toi_tuong(msp, p, dg, (ngang, doc_), _lech())
    sx = 1 if ngang == "trai" else -1      # góc ưu tiên nằm phía ngược lại
    sy = 1 if doc_ == "duoi" else -1
    thay = [v for v in dg if _nhin_thay(dg, p, v)] or dg
    xa_nhat = max(math.dist(v, p) for v in thay)
    gioi_han = DIM_GOC_MAX_M.get(loai, 7.2) * don_vi
    hop_le = [v for v in thay if math.dist(v, p) <= gioi_han + 1e-6]
    if not hop_le:
        return None, xa_nhat
    ung = [v for v in hop_le if (v[0] - p[0]) * sx >= 0 and (v[1] - p[1]) * sy >= 0] or hop_le
    q = max(ung, key=lambda v: math.dist(v, p))
    dim_thang(msp, p, q, _lech())
    return math.dist(p, q), xa_nhat


def dim_bao_chay_phong(msp, dg, dau_bao, don_vi=1000.0, lech_hang=300.0):
    """Ghi dim cho mọi đầu báo trong một phòng, theo bản mẫu.

    `dau_bao`: [(loai, (x, y))], loai là "bao_khoi" hoặc "bao_nhiet".
    - Hàng từ 3 đầu báo trở lên cùng tung độ (± lech_hang), hoặc phòng dạng hành lang (dài ≥ 3 lần
      rộng, > 30 m²): một chuỗi dim tường → đầu báo → … → tường dọc theo hàng; thêm một dim vuông góc
      từ đầu báo đầu hàng tới tường gần nhất và dim chéo tới góc ở hai đầu hàng (trong giới hạn
      DIM_GOC_MAX_M; hành lang thì không dim chéo).
    - Đầu báo còn lại: `dim_dau_bao` (2 vuông góc + 1 chéo trong giới hạn).
    Trả về danh sách (loai, điểm, khoảng cách góc xa nhất) để cảnh báo."""
    xs, ys = [v[0] for v in dg], [v[1] for v in dg]
    dai, rong = max(xs) - min(xs), max(ys) - min(ys)
    S = 0.0
    for i in range(len(dg)):
        S += dg[i][0] * dg[(i + 1) % len(dg)][1] - dg[(i + 1) % len(dg)][0] * dg[i][1]
    hanh_lang = abs(S) / 2 > 30 * don_vi ** 2 and max(dai, rong) > 3 * min(dai, rong)
    hang, le = [], list(dau_bao)
    if hanh_lang and len(dau_bao) >= 2:
        hang, le = [list(dau_bao)], []
    else:
        nhom = {}
        for d in dau_bao:
            k = next((k for k in nhom if abs(k - d[1][1]) <= lech_hang), d[1][1])
            nhom.setdefault(k, []).append(d)
        for k, ds in nhom.items():
            if len(ds) >= 3:
                hang.append(ds)
                le = [d for d in le if d not in ds]
    kq = []
    for ds in hang:
        ds.sort(key=lambda d: d[1][0])
        y = sum(d[1][1] for d in ds) / len(ds)
        dau, cuoi = ds[0][1], ds[-1][1]
        trai = dau[0] - (_tia(dg, dau, (-1, 0)) or 0)
        phai = cuoi[0] + (_tia(dg, cuoi, (1, 0)) or 0)
        dim_chuoi(msp, [trai, phai] + [d[1][0] for d in ds], y, y + _lech())
        len_, xuong = _tia(dg, dau, (0, 1)) or math.inf, _tia(dg, dau, (0, -1)) or math.inf
        dim_toi_tuong(msp, dau, dg, ("tren" if len_ <= xuong else "duoi",), _lech())
        for loai, p in ds:
            thay = [v for v in dg if _nhin_thay(dg, p, v)] or dg
            kq.append((loai, p, max(math.dist(v, p) for v in thay)))
        if not hanh_lang:
            for loai, p in (ds[0], ds[-1]):
                gh = DIM_GOC_MAX_M.get(loai, 7.2) * don_vi
                thay = [v for v in dg if _nhin_thay(dg, p, v) and math.dist(v, p) <= gh + 1e-6
                        and (v[0] - p[0]) * (1 if p is ds[-1][1] else -1) >= 0]
                if thay:
                    dim_thang(msp, p, max(thay, key=lambda v: math.dist(v, p)), _lech())
    for loai, p in le:
        _, xa = dim_dau_bao(msp, p, dg, loai, don_vi)
        kq.append((loai, p, xa))
    return kq


def dim_goc_xa(msp, p, dg):
    """Dim chéo từ đầu báo tới góc phòng xa nhất (cách bản mẫu chứng minh vùng bảo vệ).
    Trả về chiều dài để so với bán kính bảo vệ của đầu báo."""
    q = max([v for v in dg if _nhin_thay(dg, p, v)] or dg, key=lambda v: math.dist(v, p))
    dim_thang(msp, p, q)
    return math.dist(p, q)


def vong_phuc_vu(msp, tam, ban_kinh):
    """Vòng tròn nét đứt bán kính phục vụ của họng nước (chiều dài cuộn vòi), như bản mẫu."""
    return msp.add_circle(tam, ban_kinh, dxfattribs={"layer": LAYER_BAN_KINH[0]})


# ---------------- Chữ, ghi chú, bảng ----------------

def _chu(msp, s, p, cao_mm, can="MIDDLE_LEFT", ty_le=None, mau=None, kieu=None, layer=None):
    import ezdxf
    a = {"layer": layer or kh.LAYER_TEXT[0], "style": kieu or kh.KIEU_CHU}
    if mau is not None:
        a["color"] = mau
    t = msp.add_text(s, height=cao_mm * _s(ty_le), dxfattribs=a)
    t.set_placement(p, align=getattr(ezdxf.enums.TextEntityAlignment, can))
    return t


def _so_ky_tu(d, rong_mm, co):
    """Số ký tự tối đa một dòng: chữ in hoa Arial rộng ~0,72 cỡ chữ, chữ thường ~0,55."""
    hoa = sum(c.isupper() for c in d) > 0.6 * sum(c.isalpha() for c in d)
    return max(10, int(rong_mm / (co * (0.76 if hoa else 0.6))))


def tieu_de_to(msp, s, p, ty_le=None):
    """Tên hình vẽ đặt giữa, dưới mặt bằng, chữ Arial 5,35 mm, không ghi tỷ lệ (như bản mẫu)."""
    return _chu(msp, s, p, CO["tieu_de_to"], "MIDDLE_CENTER", ty_le)


def ghi_chu(msp, goc_tren_trai, dong, ty_le=None, tieu_de="GHI CHÚ:", co=None, rong_mm=190):
    """Khối ghi chú góc trên-trái tờ (chữ 3,7 mm, không khung)."""
    co = co or CO["ghi_chu_lon"]
    s = _s(ty_le)
    x, y = goc_tren_trai
    ds = ([tieu_de] if tieu_de else []) + [d2 for d in dong for d2 in kh._ngat_dong(d, _so_ky_tu(d, rong_mm, co))]
    for i, d in enumerate(ds):
        _chu(msp, d, (x, y - (i + 0.5) * co * 1.45 * s), co, ty_le=ty_le)
    return (x, y - len(ds) * co * 1.45 * s, x + rong_mm * s, y)


def hop_ghi_chu(msp, goc_duoi_trai, dong, rong_mm=110, ty_le=None, co=None, vien_mau=kh.DO):
    """Hộp ghi chú có khung (bản mẫu: khung đỏ mảnh, chữ 2,3 mm), đặt góc dưới-phải vùng vẽ.
    Trả về khung bao (x0, y0, x1, y1)."""
    co = co or CO["ghi_chu_hop"]
    s = _s(ty_le)
    ds = [d2 for d in dong for d2 in kh._ngat_dong(d, _so_ky_tu(d, rong_mm - 4, co))]
    cao = (len(ds) * co * 1.45 + 4) * s
    x0, y0 = goc_duoi_trai
    msp.add_lwpolyline([(x0, y0), (x0 + rong_mm * s, y0), (x0 + rong_mm * s, y0 + cao), (x0, y0 + cao)],
                       close=True, dxfattribs={"layer": kh.LAYER_TEXT[0], "color": vien_mau})
    for i, d in enumerate(ds):
        _chu(msp, d, (x0 + 2 * s, y0 + cao - (2 + (i + 0.5) * co * 1.45) * s), co, ty_le=ty_le)
    return (x0, y0, x0 + rong_mm * s, y0 + cao)


def bang(msp, goc_tren_trai, rong_cot_mm, hang, ty_le=None, cao_hang_mm=7.0, co=None, tieu_de=None,
         can_giua=True, mau_vien=None, kieu=None):
    """Bảng kẻ ô tổng quát. `hang`: list các hàng, mỗi hàng list chuỗi (dùng "\\n" để xuống dòng trong ô).
    Trả về khung bao."""
    co = co or CO["bang"]
    kieu = kieu or kh.KIEU_CHU  # Arial Narrow trên Windows thiếu dấu tiếng Việt: chỉ dùng cho chữ số dim
    s = _s(ty_le)
    x0, y0 = goc_tren_trai
    rong = sum(rong_cot_mm) * s
    a = {"layer": kh.LAYER_TEXT[0]}
    if mau_vien is not None:
        a["color"] = mau_vien
    y = y0
    if tieu_de:
        h = cao_hang_mm * 1.3 * s
        msp.add_lwpolyline([(x0, y), (x0 + rong, y), (x0 + rong, y - h), (x0, y - h)], close=True, dxfattribs=a)
        _chu(msp, tieu_de, (x0 + 2 * s, y - h / 2), CO["tieu_de_bang"], ty_le=ty_le)
        y -= h
    for r in hang:
        so_dong = max(len(str(c).split("\n")) for c in r)
        h = max(cao_hang_mm, so_dong * co * 1.5 + 2) * s
        x = x0
        for w, c in zip(rong_cot_mm, r):
            msp.add_lwpolyline([(x, y), (x + w * s, y), (x + w * s, y - h), (x, y - h)], close=True, dxfattribs=a)
            ds = str(c).split("\n")
            for j, d in enumerate(ds):
                yy = y - h / 2 + (len(ds) / 2 - j - 0.5) * co * 1.5 * s
                if can_giua:
                    _chu(msp, d, (x + w * s / 2, yy), co, "MIDDLE_CENTER", ty_le, kieu=kieu)
                else:
                    _chu(msp, d, (x + 1.5 * s, yy), co, ty_le=ty_le, kieu=kieu)
            x += w * s
        y -= h
    return (x0, y, x0 + rong, y0)


def tinh_binh(dien_tich, s_1_binh, du_phong=0.10):
    """Số bình theo diện tích: n = S / S1 (làm tròn lên), dự phòng 10 % (làm tròn lên)."""
    n = math.ceil(dien_tich / s_1_binh - 1e-9)
    dp = math.ceil(n * du_phong - 1e-9)
    return {"tinh_toan": n, "du_phong": dp, "tong": n + dp}


def bang_binh(msp, goc_tren_trai, tang, ty_le=None, s_1_binh=100, muc_nguy_hiem="CAO",
              loai=("BÌNH CHỮA CHÁY ABC 8KG", "BÌNH CHỮA CHÁY CO2 5kg")):
    """Bảng "BỐ TRÍ VÀ CÔNG SUẤT BÌNH CHỮA CHÁY VỚI MỐI NGUY HIỂM LOẠI A THEO TCVN 7435-1:2004".
    `tang`: [(tên tầng, diện tích m², số bình thiết kế)]. Kết quả ĐẠT khi số thiết kế ≥ tổng tính toán.
    s_1_binh, muc_nguy_hiem: tra TCVN 7435-1 — kỹ sư chốt (bản mẫu dùng 100 m², mức CAO)."""
    cot = [8, 46, 16, 26, 22, 22, 16, 20, 16, 12]  # tổng ~204 mm như bản mẫu
    hang = [["STT", "BÌNH CHỮA CHÁY", "MỨC NGUY\nHIỂM", "DIỆN TÍCH BẢO VỆ LỚN\nNHẤT CỦA 1 BÌNH\nCHỮA CHÁY, M²",
             "DIỆN TÍCH SÀN\n(M2)", "SỐ LƯỢNG BÌNH\nTÍNH TOÁN", "DỰ PHÒNG\n(10%)", "TỔNG SỐ LƯỢNG\nTÍNH TOÁN",
             "SỐ BÌNH\nTHIẾT KẾ", "KẾT QUẢ"]]
    for i, (ten, S, tk) in enumerate(tang, 1):
        k = tinh_binh(S, s_1_binh)
        hang.append([f"{i:02d}", "\n".join(f": {l}" for l in loai), muc_nguy_hiem, str(s_1_binh),
                     f"{ten}: {S:g}m²", f"={S:g}/{s_1_binh}~{k['tinh_toan']}", f"{k['du_phong']:02d}",
                     f"{k['tong']:02d}", f"{tk:02d}", "ĐẠT" if tk >= k["tong"] else "CHƯA ĐẠT"])
    return bang(msp, goc_tren_trai, cot, hang, ty_le, cao_hang_mm=9, co=1.9, tieu_de=(
        "BỐ TRÍ VÀ CÔNG SUẤT BÌNH CHỮA CHÁY VỚI MỐI NGUY HIỂM LOẠI A THEO TCVN 7435-1:2004"))


def bang_quy_mo(msp, goc_tren_trai, tang, ty_le=None):
    """Bảng "KHỐI TÍCH CÔNG TRÌNH": [(tên tầng, công năng, S m², h m)]. Tự đánh STT và cộng tổng
    (bản mẫu từng ghi sai tổng chiều cao và khối tích vì cộng tay)."""
    hang = [["STT", "SỐ TẦNG", "CÔNG NĂNG", "DIỆN TÍCH (m2)\nS", "CHIỀU CAO (m)\nH", "KHỐI TÍCH (m3)\nS*H"]]
    tS = tH = tV = 0.0
    for i, (ten, cn, S, h) in enumerate(tang, 1):
        hang.append([str(i), ten, cn, f"{S:g}", f"{h:g}", f"{S * h:,.0f}"])
        tS, tH, tV = tS + S, tH + h, tV + S * h
    hang.append(["", "Tổng", "", f"{tS:g}", f"{tH:.1f}", f"{tV:,.0f}"])
    return bang(msp, goc_tren_trai, [10, 30, 50, 27, 25, 28], hang, ty_le, tieu_de="KHỐI TÍCH CÔNG TRÌNH",
                mau_vien=kh.DO), {"dien_tich": tS, "chieu_cao": tH, "khoi_tich": tV}


# ---------------- Khung tên ----------------

def khung_a3(msp, goc, ty_le=None, tt=None):
    """Khung A3 ngang + cột thông tin bên phải như bản mẫu. `goc`: góc dưới-trái tờ giấy (model).

    tt (dict, đều tuỳ chọn): phat_hanh ("Thiết kế sơ bộ"), cong_ty (list dòng), dia_chi_cty, mst,
    giam_doc, chu_tri, thiet_ke, du_an, dia_chi, ngay ("..../10/2026"), so_to ("PCCC-01").
    Trả về vùng vẽ (x0, y0, x1, y1) bên trái cột thông tin.
    """
    tt = tt or {}
    s = _s(ty_le)
    gx, gy = goc
    L = {"layer": LAYER_KHUNG[0]}

    def hcn(x0, y0, x1, y1, day=None):
        p = msp.add_lwpolyline([(gx + x0 * s, gy + y0 * s), (gx + x1 * s, gy + y0 * s), (gx + x1 * s, gy + y1 * s),
                                (gx + x0 * s, gy + y1 * s)], close=True, dxfattribs=L)
        if day:
            p.dxf.lineweight = day

    def chu(st, x, y, co, can="MIDDLE_LEFT", dam=False):
        _chu(msp, st, (gx + x * s, gy + y * s), co, can, ty_le, layer=LAYER_KHUNG[0],
             kieu=kh.KIEU_CHU + "_B" if dam else None)

    W, H = A3
    hcn(0, 0, W, H)                                   # mép giấy
    x0, y0, x1, y1 = LE[0], LE[1], W - LE[0], H - LE[1]
    hcn(x0, y0, x1, y1, 50)                           # khung 0,5 mm
    xc = x1 - RONG_COT_TEN
    msp.add_line((gx + xc * s, gy + y0 * s), (gx + xc * s, gy + y1 * s), dxfattribs={**L, "lineweight": 50})
    y = y1
    for cao, o in O_COT_TEN:
        yd = y - cao
        msp.add_line((gx + xc * s, gy + yd * s), (gx + x1 * s, gy + yd * s), dxfattribs=L)
        m = xc + 1.5
        if o == "phat_hanh":
            chu("MỤC ĐÍCH PHÁT HÀNH / ISSUED FOR", x1 - 1, y - 2, 1.6, "MIDDLE_RIGHT")
            muc = ["Tham khảo", "Thiết kế sơ bộ", "Trình duyệt", "Đấu thầu", "Thi công", "Hoàn công"]
            for i, mm in enumerate(muc):
                yy = y - 6 - i * 3.3
                chu(mm, m + 2, yy, 1.7)
                hcn(xc + 22, yy - 0.8, xc + 23.6, yy + 0.8)
                if mm == tt.get("phat_hanh", "Thiết kế sơ bộ"):
                    chu("X", xc + 22.8, yy, 1.5, "MIDDLE_CENTER")
        elif o == "chu_dau_tu":
            chu("CHẤP THUẬN CỦA CHỦ ĐẦU TƯ", m, y - 2.5, 1.7, dam=True)
            chu("APPROVAL OF THE OWNER", m, y - 5, 1.4)
        elif o == "don_vi":
            chu("ĐƠN VỊ THIẾT KẾ:", m, y - 2.5, 2.0, dam=True)
            hcn(xc + 13, y - 24, xc + 29, y - 6)       # chỗ đặt logo
            for i, d in enumerate(tt.get("cong_ty", ["TÊN CÔNG TY"])):
                chu(d, xc + RONG_COT_TEN / 2, y - 27 - i * 2.6, 1.9, "MIDDLE_CENTER", dam=True)
            chu(tt.get("dia_chi_cty", "AD: ..."), m, y - 38, 1.3, dam=True)
            chu("MST: " + tt.get("mst", "..."), m, y - 40.5, 1.3, dam=True)
        elif o in ("giam_doc", "chu_tri", "thiet_ke"):
            nhan = {"giam_doc": "Giám Đốc - Director", "chu_tri": "CHỦ TRÌ THIẾT KẾ", "thiet_ke": "THIẾT KẾ"}[o]
            chu(nhan, xc + RONG_COT_TEN / 2, y - 2.5, 2.4, "MIDDLE_CENTER")
            chu(tt.get(o, ""), xc + RONG_COT_TEN / 2, yd + 2.5, 2.4, "MIDDLE_CENTER")
        elif o == "du_an":
            chu("DỰ ÁN:", m, y - 2.5, 2.4)
            for i, d in enumerate(kh._ngat_dong(tt.get("du_an", ""), 26)):
                chu(d, m + 3, y - 6.5 - i * 2.6, 2.0)
            for i, d in enumerate(kh._ngat_dong("Đ/c: " + tt.get("dia_chi", ""), 32)):
                chu(d, m + 2, y - 13 - i * 2.2, 1.8)
        elif o == "ngay":
            chu("Com.date: " + tt.get("ngay", "....../..../...."), m, y - 2, 1.3)
            chu("Ký hiệu: " + tt.get("so_to", ""), xc + 25, y - 2, 1.3)
        elif o == "sua_doi":
            for xx in (6, 10, 33):
                msp.add_line((gx + (xc + xx) * s, gy + y * s), (gx + (xc + xx) * s, gy + yd * s), dxfattribs=L)
            chu("No.", m - 0.5, y - 1.8, 1.4)
            chu("Mark", xc + 6.3, y - 1.8, 1.4)
            chu("Revision note", xc + 10.5, y - 1.8, 1.4)
            chu("Date", xc + 34, y - 1.8, 1.4)
            msp.add_line((gx + xc * s, gy + (y - 3.5) * s), (gx + x1 * s, gy + (y - 3.5) * s), dxfattribs=L)
        elif o == "so_to":
            chu(tt.get("so_to", ""), xc + RONG_COT_TEN / 2, y - cao / 2, 4.0, "MIDDLE_CENTER", dam=True)
        y = yd
    return (gx + x0 * s, gy + y0 * s, gx + xc * s, gy + y1 * s)


def to_bia_hang_muc(msp, goc, ten_hang_muc, ty_le=None):
    """Tờ phân cách hạng mục: khung A3, giữa tờ "HẠNG MỤC:" và tên hệ thống (bản mẫu tờ 4, 13, 24, 31)."""
    s = _s(ty_le)
    gx, gy = goc
    msp.add_lwpolyline([(gx, gy), (gx + A3[0] * s, gy), (gx + A3[0] * s, gy + A3[1] * s), (gx, gy + A3[1] * s)],
                       close=True, dxfattribs={"layer": LAYER_KHUNG[0]})
    msp.add_lwpolyline([(gx + LE[0] * s, gy + LE[1] * s), (gx + (A3[0] - LE[0]) * s, gy + LE[1] * s),
                        (gx + (A3[0] - LE[0]) * s, gy + (A3[1] - LE[1]) * s), (gx + LE[0] * s, gy + (A3[1] - LE[1]) * s)],
                       close=True, dxfattribs={"layer": LAYER_KHUNG[0], "lineweight": 70})
    _chu(msp, "HẠNG MỤC:", (gx + A3[0] / 2 * s, gy + 195 * s), 7, "MIDDLE_CENTER", ty_le)
    _chu(msp, ten_hang_muc, (gx + A3[0] / 2 * s, gy + 175 * s), 7, "MIDDLE_CENTER", ty_le)
