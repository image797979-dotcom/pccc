"""Thiết kế PCCC khách sạn 8 tầng trên bản vẽ hiện trạng (DXF), ghi ra DXF mới.

  python thiet_ke.py <scripts> hien_trang.dxf phong_all.json KS_PCCC.dxf

Bộ tờ (theo block tầng chèn vào Model):
  nhóm 1 (tờ 6–9 + 1–5): báo cháy  -> chỉ dùng block 1, 2, 3 (3–8), tum
  nhóm 2 (tờ 11–19):     sprinkler
  nhóm 3 (tờ 21–29):     họng nước + bình chữa cháy
"""
import json
import math
import sys
from collections import defaultdict

sys.path.insert(0, sys.argv[1])
import ezdxf
import ezdxf.bbox
import ky_hieu as KH
import rai_thiet_bi as rtb

doc = ezdxf.readfile(sys.argv[2])
msp = doc.modelspace()
phong = json.load(open(sys.argv[3], encoding="utf-8"))
TEN_TANG = {"1": "TẦNG 1", "2": "TẦNG 2", "3": "TẦNG 3-8", "4": "TẦNG 4", "5": "TẦNG 5", "6": "TẦNG 6",
            "7": "TẦNG 7", "8": "TẦNG 8", "tum": "TẦNG TUM"}

# ---- các lần chèn block tầng, chia 3 nhóm theo thứ tự xuất hiện ----
chen = defaultdict(list)
for e in msp.query('INSERT[layer=="@ NETMANH"]'):
    if e.dxf.name in TEN_TANG:
        chen[e.dxf.name].append((e.dxf.insert.x, e.dxf.insert.y))
NHOM = {k: {"bao_chay": v[0], "sprinkler": v[1], "hong_binh": v[2]} for k, v in chen.items()}

LAYER_PHONG = "PCCC-PHONG"
LAYER_DIM = rtb.LAYER_DIM
for ten, mau in [(LAYER_PHONG, 8), (LAYER_DIM, 7)]:
    if ten not in doc.layers:
        doc.layers.add(ten, color=mau)
if rtb.DIMSTYLE not in doc.dimstyles:
    doc.dimstyles.new(rtb.DIMSTYLE, dxfattribs={
        "dimscale": 100, "dimtxt": 2.5, "dimasz": 1.5, "dimexo": 1.0, "dimexe": 1.0, "dimgap": 0.8,
        "dimtad": 1, "dimdec": 0, "dimblk": "ARCHTICK"})

KH.dam_bao_tat_ca(doc)  # một bộ ký hiệu thống nhất cho mọi tờ
if "PCCC-CU" not in doc.layers:
    doc.layers.add("PCCC-CU", color=8)


_thiet_bi_ve_sinh = {}


def _tam_vat_dung(b):
    """Tâm các nét đồ đạc / thiết bị vệ sinh (layer *VAT$DUNG*) trong block tầng."""
    if b not in _thiet_bi_ve_sinh:
        ds = []
        for e in doc.blocks.get(b):
            if "VAT$DUNG" in e.dxf.layer.upper() and e.dxftype() in ("LWPOLYLINE", "CIRCLE", "ARC", "ELLIPSE"):
                try:
                    bb = ezdxf.bbox.extents([e], fast=True)
                except Exception:
                    continue
                if bb.has_data and max(bb.size.x, bb.size.y) < 900:
                    ds.append((bb.center.x, bb.center.y))
        _thiet_bi_ve_sinh[b] = ds
    return _thiet_bi_ve_sinh[b]


def la_wc(p, b):
    """WC / phòng tắm: theo tên; hoặc phòng nhỏ không tên (< 5 m²) có vẽ thiết bị vệ sinh bên trong
    (bồn cầu, lavabo). Phòng nhỏ không có thiết bị (hốc kỹ thuật, phòng máy phát...) vẫn bố trí."""
    t = p["ten"].upper()
    if "WC" in t or "VỆ SINH" in t or "TẮM" in t:
        return True
    if p["ten"] or p["dien_tich"] >= 5.0:
        return False
    if b not in ("1", "2", "tum") and p["dien_tich"] < 4.0:
        return True  # tầng phòng ngủ: vùng nhỏ không tên là WC / hốc tủ của phòng
    return sum(rtb.trong_da_giac(x, y, p["dg"]) for x, y in _tam_vat_dung(b)) >= 1


