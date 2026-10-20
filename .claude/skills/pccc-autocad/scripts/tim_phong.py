"""Tự dựng polyline phòng từ nét tường / cột / cửa (dùng cho bản vẽ nhập từ PDF, chưa có phòng).

Cách làm: tô tường, cột, khung cửa sổ và cánh cửa + bán kính cung mở cửa (để "đóng" lỗ cửa)
lên một lưới ô vuông; vùng trống kín không chạm biên là một phòng. Biên vùng được dò lại
thành polygon trực giao. Tên phòng lấy từ TEXT/MTEXT nằm trong vùng.

Dùng như thư viện:
    from tim_phong import tim_phong_trong_block
    phong = tim_phong_trong_block(doc, "4", lop_tuong=[...], lop_cua=[...])
    # -> [{"ten": "PHÒNG NGỦ 10", "dg": [(x, y), ...], "dien_tich": m2}, ...]  (toạ độ block, mm)

Hoặc chạy thử: python tim_phong.py ban_ve.dxf <tên block> anh_kiem_tra.png
"""
import math
import sys
from collections import deque

import numpy as np
from matplotlib.path import Path as MPath

O = 40.0  # kích thước ô lưới (mm)


def _hau_to(layer):
    """'PDF7_XREF$MB$HL-NET$TUONG' -> 'HL-NET$TUONG' (bỏ tiền tố do PDF import / xref)."""
    return layer.split("$MB$", 1)[1] if "$MB$" in layer else layer


