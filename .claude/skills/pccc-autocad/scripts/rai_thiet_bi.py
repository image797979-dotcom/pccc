"""Rải tự động sprinkler / đầu báo khói / đầu báo nhiệt trong các phòng.

Phòng là các polyline KÍN trên một layer (mặc định PCCC-PHONG). Thông số lấy từ thong_so.json.

Ví dụ:
  # Làm trên file DXF (không cần AutoCAD), ghi ra file mới
  python rai_thiet_bi.py --dxf mat_bang.dxf --loai sprinkler --nhom 2 --ra mat_bang_spr.dxf

  # Làm trực tiếp trên bản vẽ đang mở trong AutoCAD
  python rai_thiet_bi.py --com --loai bao_khoi --tran 3.2

  # Chỉ tính, không vẽ (in toạ độ + kiểm tra)
  python rai_thiet_bi.py --dxf mat_bang.dxf --loai bao_nhiet --tran 4 --chi-tinh

Giả thiết: đơn vị bản vẽ là mm (đổi bằng --don-vi m). Cạnh cong (bulge) của polyline bị bỏ qua.
"""
import argparse
import json
import math
import sys
from pathlib import Path

THU_MUC = Path(__file__).resolve().parent
LAYER_DIM = "PCCC-DIM"
DIMSTYLE = "PCCC"


# ---------- Thông số ----------

def doc_thong_so(loai, nhom=None, tran=None):
    """Trả về dict: khoang_cach_max, cach_tuong_max, dien_tich_max, khoang_cach_min (mét)."""
    ts = json.loads((THU_MUC / "thong_so.json").read_text(encoding="utf-8"))
    if loai == "sprinkler":
        if nhom not in ts["sprinkler"]["nhom"]:
            sys.exit(f"Nhóm '{nhom}' chưa có trong thong_so.json. Có: {list(ts['sprinkler']['nhom'])}")
        n = ts["sprinkler"]["nhom"][nhom]
        return {
            "khoang_cach_max": n["khoang_cach_max_m"],
            "cach_tuong_max": n["khoang_cach_max_m"] * ts["sprinkler"]["ty_le_cach_tuong_max"],
            "dien_tich_max": n["dien_tich_max_moi_dau_m2"],
            "khoang_cach_min": ts["sprinkler"]["khoang_cach_min_m"],
            "cach_tuong_min": ts["sprinkler"].get("cach_tuong_min_m", 0.0),
            "nguon": f"{ts['sprinkler']['_nguon']}, nhóm {nhom}",
        }
    if tran is None:
        sys.exit("Đầu báo cần --tran (chiều cao trần, m).")
    for dong in ts[loai]["theo_chieu_cao"]:
        if tran <= dong["tran_den_m"]:
            return {
                "khoang_cach_max": dong["khoang_cach_max_m"],
                "cach_tuong_max": dong["cach_tuong_max_m"],
                "dien_tich_max": dong["dien_tich_max_m2"],
                "khoang_cach_min": 0.0,
                "cach_tuong_min": 0.0,
                "nguon": f"{ts[loai]['_nguon']}, trần ≤ {dong['tran_den_m']} m",
            }
    sys.exit(f"Trần {tran} m vượt bảng {loai} trong thong_so.json; tra tiêu chuẩn cho trần cao.")


# ---------- Hình học ----------

