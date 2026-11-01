"""Model space AutoCAD (COM) giả lập API ezdxf, để các hàm ký hiệu và trình bày vẽ thẳng vào AutoCAD.

`ky_hieu.py` và `trinh_bay.py` viết cho ezdxf (msp.add_line, add_text(...).set_placement, add_linear_dim…).
Bọc model space COM bằng lớp này thì các hàm đó vẽ trực tiếp lên bản vẽ đang mở, người dùng thấy
từng đối tượng hiện ra:

    import acad_com as ac, acad_msp, ky_hieu as kh, trinh_bay as tb
    acad = ac.ket_noi(); doc = acad.ActiveDocument
    doc = acad_msp.nap_thu_vien(doc, ty_le=125)  # block, layer, kiểu chữ, dim style "PCCC"; trả lại doc
    msp = acad_msp.MSP(doc)
    kh.TY_LE = 125
    kh.chen(msp, "bao_khoi", (x, y)); tb.dim_dau_bao(msp, (x, y), dg); tb.khung_a3(msp, goc, 125, tt)

Thư viện (block, layer, style) dựng bằng ezdxf ra DXF → AutoCAD lưu sang DWG → chèn vào bản vẽ
(chèn DWG như block sẽ mang theo định nghĩa block, layer, kiểu chữ, dim style). Block, layer trùng
tên đã có trong bản vẽ thì AutoCAD giữ bản đang có.
"""
import math
import os
import tempfile

import acad_com as ac

_CAN = {  # ezdxf TextEntityAlignment -> AcAlignment
    "LEFT": 0, "CENTER": 1, "RIGHT": 2, "MIDDLE": 4, "TOP_LEFT": 6, "TOP_CENTER": 7, "TOP_RIGHT": 8,
    "MIDDLE_LEFT": 9, "MIDDLE_CENTER": 10, "MIDDLE_RIGHT": 11, "BOTTOM_LEFT": 12, "BOTTOM_CENTER": 13,
    "BOTTOM_RIGHT": 14,
}


def _gan(obj, a, moi=False):
    """Áp các thuộc tính dxfattribs kiểu ezdxf lên đối tượng COM.
    moi=True (đối tượng vừa tạo): màu, nét không chỉ định thì đặt ByLayer, vì COM gán theo màu/nét
    hiện hành của bản vẽ (CECOLOR, CELTYPE), có thể đang là màu bất kỳ."""
    if moi:
        if a.get("color") is None:
            ac.goi_lai(lambda: setattr(obj, "Color", 256))
        if not a.get("linetype"):
            ac.goi_lai(lambda: setattr(obj, "Linetype", "ByLayer"))
        if a.get("lineweight") is None:
            ac.goi_lai(lambda: setattr(obj, "Lineweight", -1))
    if "layer" in a:
        ac.goi_lai(lambda: setattr(obj, "Layer", a["layer"]))
    if a.get("color") is not None:
        ac.goi_lai(lambda: setattr(obj, "Color", int(a["color"])))
    if a.get("lineweight") is not None:
        ac.goi_lai(lambda: setattr(obj, "Lineweight", int(a["lineweight"])))
    if a.get("linetype"):
        ac.goi_lai(lambda: setattr(obj, "Linetype", a["linetype"]))
    if a.get("ltscale"):
        ac.goi_lai(lambda: setattr(obj, "LinetypeScale", float(a["ltscale"])))


class _Dxf:
    """Giả `entity.dxf` để code ezdxf gán được vài thuộc tính sau khi tạo (lineweight, layer…)."""

    def __init__(self, obj):
        object.__setattr__(self, "_o", obj)

    def __setattr__(self, k, v):
        _gan(self._o, {k: v})

    def set(self, k, v):
        _gan(self._o, {k: v})


class _DoiTuong:
    def __init__(self, obj):
        self.obj = obj
        self.dxf = _Dxf(obj)

    def render(self):  # dim COM tự dựng hình
        return self