bo_qua = defaultdict(list)  # phòng không bố trí thiết bị, để báo cáo


def ve_dim(ds, dx, dy):
    for (x1, y1), (x2, y2) in ds:
        p1, p2 = (x1 * 1000 + dx, y1 * 1000 + dy), (x2 * 1000 + dx, y2 * 1000 + dy)
        msp.add_linear_dim(base=p1, p1=p1, p2=p2, angle=0 if abs(y1 - y2) < 1e-9 else 90,
                           dimstyle=rtb.DIMSTYLE, dxfattribs={"layer": LAYER_DIM}).render()


def ve_phong(dg, dx, dy):
    msp.add_lwpolyline([(x + dx, y + dy) for x, y in dg], close=True, dxfattribs={"layer": LAYER_PHONG})


# ================= SPRINKLER (tờ 11–19) =================
tso = rtb.doc_thong_so("sprinkler", "1")
thong_ke = {"sprinkler": {}}
dau_spr = defaultdict(list)      # block -> [(x, y)] đầu phun (mm, toạ độ block)
dau_theo_phong = defaultdict(list)  # block -> [(phòng, [(x, y)])]
for b, ds in phong.items():
    dx, dy = NHOM[b]["sprinkler"]
    tong, canh_bao = 0, []
    for p in ds:
        if la_wc(p, b):
            bo_qua[TEN_TANG[b]].append(f"{p['ten'] or 'WC/hốc'} {p['dien_tich']} m²")
            continue
        dg_m = [(x / 1000, y / 1000) for x, y in p["dg"]]
        kq = rtb.tinh_phong(dg_m, tso)
        ve_phong(p["dg"], dx, dy)
        pts = [(x * 1000, y * 1000) for x, y in kq["diem"]]
        dau_spr[b] += pts
        dau_theo_phong[b].append((p, pts))
        for x, y in kq["diem"]:
            KH.chen(msp, "sprinkler", (x * 1000 + dx, y * 1000 + dy))
        ve_dim(kq["dim"], dx, dy)
        tong += len(kq["diem"])
        canh_bao += [f"{p['ten'] or 'phòng ' + str(round(p['dien_tich'], 1)) + ' m²'}: {c}"
                     for c in kq["canh_bao"] if "chia thành" not in c]
    thong_ke["sprinkler"][TEN_TANG[b]] = {"so_dau": tong, "so_phong": len(ds), "canh_bao": canh_bao}
    print(f"[Sprinkler] {TEN_TANG[b]}: {len(ds)} phòng, {tong} đầu", flush=True)
    for c in canh_bao:
        print("   !", c)

# ================= Tiện ích đặt thiết bị trên tường =================
import tim_phong as tp


def luoi_truc(b):
    """Toạ độ trục (mm, toạ độ block) từ layer DLC-TRUC: gx = trục 1..6 (bỏ trục 7 của thang 2),
    gy = trục A..C."""
    gx, gy = set(), set()
    for e in doc.blocks.get(b):
        if tp._hau_to(e.dxf.layer) != "DLC-TRUC" or e.dxftype() != "LWPOLYLINE":
            continue
        (x1, y1), (x2, y2) = [tuple(v) for v in e.get_points("xy")][:2]
        # bản vẽ nhập từ PDF có thể lệch góc rất nhỏ (vài mm trên chục mét)
        if abs(x1 - x2) < 0.01 * abs(y1 - y2):
            gx.add(round((x1 + x2) / 2))
        elif abs(y1 - y2) < 0.01 * abs(x1 - x2):
            gy.add(round((y1 + y2) / 2))
    gx, gy = sorted(gx), sorted(gy)
    return gx[:6], gy


def phong_chua(b, x, y):
    for p in phong[b]:
        if rtb.trong_da_giac(x, y, p["dg"]):
            return p
    return min(phong[b], key=lambda p: min(math.dist((x, y), q) for q in p["dg"]))


