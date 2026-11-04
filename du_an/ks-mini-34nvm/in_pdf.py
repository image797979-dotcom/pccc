"""In các layout của bản vẽ đang mở ra PDF (DWG To PDF.pc3), mỗi layout một file.
  python in_pdf.py thu_muc_ra [tên layout ...]   (bỏ trống = tất cả)"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import acad_com as ac
ra = os.path.abspath(sys.argv[1]); os.makedirs(ra, exist_ok=True)
chon = sys.argv[2:]
acad = ac.ket_noi(); doc = ac.goi_lai(lambda: acad.ActiveDocument)
ac.goi_lai(lambda: doc.SetVariable("BACKGROUNDPLOT", 0))
las = ac.goi_lai(lambda: doc.Layouts)
ten_ds = [ac.goi_lai(lambda: las.Item(i)).Name for i in range(ac.goi_lai(lambda: las.Count))]
for ten in ten_ds:
    if ten == "Model" or (chon and ten not in chon):
        continue
    lay = ac.goi_lai(lambda: las.Item(ten))
    ac.goi_lai(lambda: setattr(doc, "ActiveLayout", lay)); ac.cho_san_sang(acad)
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    lay = ac.goi_lai(lambda: doc.ActiveLayout)
    f = os.path.join(ra, ten.replace("/", "-") + ".pdf")
    ok = ac.goi_lai(lambda: doc.Plot.PlotToFile(f, "DWG To PDF.pc3"))
    print(ten, ok, os.path.exists(f), flush=True)
