"""Phá block lồng từng tầng của mbbt.dxf thành block phẳng 'T_<tầng>' (toạ độ tầng = toạ độ block 'MBBT ...'),
layer = layer lá (bỏ tiền tố '...$0$'). Tên phòng (chữ trên layer đồ đạc/chữ) chuyển sang layer TEN-PHONG.
Ghi tang.dxf."""
import collections
import ezdxf

TEN = {"MBBT HAM": "HAM", "MBBT TRET": "TRET", "MBBT LUNG": "LUNG", "MBBT TANG 2": "T2", "MBBT TANG 3": "T3",
       "MBBT TANG 4": "T4", "MBBT TANG 5": "T5", "MBBT TANG 6": "T6"}
KHONG_TEN = ("MINIBAR", "TRANH", "KỆ", "CONSOLE", "CÂY NƯỚC")
src = ezdxf.readfile("mbbt.dxf")
out = ezdxf.new("R2018", setup=True); out.units = 4


def la(layer):
    return layer.split("$0$")[-1].split("|")[-1]


def phang(e, lop_cha, sau=0):
    if e.dxftype() == "INSERT":
        if sau > 12: return
        try:
            con = list(e.virtual_entities())
        except Exception:
            return
        lop = la(e.dxf.layer)
        if lop == "0": lop = lop_cha
        for c in con:
            yield from phang(c, lop, sau + 1)
        return
    lop = la(e.dxf.layer)
    if lop == "0": lop = lop_cha
    yield e, lop


def BO(lop):
    u = lop.upper()
    return " @ " in u or any(k in u for k in ("TREE", "HATCH", "DEFPOINTS", "DIM", "CENTER", "SYMBOLS"))


tk = collections.defaultdict(collections.Counter)
blk_goc = src.blocks
for bn, ten in TEN.items():
    blk = out.blocks.new("T_" + ten)
    for e0 in blk_goc[bn]:
        for e, lop in phang(e0, la(e0.dxf.layer)):
            if BO(lop) or e.dxftype() in ("DIMENSION", "HATCH", "LEADER", "MULTILEADER", "IMAGE", "WIPEOUT", "SOLID", "POINT"):
                continue
            t = e.dxftype()
            try:
                if t in ("TEXT", "MTEXT"):
                    s = " ".join((e.plain_text() if t == "MTEXT" else e.dxf.text).split())
                    if not s or any(k in s.upper() for k in KHONG_TEN):
                        continue
                    lop = "TEN-PHONG"
                    if lop not in out.layers: out.layers.add(lop)
                    blk.add_text(s, height=250, dxfattribs={"layer": lop, "insert": e.dxf.insert})
                elif t in ("LINE", "LWPOLYLINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE", "POLYLINE"):
                    if lop not in out.layers: out.layers.add(lop)
                    if t == "POLYLINE":
                        pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
                        if len(pts) < 2: continue
                        blk.add_lwpolyline(pts, close=e.is_closed, dxfattribs={"layer": lop})
                    elif t in ("ELLIPSE", "SPLINE"):
                        pts = [(v.x, v.y) for v in e.flattening(20)]
                        blk.add_lwpolyline(pts, dxfattribs={"layer": lop})
                    else:
                        c = e.copy(); c.dxf.layer = lop; c.dxf.linetype = "BYLAYER"
                        blk.add_entity(c)
                else:
                    continue
                tk[ten][lop] += 1
            except Exception:
                pass
for t, c in tk.items():
    print(t, c.most_common(25))
out.saveas("tang.dxf")
