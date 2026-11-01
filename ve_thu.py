"""Vẽ thử trong AutoCAD qua COM: khung chữ nhật, hình tròn, chữ và kích thước.

Chạy: python ve_thu.py
Script mở (hoặc khởi động) AutoCAD, tạo bản vẽ mới rồi vẽ vào đó.
"""
import time

import pythoncom
import win32com.client
from win32com.client import VARIANT


def diem(x, y, z=0.0):
    """Toạ độ 3D dạng mảng double mà COM của AutoCAD yêu cầu."""
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (float(x), float(y), float(z)))


def mang_2d(cac_diem):
    """Danh sách điểm 2D phẳng (x1, y1, x2, y2, ...) cho LWPolyline."""
    phang = [float(v) for p in cac_diem for v in p]
    return VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, phang)


def goi_lai(ham, so_lan=60):
    """AutoCAD trả lỗi 'Call was rejected' khi đang bận, nên chờ rồi thử lại."""
    for i in range(so_lan):
        try:
            return ham()
        except pythoncom.com_error:
            if i == so_lan - 1:
                raise
            time.sleep(1)


def cho_san_sang(acad, toi_da=120):
    """Chờ AutoCAD rảnh (không còn đang chạy lệnh/khởi động)."""
    for _ in range(toi_da):
        try:
            if acad.GetAcadState().IsQuiescent:
                return
        except pythoncom.com_error:
            pass
        time.sleep(1)


def main():
    acad = win32com.client.Dispatch("AutoCAD.Application")
    goi_lai(lambda: setattr(acad, "Visible", True))
    cho_san_sang(acad)
    doc = goi_lai(lambda: acad.Documents.Add())
    cho_san_sang(acad)
    ms = goi_lai(lambda: doc.ModelSpace)

    # Layer riêng cho hình vẽ thử
    layer = goi_lai(lambda: doc.Layers.Add("CLAUDE_TEST"))
    goi_lai(lambda: setattr(layer, "Color", 4))  # cyan
    goi_lai(lambda: setattr(doc, "ActiveLayer", layer))

    # Khung chữ nhật 6000 x 4000 (mm)
    khung = goi_lai(lambda: ms.AddLightWeightPolyline(
        mang_2d([(0, 0), (6000, 0), (6000, 4000), (0, 4000)])))
    goi_lai(lambda: setattr(khung, "Closed", True))

    # Hình tròn ở tâm, bán kính 1000
    goi_lai(lambda: ms.AddCircle(diem(3000, 2000), 1000))

    # Hai đường chéo
    goi_lai(lambda: ms.AddLine(diem(0, 0), diem(6000, 4000)))
    goi_lai(lambda: ms.AddLine(diem(0, 4000), diem(6000, 0)))

    # Chữ
    goi_lai(lambda: ms.AddText("Claude ve thu - AutoCAD 2024", diem(0, 4300), 250))

    # Kích thước cạnh dưới và cạnh trái
    goi_lai(lambda: ms.AddDimAligned(diem(0, 0), diem(6000, 0), diem(3000, -600)))
    goi_lai(lambda: ms.AddDimAligned(diem(0, 0), diem(0, 4000), diem(-600, 2000)))

    goi_lai(lambda: acad.ZoomExtents())
    goi_lai(lambda: doc.Regen(1))  # acAllViewports

    print(f"Đã vẽ xong vào bản vẽ: {goi_lai(lambda: doc.Name)}")
    print(f"Số đối tượng trong Model: {goi_lai(lambda: ms.Count)}")
    dien_tich = goi_lai(lambda: khung.Area) / 1e6
    chu_vi = goi_lai(lambda: khung.Length) / 1e3
    print(f"Diện tích khung: {dien_tich:.2f} m2, chu vi: {chu_vi:.2f} m")


if __name__ == "__main__":
    main()
