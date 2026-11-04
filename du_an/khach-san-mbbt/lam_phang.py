"""Phá block lồng của từng tầng (từ MBBT_bind.dxf) thành block phẳng 'T_<tầng>' toạ độ tầng
(gốc = điểm chèn tầng), layer = layer lá (bỏ tiền tố xref '...$0$'). Ghi tang.dxf + ảnh kiểm tra."""
import collections, sys
import ezdxf
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

TANG = {"HAM": 0, "TRET": 23440, "LUNG": 46880, "T2": 70320, "T3": 93760, "T4": 117200, "T5": 140640,
        "T6": 164080, "T7": 187520, "SAN_THUONG": 210960, "MAI": 234400}
src = ezdxf.readfile("MBBT_bind.dxf")
out = ezdxf.new("R2018", setup=True); out.units = 4


def la(layer):
    return layer.split("$0$")[-1].split("|")[-1]


def phang(e, lop_cha, sau=0):
    t = e.dxftype()
    if t == "INSERT":
        if sau > 12: return
        try:
            con = list(e.virtual_entities())
        except Exception:
            return
        lop = la(e.dxf.layer)
        if lop == "0": lop = lop_cha
        for c in con:
            yield from phang(c, lop, sau + 1)
        for a in getattr(e, "attribs", []):
            yield a, la(a.dxf.layer)
        return
    lop = la(e.dxf.layer)
    if lop == "0": lop = lop_cha
    yield e, lop


def BO(lop):
    u = lop.upper()
    return " @ " in u or any(k in u for k in ("TREE", "CAY", "LANDS", "HATCH", "DEFPOINTS", "DIM", "CENTER"))


thong_ke = collections.defaultdict(collections.Counter)
dem = {}
for ins in src.modelspace().query("INSERT"):
    y = round(ins.dxf.insert.y)
    ten = next((k for k, v in TANG.items() if abs(v - y) < 400), None)
    if ten is None: continue
    bn = "T_" + ten
    blk = out.blocks.get(bn) if bn in out.blocks else out.blocks.new(bn)
    for e, lop in phang(ins, la(ins.dxf.layer)):
        if BO(lop) or e.dxftype() in ("DIMENSION", "HATCH", "LEADER", "MULTILEADER", "IMAGE", "WIPEOUT", "SOLID", "POINT"):
            continue
        try:
            if lop not in out.layers: out.layers.add(lop)
            a = {"layer": lop}
            t = e.dxftype(); dy = -TANG[ten]
            if t == "LINE":
                p, q = e.dxf.start, e.dxf.end
                blk.add_line((p.x, p.y + dy), (q.x, q.y + dy), dxfattribs=a)
            elif t in ("LWPOLYLINE", "POLYLINE"):
                pts = [(v[0], v[1] + dy) for v in (e.get_points("xy") if t == "LWPOLYLINE" else [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices])]
                if len(pts) < 2: continue
                blk.add_lwpolyline(pts, close=e.is_closed, dxfattribs=a)
            elif t == "ARC":
                c = e.dxf.center
                blk.add_arc((c.x, c.y + dy), e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle, dxfattribs=a)
            elif t == "CIRCLE":
                c = e.dxf.center
                blk.add_circle((c.x, c.y + dy), e.dxf.radius, dxfattribs=a)
            elif t in ("TEXT", "ATTRIB", "MTEXT"):
                s_ = e.plain_text() if t == "MTEXT" else e.dxf.text
                if not s_ or not s_.strip(): continue
                p = e.dxf.insert
                blk.add_text(s_, height=e.dxf.get("char_height", e.dxf.get("height", 200)) or 200,
                             dxfattribs={"layer": lop if t != "ATTRIB" else "ATTRIB", "insert": (p.x, p.y + dy)})
            else:
                continue
            dem[bn] = dem.get(bn, 0) + 1
            thong_ke[bn][(lop, t)] += 1
        except Exception as ex:
            pass
# tên phòng trong model (MTEXT 'TEXT 2')
for m in src.modelspace().query("MTEXT"):
    y = m.dxf.insert.y
    ten = min(TANG, key=lambda k: abs(y - TANG[k] - 10000) if y >= TANG[k] - 1000 else 1e9)
    for k, v in sorted(TANG.items(), key=lambda kv: kv[1]):
        if y >= v - 1000: ten = k
    if "TEN-PHONG" not in out.layers: out.layers.add("TEN-PHONG")
    out.blocks["T_" + ten].add_text(" ".join(m.plain_text().split()), height=300,
        dxfattribs={"layer": "TEN-PHONG", "insert": (m.dxf.insert.x, m.dxf.insert.y - TANG[ten])})
print(dem)
for bn, c in thong_ke.items():
    print(bn, c.most_common(40))
out.saveas("tang.dxf")