def trong_da_giac(x, y, dg):
    """Ray casting: điểm (x, y) có nằm trong đa giác dg không."""
    trong = False
    n = len(dg)
    for i in range(n):
        x1, y1 = dg[i]
        x2, y2 = dg[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            trong = not trong
    return trong


def so_hang(L, buoc_max, tuong_max):
    """Số hàng thiết bị trên chiều dài L để bước ≤ buoc_max và khoảng cách tới tường ≤ tuong_max."""
    return max(1, math.ceil(L / buoc_max - 1e-9), math.ceil(L / (2 * tuong_max) - 1e-9))


def khoang_cach_tuong(x, y, dg):
    """Khoảng cách ngắn nhất từ điểm tới các cạnh phòng."""
    tot = math.inf
    for i in range(len(dg)):
        (x1, y1), (x2, y2) = dg[i], dg[(i + 1) % len(dg)]
        dx, dy = x2 - x1, y2 - y1
        t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        tot = min(tot, math.hypot(x - x1 - t * dx, y - y1 - t * dy))
    return tot


def la_truc_giao(dg, sai_so=1e-6):
    """Mọi cạnh phòng đều song song trục X hoặc Y (phòng chữ nhật, chữ L, U, T...)."""
    return all(abs(dg[i][0] - dg[i - 1][0]) < sai_so or abs(dg[i][1] - dg[i - 1][1]) < sai_so
               for i in range(len(dg)))


def _chia_theo_x(dg):
    """Cắt phòng trực giao thành các dải dọc tại hoành độ các đỉnh, gộp các dải liền nhau
    có cùng khoảng y. Trả về [(x0, y0, x1, y1), ...]."""
    xs = sorted({round(p[0], 6) for p in dg})
    mo, truoc, hcn = {}, set(), []
    for xa, xb in zip(xs, xs[1:]):
        ys = sorted(round(v, 6) for v in _giao_doc(dg, (xa + xb) / 2))
        hien = set(zip(ys[0::2], ys[1::2]))
        for kh in truoc - hien:
            hcn.append((mo.pop(kh), kh[0], xa, kh[1]))
        for kh in hien - truoc:
            mo[kh] = xa
        truoc = hien
    hcn += [(mo[kh], kh[0], xs[-1], kh[1]) for kh in truoc]
    return hcn


def chia_hinh_chu_nhat(dg):
    """Chia phòng trực giao thành ít hình chữ nhật nhất (thử cắt dọc và cắt ngang, lấy cách
    cho ít mảnh hơn; bằng nhau thì lấy cách có cạnh ngắn nhất lớn hơn)."""
    doc = _chia_theo_x(dg)
    ngang = [(y0, x0, y1, x1) for x0, y0, x1, y1 in _chia_theo_x([(y, x) for x, y in dg])]
    canh_min = lambda ds: min(min(x1 - x0, y1 - y0) for x0, y0, x1, y1 in ds)
    return min([doc, ngang], key=lambda ds: (len(ds), -canh_min(ds)))


def luoi_hcn(hcn, tso):
    """Lưới đối xứng đều trong một hình chữ nhật: bước bằng nhau, hàng ngoài cùng cách cạnh
    đúng nửa bước, nên cả lưới đối xứng qua tâm hình chữ nhật.

    Đơn vị: mét. Trả về (danh sách điểm, bước x, bước y).
    """
    x0, y0, x1, y1 = hcn
    Lx, Ly = x1 - x0, y1 - y0
    nx = so_hang(Lx, tso["khoang_cach_max"], tso["cach_tuong_max"])
    ny = so_hang(Ly, tso["khoang_cach_max"], tso["cach_tuong_max"])
    # Diện tích bảo vệ mỗi thiết bị không vượt giới hạn: tăng số hàng ở phía có bước lớn hơn
    while (Lx / nx) * (Ly / ny) > tso["dien_tich_max"] + 1e-9:
        if Lx / nx >= Ly / ny:
            nx += 1
        else:
            ny += 1
    sx, sy = Lx / nx, Ly / ny
    diem = [(x0 + sx * (i + 0.5), y0 + sy * (j + 0.5)) for i in range(nx) for j in range(ny)]
    return diem, sx, sy


def rai_luoi(dg, tso):
    """Phòng có tường xiên: lưới đối xứng trên hình bao, giữ các điểm nằm trong phòng."""
    xs, ys = [p[0] for p in dg], [p[1] for p in dg]
    diem, sx, sy = luoi_hcn((min(xs), min(ys), max(xs), max(ys)), tso)
    return [p for p in diem if trong_da_giac(*p, dg)], sx, sy


def bo_sung_vung_trong(dg, diem, sx, sy, cach_tuong_min=0.0, buoc_mau=0.25):
    """Phòng không chữ nhật (chữ L, chữ U...) có thể còn vùng chưa phủ.

    Lấy mẫu dày trong phòng; điểm nào xa thiết bị gần nhất hơn nửa đường chéo ô lưới
    thì đặt thêm thiết bị ở điểm xa nhất, lặp tới khi phủ hết. Trả về danh sách điểm bổ sung.
    """
    r_max = math.hypot(sx / 2, sy / 2) + 1e-6
    xs, ys = [p[0] for p in dg], [p[1] for p in dg]
    mau = [
        (x, y)
        for x in _day(min(xs), max(xs), buoc_mau)
        for y in _day(min(ys), max(ys), buoc_mau)
        if trong_da_giac(x, y, dg) and khoang_cach_tuong(x, y, dg) >= cach_tuong_min
    ]
    # Khoảng cách từ mỗi điểm mẫu tới thiết bị gần nhất, cập nhật dần khi thêm thiết bị
    d_min = [min((math.dist(m, p) for p in diem), default=math.inf) for m in mau]
    them = []
    while mau:
        k = max(range(len(mau)), key=d_min.__getitem__)
        if d_min[k] <= r_max:
            return them
        moi = mau[k]
        them.append(moi)
        d_min = [min(d, math.dist(m, moi)) for d, m in zip(d_min, mau)]
    return them


def _day(a, b, buoc):
    n = max(1, int((b - a) / buoc))
    return [a + (k + 0.5) * (b - a) / n for k in range(n)]


def dien_tich(dg):
    return abs(sum(dg[i][0] * dg[(i + 1) % len(dg)][1] - dg[(i + 1) % len(dg)][0] * dg[i][1]
                   for i in range(len(dg)))) / 2


def tinh_phong(dg_m, tso):
    """Tính toàn bộ cho một phòng (toạ độ mét). Trả về dict kết quả + cảnh báo."""
    canh_bao = []
    if la_truc_giao(dg_m):
        # Phòng chữ nhật / chữ L / U...: chia thành hình chữ nhật, mỗi mảnh rải lưới đối xứng
        manh = chia_hinh_chu_nhat(dg_m)
        # Dải hẹp (lối vào phòng, khe cạnh cột) không đủ chỗ giữ khoảng cách tối thiểu tới tường:
        # chỉ rải khi các thiết bị ở mảnh rộng xung quanh không phủ tới.
        rong_min = max(2 * tso["cach_tuong_min"], 1e-9)
        rong = [h for h in manh if min(h[2] - h[0], h[3] - h[1]) >= rong_min] or manh
        hep = [h for h in manh if h not in rong]
        luoi = [luoi_hcn(h, tso) for h in rong]
        manh_dung = list(rong)  # hình chữ nhật tương ứng từng lưới (để dim trong phạm vi mảnh)
        r_phu = math.hypot(tso["khoang_cach_max"] / 2, tso["khoang_cach_max"] / 2)
        da_co = [p for d, _, _ in luoi for p in d]
        for h in hep:
            goc = [(h[0], h[1]), (h[2], h[1]), (h[2], h[3]), (h[0], h[3]), ((h[0] + h[2]) / 2, (h[1] + h[3]) / 2)]
            if any(min((math.dist(g, p) for p in da_co), default=math.inf) > r_phu for g in goc):
                luoi.append(luoi_hcn(h, tso))
                manh_dung.append(h)
                da_co += luoi[-1][0]
        if len(rong) == len(manh) and min(min(h[2] - h[0], h[3] - h[1]) for h in manh) < rong_min \
                and dien_tich(dg_m) <= tso["dien_tich_max"]:
            # Phòng nhỏ toàn dải hẹp (WC, hốc kỹ thuật): thử 1 thiết bị ở điểm xa tường nhất
            xs, ys = [p[0] for p in dg_m], [p[1] for p in dg_m]
            mau = [(x, y) for x in _day(min(xs), max(xs), 0.05) for y in _day(min(ys), max(ys), 0.05)
                   if trong_da_giac(x, y, dg_m)]
            if mau:
                tot = max(mau, key=lambda m: khoang_cach_tuong(*m, dg_m))
                if all(math.dist(m, tot) <= r_phu for m in mau):
                    luoi = [([tot], max(xs) - min(xs), max(ys) - min(ys))]
                    manh_dung = [None]  # dim tới tường thật
        nhom = [d for d, _, _ in luoi]
        diem = [p for d in nhom for p in d]
        sx = max(s for _, s, _ in luoi)
        sy = max(s for _, _, s in luoi)
        them = []
        if len(luoi) > 1:
            canh_bao.append(f"Phòng được chia thành {len(luoi)} hình chữ nhật, mỗi phần rải đối xứng riêng.")
        if hep and len(luoi) == len(rong):
            canh_bao.append(f"Bỏ qua {len(hep)} dải hẹp < {rong_min:.1f} m vì đã được thiết bị bên cạnh phủ tới.")
    else:
        diem, sx, sy = rai_luoi(dg_m, tso)
        nhom = [diem]
        manh_dung = [None]
        them = bo_sung_vung_trong(dg_m, diem, sx, sy, tso["cach_tuong_min"])
        canh_bao.append("Phòng có tường xiên: lưới theo hình bao, không đối xứng hoàn toàn, nên kiểm tra lại bằng mắt."
                        + (f" Đã bổ sung {len(them)} thiết bị cho vùng chưa phủ." if them else ""))
    tat_ca = diem + them
    if tso["cach_tuong_min"] > 0:
        for x, y in tat_ca:
            if khoang_cach_tuong(x, y, dg_m) < tso["cach_tuong_min"] - 1e-6:
                canh_bao.append(f"Thiết bị tại ({x:.2f}, {y:.2f}) cách tường < {tso['cach_tuong_min']} m.")
    if tso["khoang_cach_min"] > 0:
        for i in range(len(tat_ca)):
            for j in range(i + 1, len(tat_ca)):
                if math.dist(tat_ca[i], tat_ca[j]) < tso["khoang_cach_min"] - 1e-6:
                    canh_bao.append(f"Hai thiết bị cách nhau < {tso['khoang_cach_min']} m tại "
                                    f"({tat_ca[i][0]:.2f}, {tat_ca[i][1]:.2f}).")
    return {"diem": tat_ca, "buoc_x": sx, "buoc_y": sy, "dien_tich": dien_tich(dg_m), "canh_bao": canh_bao,
            "da_giac": dg_m,
            "dim": tinh_dim(dg_m, nhom, tat_ca, them, manh_dung)}


# ---------- Kích thước (dim) ----------

def _giao_ngang(dg, y):
    """Hoành độ các giao điểm của đường y = const với cạnh phòng."""
    xs = []
    for i in range(len(dg)):
        (x1, y1), (x2, y2) = dg[i], dg[(i + 1) % len(dg)]
        if (y1 > y) != (y2 > y):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return xs


def _giao_doc(dg, x):
    """Tung độ các giao điểm của đường x = const với cạnh phòng."""
    return _giao_ngang([(b, a) for a, b in dg], x)


def _chuoi(toa_do, co_dinh, ngang):
    """Chuỗi dim nối tiếp qua các toạ độ đã sắp xếp; trả về [(p1, p2), ...]."""
    if ngang:
        return [((a, co_dinh), (b, co_dinh)) for a, b in zip(toa_do, toa_do[1:])]
    return [((co_dinh, a), (co_dinh, b)) for a, b in zip(toa_do, toa_do[1:])]


def _chuoi_qua(dg, tat_ca, co_dinh, nhom_toa_do, ngang, gioi_han=None):
    """Chuỗi dim tường → thiết bị → ... → tường trên đường ngang y = co_dinh (hoặc dọc x = co_dinh).

    Lấy mọi thiết bị của phòng nằm trên đường đó, giới hạn trong đoạn tường bao quanh
    nhom_toa_do. Nếu cho gioi_han (lo, hi) = mép mảnh chữ nhật, chuỗi không vượt quá mép mảnh,
    để chuỗi dim của phòng chữ L/U không kéo dài xuyên qua mảnh khác.
    """
    tuong = sorted(_giao_ngang(dg, co_dinh) if ngang else _giao_doc(dg, co_dinh))
    dau, cuoi = min(nhom_toa_do), max(nhom_toa_do)
    a = max((t for t in tuong if t < dau), default=None)
    b = min((t for t in tuong if t > cuoi), default=None)
    if gioi_han:
        lo, hi = gioi_han
        a = lo if a is None or a < lo - 1e-6 else a
        b = hi if b is None or b > hi + 1e-6 else b
    tren_duong = sorted({round(p[0] if ngang else p[1], 6) for p in tat_ca
                         if abs((p[1] if ngang else p[0]) - co_dinh) < 1e-6
                         and (a is None or p[0 if ngang else 1] > a) and (b is None or p[0 if ngang else 1] < b)})
    return _chuoi([t for t in [a, *tren_duong, b] if t is not None], co_dinh, ngang)


def tinh_dim(dg, nhom, tat_ca, them, manh=None):
    """Các đoạn cần ghi kích thước (toạ độ mét), đủ để định vị mọi thiết bị:

    - Mỗi lưới đối xứng (mỗi mảnh chữ nhật): một chuỗi ngang qua hàng gần tâm nhất và một
      chuỗi dọc qua cột gần tâm nhất, đi từ tường (hoặc mép mảnh) → thiết bị → ... → tường.
    - Thiết bị bổ sung (không theo lưới): dim tới tường gần nhất theo cả hai phương.
    """
    doan = []
    manh = manh or [None] * len(nhom)
    for luoi, h in zip(nhom, manh):
        if not luoi:
            continue
        cx = sum(p[0] for p in luoi) / len(luoi)
        cy = sum(p[1] for p in luoi) / len(luoi)
        y0 = min({p[1] for p in luoi}, key=lambda y: (abs(y - cy), y))
        x0 = min({p[0] for p in luoi}, key=lambda x: (abs(x - cx), x))
        doan += _chuoi_qua(dg, tat_ca, y0, [p[0] for p in luoi if p[1] == y0], ngang=True,
                           gioi_han=(h[0], h[2]) if h else None)
        doan += _chuoi_qua(dg, tat_ca, x0, [p[1] for p in luoi if p[0] == x0], ngang=False,
                           gioi_han=(h[1], h[3]) if h else None)

    for x, y in them:
        tx = min(_giao_ngang(dg, y), key=lambda t: abs(t - x), default=None)
        ty = min(_giao_doc(dg, x), key=lambda t: abs(t - y), default=None)
        if tx is not None:
            doan.append(((tx, y), (x, y)))
        if ty is not None:
            doan.append(((x, ty), (x, y)))
    # Bỏ đoạn trùng (hai mảnh có thể sinh cùng một chuỗi)
    duy_nhat = {}
    for p1, p2 in doan:
        if math.dist(p1, p2) > 1e-6:
            duy_nhat.setdefault(tuple(round(v, 6) for v in (*p1, *p2)), (p1, p2))
    return list(duy_nhat.values())


# ---------- Vẽ ----------

def chay_dxf(args, tso, kh, he_so):
    import ezdxf

    doc = ezdxf.readfile(args.dxf)
    msp = doc.modelspace()
    phong = [
        (e.dxf.handle, [(x, y) for x, y in e.get_points("xy")])
        for e in msp.query(f'LWPOLYLINE[layer=="{args.layer_phong}"]') if e.closed
    ]
    ket_qua = xu_ly(phong, tso, he_so)
    if not args.chi_tinh:
        import ky_hieu as KH
        import trinh_bay as TB
        KH.DON_VI_MM = he_so == 1000
        TB.dam_bao(doc, args.ty_le)  # ký hiệu + dim style theo hồ sơ mẫu
        for kq in ket_qua:
            for x, y in kq["diem"]:
                KH.chen(msp, args.loai, (x * he_so, y * he_so))
        if not args.khong_dim:
            for kq in ket_qua:
                if args.loai == "sprinkler":
                    # chuỗi tường → đầu phun → … → tường (trên tờ tổng: thay bằng TB.dim_theo_truc)
                    for (x1, y1), (x2, y2) in kq["dim"]:
                        TB.dim(msp, (x1 * he_so, y1 * he_so), (x2 * he_so, y2 * he_so), ngang=y1 == y2)
                else:
                    # kiểu bản mẫu: 2 dim vuông góc tới tường gần + 1 dim chéo tới góc xa nhất
                    dg = [(x * he_so, y * he_so) for x, y in kq["da_giac"]]
                    gh = TB.DIM_GOC_MAX_M[args.loai]
                    for _, (x, y), xa in TB.dim_bao_chay_phong(
                            msp, dg, [(args.loai, (x * he_so, y * he_so)) for x, y in kq["diem"]], he_so):
                        x, y = x / he_so, y / he_so
                        if xa / he_so > gh + 1e-6:
                            kq["canh_bao"].append(f"Đầu báo ({x:.2f}, {y:.2f}) cách góc xa nhất {xa / he_so:.2f} m "
                                                  f"> {gh} m — kiểm tra vùng bảo vệ (dim chéo chỉ ghi tới góc ≤ {gh} m).")
        doc.saveas(args.ra or args.dxf.replace(".dxf", "_pccc.dxf"))
    return ket_qua


def chay_com(args, tso, kh, he_so):
    import acad_com as ac

    acad = ac.ket_noi()
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    phong = ac.polyline_kin_tren_layer(doc, args.layer_phong)
    ket_qua = xu_ly(phong, tso, he_so)
    if not args.chi_tinh:
        ac.dam_bao_layer(doc, kh["layer"], kh["mau"])
        ac.dam_bao_block_tron(doc, kh["block"], kh["ban_kinh_mm"] / 1000 * he_so, kh["chu"])
        ms = ac.goi_lai(lambda: doc.ModelSpace)
        for kq in ket_qua:
            for x, y in kq["diem"]:
                br = ac.goi_lai(lambda: ms.InsertBlock(ac.diem(x * he_so, y * he_so), kh["block"], 1, 1, 1, 0))
                ac.goi_lai(lambda: setattr(br, "Layer", kh["layer"]))
        if not args.khong_dim:
            ac.dam_bao_layer(doc, LAYER_DIM, 7)
            ac.dam_bao_dimstyle(doc, DIMSTYLE, args.ty_le / 1000 * he_so, 0 if he_so == 1000 else 2)
            for kq in ket_qua:
                for (x1, y1), (x2, y2) in kq["dim"]:
                    p1, p2 = ac.diem(x1 * he_so, y1 * he_so), ac.diem(x2 * he_so, y2 * he_so)
                    goc = 0.0 if y1 == y2 else math.pi / 2
                    d = ac.goi_lai(lambda: ms.AddDimRotated(p1, p2, p1, goc))
                    ac.goi_lai(lambda: setattr(d, "Layer", LAYER_DIM))
        ac.goi_lai(lambda: doc.Regen(1))
    return ket_qua


def xu_ly(phong, tso, he_so):
    ket_qua = []
    for handle, dg in phong:
        dg_m = [(x / he_so, y / he_so) for x, y in dg]
        kq = tinh_phong(dg_m, tso)
        kq["handle"] = handle
        ket_qua.append(kq)
    return ket_qua


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    nguon = ap.add_mutually_exclusive_group(required=True)
    nguon.add_argument("--dxf", help="File DXF đầu vào")
    nguon.add_argument("--com", action="store_true", help="Dùng bản vẽ đang mở trong AutoCAD")
    ap.add_argument("--loai", required=True, choices=["sprinkler", "bao_khoi", "bao_nhiet"])
    ap.add_argument("--nhom", help="Nhóm nguy hiểm cháy cho sprinkler: 1, 2, 3, 4.1")
    ap.add_argument("--tran", type=float, help="Chiều cao trần (m), bắt buộc với đầu báo")
    ap.add_argument("--layer-phong", default="PCCC-PHONG")
    ap.add_argument("--don-vi", choices=["mm", "m"], default="mm")
    ap.add_argument("--ra", help="File DXF đầu ra (mặc định <tên>_pccc.dxf)")
    ap.add_argument("--chi-tinh", action="store_true", help="Chỉ tính và in kết quả, không vẽ")
    ap.add_argument("--ty-le", type=float, default=100, help="Tỷ lệ in để đặt cỡ chữ dim (mặc định 1:100)")
    ap.add_argument("--khong-dim", action="store_true", help="Không ghi kích thước (mặc định luôn dim)")
    args = ap.parse_args()

    tso = doc_thong_so(args.loai, args.nhom, args.tran)
    kh = json.loads((THU_MUC / "thong_so.json").read_text(encoding="utf-8"))["ky_hieu"][args.loai]
    he_so = 1000.0 if args.don_vi == "mm" else 1.0

    ket_qua = chay_dxf(args, tso, kh, he_so) if args.dxf else chay_com(args, tso, kh, he_so)

    print(f"Thông số: {tso['nguon']} | bước ≤ {tso['khoang_cach_max']} m, cách tường ≤ "
          f"{tso['cach_tuong_max']} m, ≤ {tso['dien_tich_max']} m²/thiết bị")
    if not ket_qua:
        print(f"Không thấy polyline kín nào trên layer '{args.layer_phong}'.")
        return
    tong = 0
    for kq in ket_qua:
        tong += len(kq["diem"])
        print(f"- Phòng {kq['handle']}: {kq['dien_tich']:.1f} m², {len(kq['diem'])} thiết bị, "
              f"bước {kq['buoc_x']:.2f} x {kq['buoc_y']:.2f} m, {len(kq['dim'])} kích thước")
        for cb in kq["canh_bao"]:
            print(f"    ! {cb}")
    print(f"Tổng: {len(ket_qua)} phòng, {tong} thiết bị.")


if __name__ == "__main__":
    main()