def len_tuong(b, x, y, huong=None, cach=150):
    """Dời điểm (x, y) tới sát tường gần nhất (theo huong nếu cho), lùi vào trong `cach` mm."""
    p = phong_chua(b, x, y)
    dg = p["dg"]
    lua_chon = []
    for t in rtb._giao_doc(dg, x):
        lua_chon.append(("tren" if t > y else "duoi", abs(t - y), (x, t - cach if t > y else t + cach)))
    for t in rtb._giao_ngang(dg, y):
        lua_chon.append(("phai" if t > x else "trai", abs(t - x), (t - cach if t > x else t + cach, y)))
    if huong:
        lua_chon = [c for c in lua_chon if c[0] == huong] or lua_chon
    _, _, diem = min(lua_chon, key=lambda c: c[1])
    return diem, p


def dat(loai, x, y, dx, dy):
    KH.chen(msp, loai, (x + dx, y + dy))


def dim_toi_tuong(b, pts, dx, dy):
    """Dim từ thiết bị tới tường gần nhất theo hai phương (quy ước: luôn dim thiết bị PCCC)."""
    for x, y in pts:
        dg_m = [(u / 1000, v / 1000) for u, v in phong_chua(b, x, y)["dg"]]
        ve_dim(rtb.tinh_dim(dg_m, [], [(x / 1000, y / 1000)], [(x / 1000, y / 1000)]), dx, dy)


# ================= BÁO CHÁY (tờ 6–9: block 1, 2, 3, tum) =================
# Thiết bị báo cháy cũ trong 4 tờ này: chuyển sang layer PCCC-CU (đóng băng), không xoá
khung_bc = []
for b in ["1", "2", "3", "tum"]:
    dx, dy = NHOM[b]["bao_chay"]
    xs = [x + dx for p in phong[b] for x, _ in p["dg"]]
    ys = [y + dy for p in phong[b] for _, y in p["dg"]]
    khung_bc.append((min(xs) - 3000, min(ys) - 8000, max(xs) + 3000, max(ys) + 3000))
LOP_CU = {"Báo cháy", "3 - THIETBI PCCC", "F-FITTING-25", "3.GW-Wall"}
so_cu = 0
for e in list(msp):
    l = e.dxf.layer
    if e.dxftype() in ("TEXT", "MTEXT") and l == "0":
        s = (e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text).upper()
        cu = "ZONE" in s or "KEÁT NOÁI" in s
    elif l == "@ NETMANH":
        # dim / nét ghi chú của thiết kế báo cháy cũ nằm chung layer với block mặt bằng
        cu = e.dxftype() in ("DIMENSION", "LINE", "LWPOLYLINE", "LEADER")
    else:
        cu = l in LOP_CU
    if not cu:
        continue
    try:
        bb = ezdxf.bbox.extents([e], fast=True)
        c = ((bb.extmin.x + bb.extmax.x) / 2, (bb.extmin.y + bb.extmax.y) / 2)
    except Exception:
        continue
    if any(k[0] <= c[0] <= k[2] and k[1] <= c[1] <= k[3] for k in khung_bc):
        e.dxf.layer = "PCCC-CU"
        so_cu += 1
doc.layers.get("PCCC-CU").freeze()
print(f"[Báo cháy] Chuyển {so_cu} đối tượng báo cháy cũ sang layer PCCC-CU (đóng băng)")

