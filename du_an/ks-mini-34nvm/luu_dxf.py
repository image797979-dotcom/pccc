"""Mở bản sao DWG trong AutoCAD, lưu bản DXF (R2018) để đọc bằng ezdxf."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import acad_com as ac
acad = ac.ket_noi()
for src, dst in zip(sys.argv[1::2], sys.argv[2::2]):
    F = os.path.abspath(src)
    doc = None
    for i in range(ac.goi_lai(lambda: acad.Documents.Count)):
        d = ac.goi_lai(lambda: acad.Documents.Item(i))
        if ac.goi_lai(lambda: d.FullName).lower() == F.lower(): doc = d
    doc = doc or ac.goi_lai(lambda: acad.Documents.Open(F))
    ac.cho_san_sang(acad)
    # SaveAs đổi tên document -> mở lại bản DWG sau
    ac.goi_lai(lambda: doc.SaveAs(os.path.abspath(dst), 61), so_lan=5)
    print("luu", dst, flush=True)
