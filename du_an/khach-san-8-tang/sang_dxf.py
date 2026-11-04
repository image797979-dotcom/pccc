"""Mở bản sao DWG bằng AutoCAD (COM) và lưu sang DXF để phân tích bằng ezdxf."""
import sys
sys.path.insert(0, sys.argv[3])
import acad_com as ac

nguon, dich = sys.argv[1], sys.argv[2]
acad = ac.ket_noi()
docs = ac.goi_lai(lambda: acad.Documents)
doc = next((d for d in (docs.Item(i) for i in range(docs.Count)) if d.FullName.lower() == nguon.lower()), None)
doc = doc or ac.goi_lai(lambda: acad.Documents.Open(nguon, False))
ac.cho_san_sang(acad)
for kieu in (61, 13):  # ac2013_dxf, ac2000_dxf
    try:
        ac.goi_lai(lambda: doc.SaveAs(dich, kieu), so_lan=5)
        print("Đã lưu DXF, kiểu", kieu)
        break
    except Exception as e:
        print("SaveAs kiểu", kieu, "lỗi:", e)
ac.goi_lai(lambda: doc.Close(False))