thong_ke["bao_chay"] = {}
for b in ["1", "2", "3", "tum"]:
    dx, dy = NHOM[b]["bao_chay"]
    gx, gy = luoi_truc(b)
    dem = {"bao_khoi": 0, "bao_nhiet": 0, "nut_an": 0, "chuong_den": 0, "tu_tt": 0}
    dau_bao = []
    # Tên phòng nằm ngoài polygon (chữ ghi cạnh phòng nhỏ): gán cho phòng gần nhất
    for e in doc.blocks.get(b).query("TEXT MTEXT"):
        s = " ".join((e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text).split())
        if "MÁY PHÁT" in s.upper():
            gan = min(phong[b], key=lambda p: min(math.dist((e.dxf.insert.x, e.dxf.insert.y), q) for q in p["dg"]))
            if "MÁY PHÁT" not in gan["ten"].upper():
                gan["ten"] = (gan["ten"] + " / " if gan["ten"] else "") + s
    for p in phong[b]:
        if la_wc(p, b):
            continue
        loai = "bao_nhiet" if "MÁY PHÁT" in p["ten"].upper() else "bao_khoi"
        kq = rtb.tinh_phong([(x / 1000, y / 1000) for x, y in p["dg"]], rtb.doc_thong_so(loai, tran=3.3))
        for x, y in kq["diem"]:
            KH.chen(msp, loai, (x * 1000 + dx, y * 1000 + dy))
            dau_bao.append((x * 1000, y * 1000))
        ve_dim(kq["dim"], dx, dy)
        dem[loai] += len(kq["diem"])

    # Nút ấn + chuông đèn: cạnh lối vào thang bộ chính (giữa trục 2–3) và thang bộ 2 (trục 6)
    if b == "tum":
        ktp = max(phong[b], key=lambda p: ("KỸ THUẬT" in p["ten"].upper(), p["dien_tich"]))
        cx = sum(x for x, _ in ktp["dg"]) / len(ktp["dg"])
        cy = sum(y for _, y in ktp["dg"]) / len(ktp["dg"])
        vi_tri = [len_tuong(b, cx, cy)[0]]
    else:
        vi_tri = [len_tuong(b, gx[1] + 2000, gy[1] + 800, "duoi" if b in ("1", "2") else "tren")[0],
                  len_tuong(b, gx[-1] - 600, gy[1] + 800, "phai")[0]]
    for (x, y) in vi_tri:
        dat("nut_an", x - 300, y, dx, dy)
        dat("chuong_den", x + 300, y, dx, dy)
        dem["nut_an"] += 1
        dem["chuong_den"] += 1
    dim_toi_tuong(b, [(x - 300, y) for x, y in vi_tri], dx, dy)

    # Tủ trung tâm báo cháy: phòng an ninh tầng 1
    if b == "1":
        an_ninh = next(p for p in phong[b] if "AN NINH" in p["ten"].upper())
        cx = sum(x for x, _ in an_ninh["dg"]) / len(an_ninh["dg"])
        cy = sum(y for _, y in an_ninh["dg"]) / len(an_ninh["dg"])
        (tx, ty), _ = len_tuong(b, cx, cy, "tren", cach=250)
        dat("tu_tt", tx, ty, dx, dy)
        dim_toi_tuong(b, [(tx, ty)], dx, dy)
        dem["tu_tt"] = 1

    # Cáp tín hiệu: nối tuần tự các đầu báo theo đường gần nhất, bắt đầu từ nút ấn thứ nhất
    con = list(dau_bao)
    tuyen = [vi_tri[0]]
    while con:
        k = min(range(len(con)), key=lambda i: math.dist(tuyen[-1], con[i]))
        tuyen.append(con.pop(k))
    tuyen += vi_tri[1:]
    tuyen_vuong = [tuyen[0]]
    for (x1, y1), (x2, y2) in zip(tuyen, tuyen[1:]):
        tuyen_vuong += [(x2, y1), (x2, y2)]  # đi cáp vuông góc theo trần
    msp.add_lwpolyline([(x + dx, y + dy) for x, y in tuyen_vuong], dxfattribs={"layer": "PCCC-CAP-BC", "linetype": "DASHED"} if "DASHED" in doc.linetypes else {"layer": "PCCC-CAP-BC"})
    dai = sum(math.dist(a, c) for a, c in zip(tuyen_vuong, tuyen_vuong[1:])) / 1000
    dem["cap_m"] = round(dai, 1)
    thong_ke["bao_chay"][TEN_TANG[b]] = dem
    print(f"[Báo cháy] {TEN_TANG[b]}: {dem}", flush=True)


