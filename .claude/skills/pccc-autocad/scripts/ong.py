"""Đi ống sprinkler kiểu "xương cá" và chọn đường kính sơ bộ theo số đầu phun.

Sơ đồ: trục đứng -> ống chính chạy theo một đường ngang (thường là tim hành lang) -> ống nhánh
vuông góc tới từng cột đầu phun (các đầu cùng hoành độ dùng chung một nhánh).

Đường kính chọn theo số đầu phun phía sau đoạn ống (bảng ống cho nguy cơ thấp – nhóm 1).
Đây chỉ là CHỌN SƠ BỘ để vẽ và bóc khối lượng; TCVN 7336:2021 yêu cầu tính thuỷ lực
để kiểm tra áp lực, lưu lượng tại đầu bất lợi nhất.

Toạ độ: đơn vị tuỳ ý nhưng thống nhất (script dự án dùng mm).
"""
from collections import defaultdict

# (số đầu tối đa, DN) – bảng ống nguy cơ thấp, dùng cho nhóm 1
BANG_DN_SPR = [(2, 25), (3, 32), (5, 40), (10, 50), (30, 65), (60, 80), (100, 90), (10 ** 9, 100)]


def dn_spr(so_dau):
    for n, dn in BANG_DN_SPR:
        if so_dau <= n:
            return dn
    return 100


def tuyen_spr(dau, x_truc, y_truc, y_chinh, sai_so=1.0):
    """Tuyến ống cho một tầng.

    dau      : [(x, y)] toạ độ đầu phun
    x_truc, y_truc : vị trí trục đứng
    y_chinh  : tung độ ống chính (chạy ngang)
    Trả về [(p1, p2, so_dau_phia_sau, "chinh"|"nhanh"|"truc")], p = (x, y).
    """
    if not dau:
        return []
    cot = defaultdict(list)
    for x, y in dau:
        cot[round(x / sai_so) * sai_so].append(y)

    doan = []
    so_tai_te = {}  # hoành độ điểm rẽ nhánh trên ống chính -> số đầu của nhánh đó
    for x, ys in cot.items():
        tren = sorted(y for y in ys if y > y_chinh + sai_so)
        duoi = sorted((y for y in ys if y < y_chinh - sai_so), reverse=True)
        tren_ong = sum(1 for y in ys if abs(y - y_chinh) <= sai_so)
        for day in (tren, duoi):
            truoc = y_chinh
            for i, y in enumerate(day):
                doan.append(((x, truoc), (x, y), len(day) - i, "nhanh"))
                truoc = y
        so_tai_te[x] = len(ys)
        _ = tren_ong  # đầu nằm ngay trên ống chính: tính vào số đầu tại điểm rẽ

    # ống chính: hai phía của trục đứng, đoạn gần trục mang nhiều đầu nhất
    for phia in (-1, 1):
        te = sorted((x for x in so_tai_te if (x - x_truc) * phia > sai_so), key=lambda x: abs(x - x_truc))
        con_lai = sum(so_tai_te[x] for x in te)
        truoc = x_truc
        for x in te:
            doan.append(((truoc, y_chinh), (x, y_chinh), con_lai, "chinh"))
            con_lai -= so_tai_te[x]
            truoc = x
    # đoạn từ trục đứng ra ống chính
    if abs(y_truc - y_chinh) > sai_so:
        doan.append(((x_truc, y_truc), (x_truc, y_chinh), len(dau), "truc"))
    return doan


def gom_chieu_dai(doan, dn_theo):
    """Tổng chiều dài theo DN: {dn: chiều dài} (cùng đơn vị toạ độ)."""
    kq = defaultdict(float)
    for (x1, y1), (x2, y2), n, _ in doan:
        kq[dn_theo(n)] += abs(x2 - x1) + abs(y2 - y1)
    return dict(kq)
