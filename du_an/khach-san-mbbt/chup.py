"""Xuất ảnh vùng một tầng của bản vẽ đang mở (WMF qua COM Export → PNG) để kiểm tra.
  python chup.py T3 ra.png [x0 y0 x1 y1 (toạ độ tầng)]"""
import os, sys, time
sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac
from win32com.client import VARIANT
import pythoncom
TANG_Y = {"HAM": 0, "TRET": 23440, "LUNG": 46880, "T2": 70320, "T3": 93760, "T4": 117200, "T5": 140640,
          "T6": 164080, "T7": 187520, "SAN_THUONG": 210960}
t, ra = sys.argv[1], os.path.abspath(sys.argv[2])
x0, y0, x1, y1 = map(float, sys.argv[3:7]) if len(sys.argv) > 6 else (-3000, -2000, 25000, 21500)
y = TANG_Y.get(t, 0)
acad = ac.ket_noi(); doc = ac.goi_lai(lambda: acad.ActiveDocument)
ac.goi_lai(lambda: setattr(doc, "ActiveSpace", 1)); print("zoom", flush=True); ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(x0, y + y0), ac.diem(x1, y + y1)))
ss = ac.goi_lai(lambda: doc.SelectionSets)
try: ss.Item("CHUP").Delete()
except Exception: pass
s = ac.goi_lai(lambda: ss.Add("CHUP"))
ac.goi_lai(lambda: s.Select(1, ac.diem(x0, y + y0), ac.diem(x1, y + y1)))  # crossing
print("chọn", s.Count, flush=True); wmf = ra[:-4] + ".wmf"
if os.path.exists(wmf): os.remove(wmf)
ac.goi_lai(lambda: doc.Export(wmf[:-4], "WMF", s))
ac.goi_lai(lambda: s.Delete())
print("xuất xong", os.path.exists(wmf), flush=True); from PIL import Image
im = Image.open(wmf); im.load(dpi=200) if hasattr(im, "load") else None
im = im.convert("RGB"); im.save(ra); print("ok", im.size)