# ================= HỌNG NƯỚC + BÌNH CHỮA CHÁY (tờ 21–29) =================
thong_ke["hong_binh"] = {}
hong_vt = {}
for b in phong:
    dx, dy = NHOM[b]["hong_binh"]
    gx, gy = luoi_truc(b)
    dem = {"hong": 0, "binh": 0}
    binh = []
    if b != "tum":
        (hx, hy), _ = len_tuong(b, gx[1] + 3200, gy[1] + 800, "duoi" if b in ("1", "2") else "tren")
        dat("hong", hx, hy, dx, dy)
        hong_vt[b] = (hx, hy)
        dem["hong"] = 1
        # Dim hộp họng nước: theo phương dọc nhà tới trục gần nhất, phương ngang tới tường
        truc = min(gx, key=lambda g: abs(g - hx))
        ve_dim([((truc / 1000, hy / 1000), (hx / 1000, hy / 1000))], dx, dy)
        dg_m = [(u / 1000, v / 1000) for u, v in phong_chua(b, hx, hy)["dg"]]
        ty = min(rtb._giao_doc(dg_m, hx / 1000), key=lambda t: abs(t - hy / 1000))
        ve_dim([((hx / 1000, ty), (hx / 1000, hy / 1000))], dx, dy)
        binh += [(hx + 600, hy), (hx + 1000, hy)]  # 2 bình đặt cạnh hộp họng nước
        (sx2, sy2), _ = len_tuong(b, gx[-1] - 600, gy[1] + 800, "phai")
        binh += [(sx2, sy2 + 250), (sx2, sy2 - 250)]  # 2 bình trên tường cuối hành lang, cạnh thang bộ 2
        # kiểm tra tầm với: vòi 20 m + tia đặc ~6 m (đường chim bay, cần kiểm tra lại theo lối đi)
        xa = max(math.dist((hx, hy), q) for p in phong[b] for q in p["dg"]) / 1000
        dem["hong_tam_xa_nhat_m"] = round(xa, 1)
    else:
        ktp = max(phong[b], key=lambda p: ("KỸ THUẬT" in p["ten"].upper(), p["dien_tich"]))
        cx = sum(x for x, _ in ktp["dg"]) / len(ktp["dg"])
        cy = sum(y for _, y in ktp["dg"]) / len(ktp["dg"])
        (bx, by), _ = len_tuong(b, cx, cy)
        binh += [(bx - 200, by), (bx + 200, by)]
    for x, y in binh:
        dat("binh", x, y, dx, dy)
    # bình cạnh hộp họng nước đã định vị theo hộp; chỉ dim cụm bình độc lập
    dim_toi_tuong(b, binh[2:3] if b != "tum" else binh[:1], dx, dy)
    dem["binh"] = len(binh)
    nhom_binh = binh[::2]
    dem["binh_xa_nhat_m"] = round(max(min(math.dist(q, g) for g in nhom_binh)
                                      for p in phong[b] for q in p["dg"]) / 1000, 1)
    thong_ke["hong_binh"][TEN_TANG[b]] = dem
    print(f"[Họng/bình] {TEN_TANG[b]}: {dem}", flush=True)

# ================= ĐƯỜNG ỐNG (sơ bộ, cần tính thuỷ lực) =================
import ong as ONG


def ve_ong(p1, p2, dn, he, dx, dy, nhan=True, chu=None):
    """Vẽ một đoạn ống (mm, toạ độ block) trên layer theo DN, ghi DN cạnh ống."""
    goc, mau, _ = KH.LAYER_ONG[he]
    layer = f"{goc}-D{dn}"
    if layer not in doc.layers:
        doc.layers.add(layer, color=mau)
    rong = 40 if dn >= 65 else 25
    msp.add_lwpolyline([(p1[0] + dx, p1[1] + dy), (p2[0] + dx, p2[1] + dy)],
                       dxfattribs={"layer": layer, "const_width": rong})
    L = abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])
    if nhan and L >= 600:
        doc_ngang = abs(p2[1] - p1[1]) < 1
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        # chữ dim nằm phía trên / bên trái đường dim (trùng tuyến ống), nên ghi DN phía dưới / bên phải
        t = msp.add_text(chu or f"DN{dn}", height=120,
                         dxfattribs={"layer": KH.LAYER_TEXT[0], "style": KH.KIEU_CHU,
                                     "rotation": 0 if doc_ngang else 90})
        t.set_placement((mx + dx + (300 if doc_ngang else 0), my + dy - 100) if doc_ngang
                        else (mx + dx + 100, my + dy + 300),
                        align=ezdxf.enums.TextEntityAlignment.TOP_CENTER)


