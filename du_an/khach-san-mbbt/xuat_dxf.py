"""Lưu bản sao DXF (R2018) của MBBT_PCCC.dwg để đọc bằng ezdxf, rồi trả bản vẽ đang mở về file DWG."""
import os, sys
sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac
acad = ac.ket_noi()
doc = ac.goi_lai(lambda: acad.ActiveDocument)
assert doc.Name == "MBBT_PCCC.dwg", doc.Name
dwg = ac.goi_lai(lambda: doc.FullName)
ac.goi_lai(lambda: doc.SaveAs(os.path.abspath("MBBT_goc.dxf"), 65))
ac.goi_lai(lambda: doc.SaveAs(dwg, 60))
print("ok", ac.goi_lai(lambda: doc.FullName))
