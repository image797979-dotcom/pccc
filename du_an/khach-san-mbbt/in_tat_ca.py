"""In mọi layout của 4 file PCCC (đang mở trong AutoCAD) ra PDF: PDF/<tên file>/<layout>.pdf"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import acad_com as ac
acad = ac.ket_noi()
ac.goi_lai(lambda: acad.ActiveDocument.SetVariable("BACKGROUNDPLOT", 0))
docs = ac.goi_lai(lambda: acad.Documents)
for i in range(ac.goi_lai(lambda: docs.Count)):
    d = ac.goi_lai(lambda: docs.Item(i))
    ten_f = ac.goi_lai(lambda: d.Name)
    if not ten_f.startswith("PCCC-0") or "__moi" in ten_f:
        continue
    ac.goi_lai(lambda: setattr(acad, "ActiveDocument", d)); ac.cho_san_sang(acad)
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    ra = os.path.abspath(os.path.join("PDF", ten_f[:-4])); os.makedirs(ra, exist_ok=True)
    las = ac.goi_lai(lambda: doc.Layouts)
    ds = sorted(ac.goi_lai(lambda: las.Item(k)).Name for k in range(ac.goi_lai(lambda: las.Count)))
    for ten in ds:
        if ten == "Model":
            continue
        lay = ac.goi_lai(lambda: las.Item(ten))
        ac.goi_lai(lambda: setattr(doc, "ActiveLayout", lay)); ac.cho_san_sang(acad)
        doc = ac.goi_lai(lambda: acad.ActiveDocument)
        f = os.path.join(ra, ten + ".pdf")
        ok = ac.goi_lai(lambda: doc.Plot.PlotToFile(f, "DWG To PDF.pc3"))
        print(ten_f, "|", ten, ok, flush=True)
    ac.goi_lai(lambda: setattr(doc, "ActiveSpace", 1))
    ac.goi_lai(lambda: doc.Save())