def ghi_chu(s, x, y, dx, dy):
    msp.add_text(s, height=150, dxfattribs={"layer": KH.LAYER_TEXT[0], "style": KH.KIEU_CHU}).set_placement(
        (x + dx, y + dy), align=ezdxf.enums.TextEntityAlignment.BOTTOM_LEFT)


def phong_bom(b):
    p = next((p for p in phong[b] if "BƠM" in p["ten"].upper()), None)
    if p:
        return (sum(x for x, _ in p["dg"]) / len(p["dg"]), sum(y for _, y in p["dg"]) / len(p["dg"]))


thong_ke["ong_spr"], thong_ke["ong_hong"] = {}, {}

# --- Sprinkler: trục đứng cạnh thang chính, ống chính theo tim hành lang, nhánh tới từng cột đầu ---
for b in phong:
    dx, dy = NHOM[b]["sprinkler"]
    gx, gy = luoi_truc(b)
    dau = dau_spr[b]
    if not dau:
        continue
    # ống chính: đi qua hàng đầu phun hành lang (phòng không tên dài nhất), nếu không có thì
    # chọn hàng đầu phun gần tim hành lang dự kiến nhất
    hanh_lang = [(p, pts) for p, pts in dau_theo_phong[b]
                 if pts and (not p["ten"] or "HÀNH LANG" in p["ten"].upper())]
    hanh_lang.sort(key=lambda t: -(max(x for x, _ in t[0]["dg"]) - min(x for x, _ in t[0]["dg"])))
    y_muc = gy[1] + 800 if len(gy) > 1 else sum(y for _, y in dau) / len(dau)
    if hanh_lang and b not in ("1", "2"):
        ys = [y for _, y in hanh_lang[0][1]]
        y_chinh = max(set(ys), key=ys.count)
    else:
        y_chinh = min({y for _, y in dau}, key=lambda y: abs(y - y_muc))
    huong = "duoi" if b in ("1", "2") else "tren"
    if b == "tum":
        x_tb = sum(x for x, _ in dau) / len(dau)
        (rx, ry), _ = len_tuong(b, x_tb, y_chinh)
    else:
        (rx, ry), _ = len_tuong(b, gx[1] + 1800, y_chinh, huong)
    doan = ONG.tuyen_spr(dau, rx, ry, y_chinh)
    truoc = {}
    for p1, p2, n, loai in doan:
        dn = ONG.dn_spr(n)
        if loai == "nhanh":
            # ghi DN ở đoạn sát ống chính và ở chỗ đổi cỡ ống
            nhan = abs(p1[1] - y_chinh) < 1 or ONG.dn_spr(n + 1) != dn
        else:
            nhan = True
        ve_ong(p1, p2, dn, "spr", dx, dy, nhan=nhan)
    KH.chen(msp, "truc_spr", (rx + dx, ry + dy))
    # van khống chế + công tắc dòng chảy trên đoạn từ trục đứng ra ống chính
    if abs(y_chinh - ry) > 700:  # đoạn trục -> ống chính đủ dài: van nằm trên đoạn đó
        van = KH.chen(msp, "van_spr", (rx + dx, ry + (350 if y_chinh > ry else -350) + dy))
        van.dxf.rotation = 90
    else:                        # đoạn ngắn: van nằm trên ống chính, sát điểm rẽ từ trục
        KH.chen(msp, "van_spr", (rx + 450 + dx, y_chinh + dy))
    # ghi chú trục đứng đặt phía sau tường (ngoài hành lang) để không đè dim / DN
    ghi_chu("TRỤC ĐỨNG SPRINKLER DN100", rx + 250, ry + (-450 if huong == "duoi" else 250), dx, dy)
    truc = min(gx, key=lambda g: abs(g - rx))
    ve_dim([((truc / 1000, ry / 1000), (rx / 1000, ry / 1000))], dx, dy)  # định vị trục đứng theo trục lưới
    dai = ONG.gom_chieu_dai(doan, ONG.dn_spr)
    # lưu mạng ống để tính thuỷ lực: đoạn (mm), trục đứng, diện tích bảo vệ của từng đầu
    dt_dau = []
    for p, pts in dau_theo_phong[b]:
        for x, y in pts:
            dt_dau.append([x, y, round(p["dien_tich"] / len(pts), 2), p["ten"]])
    thong_ke.setdefault("mang_spr", {})[TEN_TANG[b]] = {
        "truc": [rx, ry], "doan": [[list(p1), list(p2), n, loai] for p1, p2, n, loai in doan], "dau": dt_dau}
    # tầng 1: ống cấp từ trạm bơm tới chân trục đứng
    if b == "1" and phong_bom(b):
        px, py = phong_bom(b)
        for a, c in [((px, py), (px, ry)), ((px, ry), (rx, ry))]:
            ve_ong(a, c, 100, "spr", dx, dy, chu="DN100 TỪ TRẠM BƠM")
            dai[100] = dai.get(100, 0) + abs(c[0] - a[0]) + abs(c[1] - a[1])
    thong_ke["ong_spr"][TEN_TANG[b]] = {f"DN{k}": round(v / 1000, 1) for k, v in sorted(dai.items())}
    print(f"[Ống sprinkler] {TEN_TANG[b]}: {thong_ke['ong_spr'][TEN_TANG[b]]}", flush=True)

