"""Mở DXF bằng AutoCAD và lưu thành DWG (AutoCAD 2018 trở lên)."""
import sys
sys.path.insert(0, sys.argv[3])
import acad_com as ac

nguon, dich = sys.argv[1], sys.argv[2]
acad = ac.ket_noi()
doc = ac.goi_lai(lambda: acad.Documents.Open(nguon, False))
ac.cho_san_sang(acad)
for kieu in (64, 60):  # ac2018_dwg, ac2013_dwg
    try:
        ac.goi_lai(lambda: doc.SaveAs(dich, kieu), so_lan=5)
        print("Đã lưu DWG, kiểu", kieu)
        break
    except Exception as e:
        print("SaveAs kiểu", kieu, "lỗi:", e)
ac.goi_lai(lambda: doc.Close(False))
