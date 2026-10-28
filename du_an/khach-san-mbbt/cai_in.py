"""Thiết lập in A3 cho mọi layout của bản vẽ đang mở: DWG To PDF, ISO full bleed A3, cửa sổ = khung A3
(-795, 889)–(-375, 1186), tỷ lệ 1:1, acad.ctb (giữ màu)."""
import sys
sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac
import pythoncom
from win32com.client import VARIANT


def cai_dat(acad, doc):
    las = ac.goi_lai(lambda: doc.Layouts)
    for i in range(ac.goi_lai(lambda: las.Count)):
        lay = ac.goi_lai(lambda: las.Item(i))
        if ac.goi_lai(lambda: lay.Name) == "Model":
            continue
        ac.goi_lai(lambda: setattr(lay, "ConfigName", "DWG To PDF.pc3"))
        ac.goi_lai(lambda: lay.RefreshPlotDeviceInfo())
        ac.goi_lai(lambda: setattr(lay, "CanonicalMediaName", "ISO_full_bleed_A3_(420.00_x_297.00_MM)"))
        ac.goi_lai(lambda: setattr(lay, "PaperUnits", 1))
        ac.goi_lai(lambda: setattr(lay, "PlotRotation", 0))
        p1 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (-795.0, 889.0))
        p2 = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (-375.0, 1186.0))
        ac.goi_lai(lambda: lay.SetWindowToPlot(p1, p2))
        ac.goi_lai(lambda: setattr(lay, "PlotType", 4))  # acWindow
        ac.goi_lai(lambda: setattr(lay, "UseStandardScale", True))
        ac.goi_lai(lambda: setattr(lay, "StandardScale", 16))  # 1:1
        ac.goi_lai(lambda: setattr(lay, "CenterPlot", True))
        try:
            ac.goi_lai(lambda: setattr(lay, "StyleSheet", "acad.ctb"), so_lan=2)
        except Exception:
            pass
        ac.goi_lai(lambda: setattr(lay, "PlotWithPlotStyles", True))


if __name__ == "__main__":
    acad = ac.ket_noi()
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    cai_dat(acad, doc)
    ac.goi_lai(lambda: doc.Save())
    print("đã đặt in A3 cho", doc.Name)
