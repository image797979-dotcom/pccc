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


def rai_luoi(dg, tso):
    """Lưới đều trong hình bao của phòng, giữ các điểm nằm trong phòng.

    Đơn vị: mét. Trả về (danh sách điểm, bước x, bước y).
    """
    xs, ys = [p[0] for p in dg], [p[1] for p in dg]
    x0, y0 = min(xs), min(ys)
    Lx, Ly = max(xs) - x0, max(ys) - y0
    nx = so_hang(Lx, tso["khoang_cach_max"], tso["cach_tuong_max"])
    ny = so_hang(Ly, tso["khoang_cach_max"], tso["cach_tuong_max"])
    # Diện tích bảo vệ mỗi thiết bị không vượt giới hạn: tăng số hàng ở phía có bước lớn hơn
    while (Lx / nx) * (Ly / ny) > tso["dien_tich_max"] + 1e-9:
        if Lx / nx >= Ly / ny:
            nx += 1
        else:
            ny += 1
    sx, sy = Lx / nx, Ly / ny
    diem = [
        (x0 + sx * (i + 0.5), y0 + sy * (j + 0.5))
        for i in range(nx) for j in range(ny)
        if trong_da_giac(x0 + sx * (i + 0.5), y0 + sy * (j + 0.5), dg)
    ]
    return diem, sx, sy


def bo_sung_vung_trong(dg, diem, sx, sy, buoc_mau=0.25):
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
        if trong_da_giac(x, y, dg)
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
    diem, sx, sy = rai_luoi(dg_m, tso)
    them = bo_sung_vung_trong(dg_m, diem, sx, sy)
    tat_ca = diem + them
    canh_bao = []
    if them:
        canh_bao.append(f"Phòng không chữ nhật: đã bổ sung {len(them)} thiết bị cho vùng chưa phủ, nên kiểm tra lại bằng mắt.")
    if tso["khoang_cach_min"] > 0:
        for i in range(len(tat_ca)):
            for j in range(i + 1, len(tat_ca)):
                if math.dist(tat_ca[i], tat_ca[j]) < tso["khoang_cach_min"] - 1e-6:
                    canh_bao.append(f"Hai thiết bị cách nhau < {tso['khoang_cach_min']} m tại "
                                    f"({tat_ca[i][0]:.2f}, {tat_ca[i][1]:.2f}).")
    return {"diem": tat_ca, "buoc_x": sx, "buoc_y": sy, "dien_tich": dien_tich(dg_m), "canh_bao": canh_bao,
            "dim": tinh_dim(dg_m, diem, them)}


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


def tinh_dim(dg, luoi, them):
    """Các đoạn cần ghi kích thước (toạ độ mét), đủ để định vị mọi thiết bị:

    - Lưới đều: một chuỗi ngang qua hàng nhiều thiết bị nhất và một chuỗi dọc qua cột nhiều
      thiết bị nhất, mỗi chuỗi gồm tường → thiết bị → ... → thiết bị → tường.
    - Thiết bị bổ sung (không theo lưới): dim tới tường gần nhất theo cả hai phương.
    """
    doan = []
    if luoi:
        hang, cot = {}, {}
        for x, y in luoi:
            hang.setdefault(round(y, 6), []).append(x)
            cot.setdefault(round(x, 6), []).append(y)
        y0, xs = max(sorted(hang.items()), key=lambda kv: len(kv[1]))
        xs = sorted(xs)
        tuong = _giao_ngang(dg, y0)
        trai = max((t for t in tuong if t < xs[0]), default=None)
        phai = min((t for t in tuong if t > xs[-1]), default=None)
        doan += _chuoi([t for t in [trai, *xs, phai] if t is not None], y0, ngang=True)

        x0, ys = max(sorted(cot.items()), key=lambda kv: len(kv[1]))
        ys = sorted(ys)
        tuong = _giao_doc(dg, x0)
        duoi = max((t for t in tuong if t < ys[0]), default=None)
        tren = min((t for t in tuong if t > ys[-1]), default=None)
        doan += _chuoi([t for t in [duoi, *ys, tren] if t is not None], x0, ngang=False)

    for x, y in them:
        tx = min(_giao_ngang(dg, y), key=lambda t: abs(t - x), default=None)
        ty = min(_giao_doc(dg, x), key=lambda t: abs(t - y), default=None)
        if tx is not None:
            doan.append(((tx, y), (x, y)))
        if ty is not None:
            doan.append(((x, ty), (x, y)))
    return [(p1, p2) for p1, p2 in doan if math.dist(p1, p2) > 1e-6]


# ---------- Vẽ ----------

def chay_dxf(args, tso, kh, he_so):
    import ezdxf

    doc = ezdxf.readfile(args.dxf)
    msp = doc.modelspace()
    phong = [
        (e.dxf.handle, [(x, y) for x, y in e.get_points("xy")])
        for e in msp.query(f'LWPOLYLINE[layer=="{args.layer_phong}"]') if e.closed
    ]
    if not args.chi_tinh:
        if kh["layer"] not in doc.layers:
            doc.layers.add(kh["layer"], color=kh["mau"])
        if kh["block"] not in doc.blocks:
            blk = doc.blocks.new(kh["block"])
            r = kh["ban_kinh_mm"] / 1000 * he_so
            blk.add_circle((0, 0), r)
            blk.add_text(kh["chu"], height=r * 0.7).set_placement((0, 0), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    ket_qua = xu_ly(phong, tso, he_so)
    if not args.chi_tinh:
        for kq in ket_qua:
            for x, y in kq["diem"]:
                msp.add_blockref(kh["block"], (x * he_so, y * he_so), dxfattribs={"layer": kh["layer"]})
        if not args.khong_dim:
            if LAYER_DIM not in doc.layers:
                doc.layers.add(LAYER_DIM, color=7)
            if DIMSTYLE not in doc.dimstyles:
                doc.dimstyles.new(DIMSTYLE, dxfattribs={
                    "dimscale": args.ty_le / 1000 * he_so, "dimtxt": 2.5, "dimasz": 1.5,
                    "dimexo": 1.0, "dimexe": 1.0, "dimgap": 0.8, "dimtad": 1,
                    "dimdec": 0 if he_so == 1000 else 2, "dimblk": "ARCHTICK",
                })
            for kq in ket_qua:
                for (x1, y1), (x2, y2) in kq["dim"]:
                    p1, p2 = (x1 * he_so, y1 * he_so), (x2 * he_so, y2 * he_so)
                    msp.add_linear_dim(base=p1, p1=p1, p2=p2, angle=0 if y1 == y2 else 90,
                                       dimstyle=DIMSTYLE, dxfattribs={"layer": LAYER_DIM}).render()
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