def _thu_hinh(blk, lop_tuong, lop_cua):
    """Gom hình học: tường (đoạn + đa giác đặc), cung cửa [(tâm, đầu1, đầu2)], nét cửa thẳng."""
    doan, dac, cung, net_cua = [], [], [], []
    for e in blk:
        l = _hau_to(e.dxf.layer)
        t = e.dxftype()
        if l in lop_tuong:
            if t == "LWPOLYLINE":
                p = [tuple(v) for v in e.get_points("xy")]
                if e.closed and len(p) >= 3 and l in LOP_TO_DAC:
                    dac.append(p)
                doan += list(zip(p, p[1:] + ([p[0]] if e.closed else [])))
            elif t == "SOLID":
                dac.append([(q.x, q.y) for q in e.vertices()])
            elif t == "LINE":
                doan.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
            elif t in ("ARC", "CIRCLE"):
                pts = [(q.x, q.y) for q in e.construction_tool().flattening(20)] if t == "ARC" else \
                      [(e.dxf.center.x + e.dxf.radius * math.cos(a / 18 * math.pi),
                        e.dxf.center.y + e.dxf.radius * math.sin(a / 18 * math.pi)) for a in range(37)]
                doan += list(zip(pts, pts[1:]))
        elif l in lop_cua:
            if t == "LWPOLYLINE":
                p = [tuple(v) for v in e.get_points("xy")]
                if not e.closed and len(p) >= 4 and _la_cung(p):
                    tam = _tam_cung(p)
                    if tam:
                        cung.append((tam, p[0], p[-1]))
                    continue
                if e.closed:
                    p.append(p[0])
                net_cua.append(p)
            elif t == "ARC":
                c = (e.dxf.center.x, e.dxf.center.y)
                dau = [(c[0] + e.dxf.radius * math.cos(math.radians(g)), c[1] + e.dxf.radius * math.sin(math.radians(g)))
                       for g in (e.dxf.start_angle, e.dxf.end_angle)]
                cung.append((c, dau[0], dau[1]))
            elif t == "LINE":
                net_cua.append([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
    return doan, dac, cung, net_cua


def _dong_lo_cua(vc_tuong, bbox, cung, net_cua):
    """Đoạn thẳng đóng lỗ cửa + nét cửa sổ, KHÔNG gồm cánh cửa và cung mở.

    Với mỗi cung, bán kính nào nằm thẳng hàng với tường (phía sau bản lề là tường) là lỗ cửa;
    bán kính kia là cánh cửa đang mở 90°. Nét cửa thẳng nằm trong vòng quét của cung là cánh
    cửa, bỏ qua; còn lại (khung cửa sổ trên tường ngoài) giữ làm vật cản.
    """
    x0, y0 = bbox[0], bbox[1]
    ny, nx = vc_tuong.shape

    def la_tuong(x, y):
        i, j = int((x - x0) / O), int((y - y0) / O)
        return 0 <= j < ny and 0 <= i < nx and vc_tuong[j, i]

    doan = []
    for c, a, b in cung:
        diem = []
        for p in (a, b):
            r = math.dist(c, p) or 1
            ux, uy = (p[0] - c[0]) / r, (p[1] - c[1]) / r
            diem.append(sum(la_tuong(c[0] - ux * d, c[1] - uy * d) for d in (80, 160, 240)))
        if diem[0] == diem[1]:
            doan += [(c, a), (c, b)]  # không rõ: đóng cả hai cho chắc
        else:
            doan.append((c, a if diem[0] > diem[1] else b))
    for p in net_cua:
        la_canh = any(all(math.dist(c, q) <= math.dist(c, a) + 60 for q in p) for c, a, _ in cung)
        if not la_canh:
            doan += list(zip(p, p[1:]))
    return doan


def _tam_cung(p):
    """Tâm cung qua 3 điểm (đầu, giữa, cuối)."""
    (ax, ay), (bx, by), (cx, cy) = p[0], p[len(p) // 2], p[-1]
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    ux = ((ax**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d
    uy = ((ax**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax - cx) + (cx**2 + cy**2) * (bx - ax)) / d
    return (ux, uy)


def _la_cung(p):
    """Polyline cong (cung cửa xấp xỉ bằng nhiều đoạn), không phải đường thẳng/gấp khúc vuông."""
    (x0, y0), (x1, y1) = p[0], p[-1]
    dai = math.hypot(x1 - x0, y1 - y0)
    if dai < 300:
        return False
    lech = max(abs((x1 - x0) * (y0 - y) - (x0 - x) * (y1 - y0)) / dai for x, y in p)
    return lech > 0.1 * dai


def _raster(doan, dac, bbox):
    x0, y0, x1, y1 = bbox
    nx, ny = int((x1 - x0) / O) + 1, int((y1 - y0) / O) + 1
    vc = np.zeros((ny, nx), dtype=bool)

    def o(x, y):
        return int((y - y0) / O), int((x - x0) / O)

    for (ax, ay), (bx, by) in doan:
        n = max(1, int(math.hypot(bx - ax, by - ay) / (O / 2)))
        for k in range(n + 1):
            j, i = o(ax + (bx - ax) * k / n, ay + (by - ay) * k / n)
            vc[max(0, j - 1):j + 2, max(0, i - 1):i + 2] = True  # nét dày ~3 ô để không lọt khe
    for p in dac:
        xs, ys = zip(*p)
        i0, i1 = max(0, int((min(xs) - x0) / O)), min(nx - 1, int((max(xs) - x0) / O) + 1)
        j0, j1 = max(0, int((min(ys) - y0) / O)), min(ny - 1, int((max(ys) - y0) / O) + 1)
        gx, gy = np.meshgrid(x0 + (np.arange(i0, i1 + 1) + 0.5) * O, y0 + (np.arange(j0, j1 + 1) + 0.5) * O)
        m = MPath(p).contains_points(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)
        vc[j0:j1 + 1, i0:i1 + 1] |= m
    return vc


def _gan_nhan(trong):
    ny, nx = trong.shape
    nhan = np.zeros(trong.shape, dtype=np.int32)
    so = 0
    for j0 in range(ny):
        for i0 in range(nx):
            if not trong[j0, i0] or nhan[j0, i0]:
                continue
            so += 1
            nhan[j0, i0] = so
            q = deque([(j0, i0)])
            while q:
                j, i = q.popleft()
                for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = j + dj, i + di
                    if 0 <= a < ny and 0 <= b < nx and trong[a, b] and not nhan[a, b]:
                        nhan[a, b] = so
                        q.append((a, b))
    return nhan, so


def _mo_hinh(m, r):
    """Phép mở hình thái (co r ô rồi giãn r ô): xoá phần lồi/khe hẹp < 2r ô."""
    def co(a):
        b = a.copy()
        b[1:, :] &= a[:-1, :]; b[:-1, :] &= a[1:, :]; b[:, 1:] &= a[:, :-1]; b[:, :-1] &= a[:, 1:]
        return b

    def gian(a):
        b = a.copy()
        b[1:, :] |= a[:-1, :]; b[:-1, :] |= a[1:, :]; b[:, 1:] |= a[:, :-1]; b[:, :-1] |= a[:, 1:]
        return b

    for _ in range(r):
        m = co(m)
    for _ in range(r):
        m = gian(m)
    return m


def _do_bien(m, x0, y0):
    """Dò biên vùng (mặt nạ bool) thành polygon trực giao; lấy vòng ngoài lớn nhất."""
    ny, nx = m.shape
    p = np.pad(m, 1)
    canh = {}
    # cạnh có hướng, vùng nằm bên trái
    for j, i in zip(*np.nonzero(p)):
        if not p[j - 1, i]:
            canh[(i, j)] = (i + 1, j)          # cạnh dưới, đi sang phải
        if not p[j + 1, i]:
            canh[(i + 1, j + 1)] = (i, j + 1)  # cạnh trên, đi sang trái
        if not p[j, i - 1]:
            canh[(i, j + 1)] = (i, j)          # cạnh trái, đi xuống
        if not p[j, i + 1]:
            canh[(i + 1, j)] = (i + 1, j + 1)  # cạnh phải, đi lên
    vong_tot, dt_tot = None, 0
    da_di = set()
    for bd in list(canh):
        if bd in da_di:
            continue
        vong, d = [], bd
        while d not in da_di and d in canh:
            da_di.add(d)
            vong.append(d)
            d = canh[d]
        if len(vong) < 4:
            continue
        dt = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(vong, vong[1:] + vong[:1]))) / 2
        if dt > dt_tot:
            vong_tot, dt_tot = vong, dt
    if not vong_tot:
        return []
    # bỏ đỉnh thẳng hàng
    gon = []
    n = len(vong_tot)
    for k in range(n):
        a, b, c = vong_tot[k - 1], vong_tot[k], vong_tot[(k + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            gon.append(b)
    return [(x0 + (i - 1) * O, y0 + (j - 1) * O) for i, j in gon]


def _don_bac(dg, nguong=O * 3):
    """Bỏ các bậc nhỏ (< nguong mm) do sai số tô nét: gộp toạ độ x/y gần nhau rồi bỏ đỉnh thừa."""
    for truc in (0, 1):
        gia_tri = sorted({p[truc] for p in dg})
        nhom, ket = [], {}
        for v in gia_tri:
            if nhom and v - nhom[-1] > nguong:
                for u in nhom:
                    ket[u] = sum(nhom) / len(nhom)
                nhom = []
            nhom.append(v)
        for u in nhom:
            ket[u] = sum(nhom) / len(nhom)
        dg = [(ket[x], y) if truc == 0 else (x, ket[y]) for x, y in dg]
    gon = []
    for p in dg:
        if not gon or p != gon[-1]:
            gon.append(p)
    if len(gon) > 1 and gon[0] == gon[-1]:
        gon.pop()
    kq = []
    n = len(gon)
    for k in range(n):
        a, b, c = gon[k - 1], gon[k], gon[(k + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            kq.append(b)
    return kq


def vung_thang(blk, mo_rong=1300, so_bac_min=5):
    """Nhận diện thang bộ từ các nét bậc thang: ≥ so_bac_min đoạn thẳng song song, dài 0,6–1,8 m,
    cách đều 0,2–0,4 m, thẳng hàng hai đầu. Mỗi vế thang được nới thêm `mo_rong` mm theo hướng
    đi lên/xuống để gồm cả chiếu nghỉ. Trả về [(x0, y0, x1, y1), ...] (toạ độ block, mm)."""
    ngang, doc = [], []
    for e in blk:
        if e.dxftype() == "LINE":
            ds = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))]
        elif e.dxftype() == "LWPOLYLINE":
            p = [tuple(v) for v in e.get_points("xy")]
            ds = list(zip(p, p[1:] + ([p[0]] if e.closed else [])))
        else:
            continue
        for (x1, y1), (x2, y2) in ds:
            L = math.hypot(x2 - x1, y2 - y1)
            if not 600 <= L <= 1800:
                continue
            if abs(y1 - y2) < 0.02 * L:
                ngang.append(((y1 + y2) / 2, min(x1, x2), max(x1, x2)))
            elif abs(x1 - x2) < 0.02 * L:
                doc.append(((x1 + x2) / 2, min(y1, y2), max(y1, y2)))

    def tim_ve(ds):
        """ds: (toạ độ vuông góc, đầu, cuối). Gom các đoạn thẳng hàng hai đầu thành dãy cách đều."""
        nhom = {}
        for c, a, b in ds:
            nhom.setdefault((round(a / 100), round(b / 100)), []).append(c)
        ve = []
        for (a, b), cs in nhom.items():
            cs = sorted(set(round(c) for c in cs))
            day = [cs[0]]
            for c in cs[1:] + [None]:
                if c is not None and 180 <= c - day[-1] <= 400:
                    day.append(c)
                    continue
                if len(day) >= so_bac_min:
                    ve.append((a * 100, b * 100, day[0], day[-1]))
                day = [c] if c is not None else []
        return ve

    vung = []
    for a, b, c0, c1 in tim_ve(ngang):   # bậc nằm ngang -> thang đi theo phương y
        vung.append((a - 100, c0 - mo_rong, b + 100, c1 + mo_rong))
    for a, b, c0, c1 in tim_ve(doc):     # bậc thẳng đứng -> thang đi theo phương x
        vung.append((c0 - mo_rong, a - 100, c1 + mo_rong, b + 100))
    return vung


def _bao_theo_cot(dac, gian=150):
    """Khung chữ nhật bao các cột (khối đặc vuông cạnh 200–700 mm), nới ra `gian` mm.

    Dùng khi mặt ngoài nhà để trống hoặc chỉ có vách nhẹ/cửa cuốn không vẽ thành tường,
    để phòng ở mép nhà không bị coi là "bên ngoài".
    """
    cot = []
    for p in dac:
        xs, ys = zip(*p)
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        if 200 <= w <= 700 and 200 <= h <= 700:
            cot.append((min(xs), min(ys), max(xs), max(ys)))
    if len(cot) < 4:
        return []
    x0, y0 = min(c[0] for c in cot) - gian, min(c[1] for c in cot) - gian
    x1, y1 = max(c[2] for c in cot) + gian, max(c[3] for c in cot) + gian
    g = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return list(zip(g, g[1:] + g[:1]))


def tim_phong_trong_block(doc, ten_block, lop_tuong, lop_cua, dien_tich_min=0.8, bao_theo_cot=False):
    blk = doc.blocks.get(ten_block)
    doan, dac, cung, net_cua = _thu_hinh(blk, set(lop_tuong), set(lop_cua))
    if isinstance(bao_theo_cot, tuple):
        # khung đóng biên cho trước (vd. theo trục ngoài cùng), (x0, y0, x1, y1)
        x0, y0, x1, y1 = bao_theo_cot
        g = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        doan += list(zip(g, g[1:] + g[:1]))
    elif bao_theo_cot:
        doan += _bao_theo_cot(dac)
    xs = [p[0] for s in doan for p in s] + [p[0] for d in dac for p in d]
    ys = [p[1] for s in doan for p in s] + [p[1] for d in dac for p in d]
    bbox = (min(xs) - 1000, min(ys) - 1000, max(xs) + 1000, max(ys) + 1000)
    vc_tuong = _raster(doan, dac, bbox)
    vc = vc_tuong | _raster(_dong_lo_cua(vc_tuong, bbox, cung, net_cua), [], bbox)
    nhan, so = _gan_nhan(~vc)
    thang = np.zeros(vc.shape, dtype=bool)
    for x0, y0, x1, y1 in vung_thang(blk):
        thang[max(0, int((y0 - bbox[1]) / O)):max(0, int((y1 - bbox[1]) / O) + 1),
              max(0, int((x0 - bbox[0]) / O)):max(0, int((x1 - bbox[0]) / O) + 1)] = True
    bien = set(nhan[0, :]) | set(nhan[-1, :]) | set(nhan[:, 0]) | set(nhan[:, -1])

    chu = []
    for e in blk.query("TEXT MTEXT"):
        s = " ".join((e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text).split())
        if any(c.isalpha() for c in s):
            chu.append((e.dxf.insert.x, e.dxf.insert.y, s))

    phong = []
    for k in range(1, so + 1):
        if k in bien:
            continue
        m = nhan == k
        if (m & thang).sum() > 0.5 * m.sum():
            continue  # buồng thang bộ: không phải phòng để bố trí thiết bị
        m &= ~thang  # cắt phần chiếu nghỉ / sảnh thang dính vào hành lang
        dt = m.sum() * O * O / 1e6
        if dt < dien_tich_min:
            continue
        m2 = _mo_hinh(m, 4)  # bỏ hốc/khe hẹp < ~0,32 m (hốc tủ, gờ tường) khỏi phòng
        if m2.sum() == 0:
            continue
        # nét tường được tô dày hơn thực tế 1 ô mỗi phía: nới polygon ra lại 1 ô
        m2 = np.pad(m2, 0)
        dg = _don_bac(_do_bien(m2, bbox[0], bbox[1]))
        dg = _no_ra(dg, O)
        if len(dg) < 4:
            continue
        ten = [s for x, y, s in chu if MPath(dg).contains_point((x, y))]
        phong.append({"ten": " / ".join(ten), "dg": dg, "dien_tich": round(_dt(dg) / 1e6, 2)})
    return phong


def _dt(dg):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(dg, dg[1:] + dg[:1]))) / 2


def _no_ra(dg, d):
    """Nới polygon trực giao ra mỗi cạnh d mm (bù phần nét tô dày)."""
    n = len(dg)
    huong = 1 if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(dg, dg[1:] + dg[:1])) > 0 else -1
    kq = []
    for k in range(n):
        a, b, c = dg[k - 1], dg[k], dg[(k + 1) % n]
        # pháp tuyến ngoài của cạnh ab và bc
        def phap(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy) or 1
            return (dy / L * huong, -dx / L * huong)
        n1, n2 = phap(a, b), phap(b, c)
        kq.append((b[0] + d * (n1[0] + n2[0]), b[1] + d * (n1[1] + n2[1])))
    return kq


LOP_TUONG_MAC_DINH = ["HL-NET$TUONG", "DLC-NET$MANH$0.09$2", "kata_net$thay"]
LOP_TO_DAC = {"HL-NET$TUONG", "DLC-NET$MANH$0.09$2"}  # polyline kín trên các layer này là khối tường đặc
LOP_CUA_MAC_DINH = ["DLC-CUA", "KT-Cua"]


if __name__ == "__main__":
    import ezdxf
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    doc = ezdxf.readfile(sys.argv[1])
    ds = tim_phong_trong_block(doc, sys.argv[2], LOP_TUONG_MAC_DINH, LOP_CUA_MAC_DINH)
    fig, ax = plt.subplots(figsize=(24, 11), dpi=90)
    doan, dac, cung, net_cua = _thu_hinh(doc.blocks.get(sys.argv[2]), set(LOP_TUONG_MAC_DINH), set(LOP_CUA_MAC_DINH))
    for (a, b) in doan + [s for p in net_cua for s in zip(p, p[1:])]:
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#999", lw=0.5)
    cm = plt.get_cmap("tab20")
    for k, p in enumerate(ds):
        dg = p["dg"] + p["dg"][:1]
        x, y = zip(*dg)
        ax.fill(x, y, color=cm(k % 20), alpha=0.35)
        ax.plot(x, y, color=cm(k % 20), lw=1.2)
        cx, cy = sum(x[:-1]) / (len(x) - 1), sum(y[:-1]) / (len(y) - 1)
        ax.text(cx, cy, f"{k+1}. {p['ten'][:18]}\n{p['dien_tich']} m²", fontsize=7, ha="center")
        print(f"{k+1:2}. {p['dien_tich']:6.2f} m²  {len(p['dg'])} đỉnh  {p['ten']}")
    ax.set_aspect("equal")
    plt.tight_layout()
    fig.savefig(sys.argv[3])
