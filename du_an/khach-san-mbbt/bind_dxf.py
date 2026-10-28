"""Mở bản sao YERSIN/MBBT_BIND.dwg, bind toàn bộ xref (kiểu Bind, layer có tiền tố) rồi lưu DXF để dò phòng."""
import os, sys
sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac
acad = ac.ket_noi()
F = os.path.abspath(r"YERSIN\MBBT_BIND.dwg")
doc = None
for i in range(ac.goi_lai(lambda: acad.Documents.Count)):
    d = ac.goi_lai(lambda: acad.Documents.Item(i))
    if ac.goi_lai(lambda: d.FullName).lower() == F.lower():
        doc = d
doc = doc or ac.goi_lai(lambda: acad.Documents.Open(F))
ac.cho_san_sang(acad)
bl = ac.goi_lai(lambda: doc.Blocks)
xr = [ac.goi_lai(lambda: bl.Item(i)) for i in range(ac.goi_lai(lambda: bl.Count))]
xr = [b for b in xr if ac.goi_lai(lambda: b.IsXRef)]
for b in xr:
    ten = ac.goi_lai(lambda: b.Name)
    ac.goi_lai(lambda: b.Bind(True), so_lan=10)
    print("bind", ten, flush=True)
ac.goi_lai(lambda: doc.SaveAs(os.path.abspath("MBBT_bind.dxf"), 61), so_lan=5)
ac.goi_lai(lambda: doc.Close(False))
print("ok")