class _Chu(_DoiTuong):
    def set_placement(self, p, align=None):
        ten = getattr(align, "name", "LEFT") if align is not None else "LEFT"
        can = _CAN.get(ten, 0)
        if can:
            ac.goi_lai(lambda: setattr(self.obj, "Alignment", can))
            ac.goi_lai(lambda: setattr(self.obj, "TextAlignmentPoint", ac.diem(*p[:2])))
        else:
            ac.goi_lai(lambda: setattr(self.obj, "InsertionPoint", ac.diem(*p[:2])))
        return self


class _BangLayer:
    """`msp.doc.layers` tối giản: kiểm tra / tạo layer qua COM."""

    def __init__(self, doc):
        self.doc = doc

    def __contains__(self, ten):
        try:
            ac.goi_lai(lambda: self.doc.Layers.Item(ten), so_lan=1)
            return True
        except Exception:
            return False

    def add(self, ten, color=7, **_):
        la = ac.dam_bao_layer(self.doc, ten, color)
        return _DoiTuong(la)

    def get(self, ten):
        return _DoiTuong(ac.goi_lai(lambda: self.doc.Layers.Item(ten)))


class _Doc:
    def __init__(self, doc):
        self.com = doc
        self.layers = _BangLayer(doc)
        self.linetypes = ()


class MSP:
    """Model space COM với các hàm add_* giống ezdxf (chỉ phần ky_hieu/trinh_bay dùng)."""

    def __init__(self, doc):
        self.com_doc = doc
        self.ms = ac.goi_lai(lambda: doc.ModelSpace)
        self.doc = _Doc(doc)
        self.dem = 0

    def _xong(self, obj, a):
        _gan(obj, a or {}, moi=True)
        self.dem += 1
        return obj

    def add_line(self, p1, p2, dxfattribs=None):
        o = ac.goi_lai(lambda: self.ms.AddLine(ac.diem(*p1[:2]), ac.diem(*p2[:2])))
        return _DoiTuong(self._xong(o, dxfattribs))

    def add_lwpolyline(self, points, format="xy", close=False, dxfattribs=None):
        pts = [tuple(p) for p in points]
        o = ac.goi_lai(lambda: self.ms.AddLightWeightPolyline(ac.mang_2d([p[:2] for p in pts])))
        if close:
            ac.goi_lai(lambda: setattr(o, "Closed", True))
        if "b" in format:
            for i, p in enumerate(pts):
                if len(p) >= 5 and p[4]:
                    ac.goi_lai(lambda: o.SetBulge(i, float(p[4])))
        a = dict(dxfattribs or {})
        if a.get("const_width"):
            ac.goi_lai(lambda: setattr(o, "ConstantWidth", float(a.pop("const_width"))))
        return _DoiTuong(self._xong(o, a))

    def add_circle(self, c, r, dxfattribs=None):
        o = ac.goi_lai(lambda: self.ms.AddCircle(ac.diem(*c[:2]), float(r)))
        return _DoiTuong(self._xong(o, dxfattribs))

    def add_text(self, s, height=2.5, rotation=0, dxfattribs=None):
        a = dict(dxfattribs or {})
        o = ac.goi_lai(lambda: self.ms.AddText(s, ac.diem(0, 0), float(height)))
        if a.get("style"):
            ac.goi_lai(lambda: setattr(o, "StyleName", a.pop("style")))
        rot = a.pop("rotation", rotation) or 0
        if rot:
            ac.goi_lai(lambda: setattr(o, "Rotation", math.radians(rot)))
        return _Chu(self._xong(o, a))

    def add_blockref(self, ten, p, dxfattribs=None):
        a = dict(dxfattribs or {})
        sx, sy = a.pop("xscale", 1.0), a.pop("yscale", 1.0)
        rot = math.radians(a.pop("rotation", 0) or 0)
        o = ac.goi_lai(lambda: self.ms.InsertBlock(ac.diem(*p[:2]), ten, float(sx), float(sy), 1.0, rot))
        return _DoiTuong(self._xong(o, a))

    def add_linear_dim(self, base, p1, p2, angle=0, dimstyle=None, dxfattribs=None, **_):
        o = ac.goi_lai(lambda: self.ms.AddDimRotated(ac.diem(*p1[:2]), ac.diem(*p2[:2]), ac.diem(*base[:2]),
                                                    math.radians(angle)))
        if dimstyle:
            ac.goi_lai(lambda: setattr(o, "StyleName", dimstyle))
        return _DoiTuong(self._xong(o, dxfattribs))

    def add_aligned_dim(self, p1, p2, distance=0.0, dimstyle=None, dxfattribs=None, **_):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        L = math.hypot(dx, dy) or 1
        vt = ((p1[0] + p2[0]) / 2 - dy / L * distance, (p1[1] + p2[1]) / 2 + dx / L * distance)
        o = ac.goi_lai(lambda: self.ms.AddDimAligned(ac.diem(*p1[:2]), ac.diem(*p2[:2]), ac.diem(*vt)))
        if dimstyle:
            ac.goi_lai(lambda: setattr(o, "StyleName", dimstyle))
        return _DoiTuong(self._xong(o, dxfattribs))


