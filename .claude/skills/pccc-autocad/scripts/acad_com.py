"""Tiện ích điều khiển AutoCAD qua COM (Windows + AutoCAD bản đầy đủ, không dùng được với LT).

AutoCAD hay từ chối lệnh ("Call was rejected by callee") khi đang khởi động hoặc đang bận,
nên mọi lời gọi COM nên đi qua goi_lai().
"""
import time

import pythoncom
import win32com.client
from win32com.client import VARIANT


def diem(x, y, z=0.0):
    """Toạ độ 3D dạng mảng double mà COM của AutoCAD yêu cầu."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (float(x), float(y), float(z)))


def mang_2d(cac_diem):
    """Danh sách điểm 2D phẳng (x1, y1, x2, y2, ...) cho AddLightWeightPolyline."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [float(v) for p in cac_diem for v in p])


def goi_lai(ham, so_lan=60):
    """Gọi ham(); nếu AutoCAD báo bận thì chờ 1 giây rồi thử lại."""
    for i in range(so_lan):
        try:
            return ham()
        except pythoncom.com_error:
            if i == so_lan - 1:
                raise
            time.sleep(1)


def cho_san_sang(acad, toi_da=120):
    """Chờ tới khi AutoCAD rảnh (không còn khởi động hoặc chạy lệnh)."""
    for _ in range(toi_da):
        try:
            if acad.GetAcadState().IsQuiescent:
                return
        except (pythoncom.com_error, AttributeError):
            # Khi đang bận, AutoCAD có thể trả về đối tượng trạng thái chưa đầy đủ
            pass
        time.sleep(1)


def ket_noi():
    """Lấy AutoCAD đang chạy (hoặc khởi động mới) và đợi sẵn sàng."""
    acad = win32com.client.Dispatch("AutoCAD.Application")
    goi_lai(lambda: setattr(acad, "Visible", True))
    cho_san_sang(acad)
    return acad


def dam_bao_layer(doc, ten, mau):
    """Tạo layer nếu chưa có, trả về đối tượng layer."""
    layer = goi_lai(lambda: doc.Layers.Add(ten))  # Add trả về layer có sẵn nếu trùng tên
    goi_lai(lambda: setattr(layer, "Color", mau))
    return layer


def dam_bao_block_tron(doc, ten, ban_kinh, chu=None):
    """Tạo block ký hiệu đơn giản (hình tròn + chữ tuỳ chọn) nếu bản vẽ chưa có."""
    try:
        return goi_lai(lambda: doc.Blocks.Item(ten), so_lan=1)
    except pythoncom.com_error:
        pass
    blk = goi_lai(lambda: doc.Blocks.Add(diem(0, 0), ten))
    goi_lai(lambda: blk.AddCircle(diem(0, 0), ban_kinh))
    if chu:
        t = goi_lai(lambda: blk.AddText(chu, diem(-ban_kinh * 0.5, -ban_kinh * 0.35), ban_kinh * 0.7))
        goi_lai(lambda: setattr(t, "Layer", "0"))
    return blk


def dam_bao_dimstyle(doc, ten, dimscale, dimdec=0):
    """Tạo (hoặc cập nhật) dim style và đặt làm style hiện hành.

    Cách làm qua COM: đặt biến DIM* cho bản vẽ, rồi CopyFrom(doc) để style nhận các giá trị đó.
    Biến kiểu số nguyên của AutoCAD phải truyền dạng short (VT_I2), nếu không sẽ báo sai tham số.
    """
    i2 = lambda v: VARIANT(pythoncom.VT_I2, v)
    r8 = lambda v: VARIANT(pythoncom.VT_R8, float(v))
    for ten_bien, gia_tri in [
        ("DIMSCALE", r8(dimscale)), ("DIMTXT", r8(2.5)), ("DIMASZ", r8(1.5)),
        ("DIMEXO", r8(1.0)), ("DIMEXE", r8(1.0)), ("DIMGAP", r8(0.8)),
        ("DIMTAD", i2(1)), ("DIMDEC", i2(dimdec)), ("DIMTIX", i2(0)),
    ]:
        goi_lai(lambda: doc.SetVariable(ten_bien, gia_tri))
    goi_lai(lambda: doc.SetVariable("DIMBLK", "_ARCHTICK"))
    ds = goi_lai(lambda: doc.DimStyles.Add(ten))
    goi_lai(lambda: ds.CopyFrom(doc))
    goi_lai(lambda: setattr(doc, "ActiveDimStyle", ds))
    return ds


def polyline_kin_tren_layer(doc, ten_layer):
    """Trả về [(handle, [(x, y), ...]), ...] cho mọi polyline kín trên layer (Model space)."""
    ms = goi_lai(lambda: doc.ModelSpace)
    ket_qua = []
    for i in range(goi_lai(lambda: ms.Count)):
        e = goi_lai(lambda: ms.Item(i))
        if goi_lai(lambda: e.ObjectName) != "AcDbPolyline":
            continue
        if goi_lai(lambda: e.Layer).upper() != ten_layer.upper() or not goi_lai(lambda: e.Closed):
            continue
        toa_do = list(goi_lai(lambda: e.Coordinates))
        diem_2d = [(toa_do[k], toa_do[k + 1]) for k in range(0, len(toa_do), 2)]
        ket_qua.append((goi_lai(lambda: e.Handle), diem_2d))
    return ket_qua