# --- Họng nước: trục đứng DN100 cạnh hộp, nhánh DN50 vào hộp; tầng 1 có ống cấp từ trạm bơm ---
for b, (hx, hy) in hong_vt.items():
    dx, dy = NHOM[b]["hong_binh"]
    rx, ry = hx - 750, hy
    KH.chen(msp, "truc_hong", (rx + dx, ry + dy))
    ve_ong((rx, ry), (hx - 375, hy), 50, "hong", dx, dy, nhan=False)
    ghi_chu("TRỤC ĐỨNG HỌNG NƯỚC DN100, NHÁNH DN50", rx - 2600, ry + (-450 if b in ("1", "2") else 250), dx, dy)
    gxh, _ = luoi_truc(b)
    truc = min(gxh, key=lambda g: abs(g - rx))
    ve_dim([((truc / 1000, ry / 1000), (rx / 1000, ry / 1000))], dx, dy)  # định vị trục đứng theo trục lưới
    dai = {50: 375.0}
    if b == "1" and phong_bom(b):
        px, py = phong_bom(b)
        for a, c in [((px, py), (px, ry)), ((px, ry), (rx, ry))]:
            ve_ong(a, c, 100, "hong", dx, dy, chu="DN100 TỪ TRẠM BƠM")
            dai[100] = dai.get(100, 0) + abs(c[0] - a[0]) + abs(c[1] - a[1])
    thong_ke["ong_hong"][TEN_TANG[b]] = {f"DN{k}": round(v / 1000, 1) for k, v in sorted(dai.items())}
    print(f"[Ống họng] {TEN_TANG[b]}: {thong_ke['ong_hong'][TEN_TANG[b]]}", flush=True)

# ================= Bảng ký hiệu trên từng tờ (cùng block với thiết bị) =================
khung = []
for e in msp.query('LWPOLYLINE[layer=="Tpl_Bound"]'):
    xs, ys = zip(*e.get_points("xy"))
    khung.append((min(xs), min(ys), max(xs), max(ys)))
khung.sort(key=lambda k: (-round(k[1] / 1000), k[0]))
BANG = {
    range(6, 10): (["bao_khoi", "bao_nhiet", "nut_an", "chuong_den", "tu_tt"], True, ()),
    range(11, 20): (["sprinkler", "truc_spr", "van_spr"], False, ("spr",)),
    range(21, 30): (["hong", "binh", "truc_hong"], False, ("hong",)),
}
for to, (ds, cap, ong_) in BANG.items():
    for so in to:
        x0, y0, _, _ = khung[so - 1]
        KH.ve_bang(msp, (x0 + 1500, y0 + 1500), ds, co_cap=cap, ong=ong_)

thong_ke["bo_qua"] = bo_qua
json.dump(thong_ke, open(sys.argv[4] + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
doc.saveas(sys.argv[4])
print("Đã lưu", sys.argv[4])