def nap_thu_vien(doc, ty_le=125, layer_them=(), acad=None):
    """Đưa block ký hiệu, layer, kiểu chữ và dim style PCCC vào bản vẽ đang mở."""
    import ezdxf
    import ky_hieu as kh
    import trinh_bay as tb
    lib = ezdxf.new("R2018", setup=True)
    tb.dam_bao(lib, ty_le)
    for he in ("spr", "hong"):
        for dn in (25, 32, 40, 50, 65, 80, 100, 150):
            kh.dam_bao_layer(lib, kh.layer_ong(he, dn), kh.mau_ong(dn), day=0.13 if dn < 50 else 0.18)
    for ten, mau in layer_them:
        kh.dam_bao_layer(lib, ten, mau)
    # một đối tượng mỗi block để chắc chắn định nghĩa được mang theo
    msp = lib.modelspace()
    for i, loai in enumerate(kh.KY_HIEU):
        kh.chen(msp, loai, (i * 10, 0), ty_le=1)
    tam = tempfile.mkdtemp()
    dxf, dwg = os.path.join(tam, "pccc_thu_vien.dxf"), os.path.join(tam, "pccc_thu_vien.dwg")
    lib.saveas(dxf)
    acad = acad or ac.goi_lai(lambda: doc.Application)
    hien = ac.goi_lai(lambda: acad.ActiveDocument)
    d2 = ac.goi_lai(lambda: acad.Documents.Open(dxf, False))
    ac.cho_san_sang(acad)
    ac.goi_lai(lambda: d2.SaveAs(dwg, 60))
    ac.goi_lai(lambda: d2.Close(False))
    ac.goi_lai(lambda: setattr(acad, "ActiveDocument", hien))
    ac.cho_san_sang(acad)
    doc = ac.goi_lai(lambda: acad.ActiveDocument)  # lấy lại: tham chiếu cũ có thể mất sau khi đổi cửa sổ
    ms = ac.goi_lai(lambda: doc.ModelSpace)
    br = ac.goi_lai(lambda: ms.InsertBlock(ac.diem(0, 0), dwg, 1.0, 1.0, 1.0, 0.0))
    ac.goi_lai(lambda: br.Delete())
    # dim style PCCC theo đúng tỷ lệ (biến DIM* đặt trực tiếp, chắc chắn hơn bản mang từ DXF)
    ac.dam_bao_dimstyle(doc, tb.DIMSTYLE, ty_le, 0)
    ds = ac.goi_lai(lambda: doc.DimStyles.Item(tb.DIMSTYLE))
    ac.goi_lai(lambda: doc.SetVariable("DIMTXSTY", kh.KIEU_CHU_HEP))
    ac.goi_lai(lambda: ds.CopyFrom(doc))
    return doc
