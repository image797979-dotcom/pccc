"""Mở YERSIN/MBBT_PCCC.dwg (bản sao) trong AutoCAD, nạp lại xref và báo xref nào lỗi / rỗng / lồng."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import acad_com as ac
F = os.path.abspath(r"YERSIN\MBBT_PCCC.dwg")
acad = ac.ket_noi()
# đóng bản DXF tạm đang mở (của mình) nếu có
for i in range(ac.goi_lai(lambda: acad.Documents.Count) - 1, -1, -1):
    d = ac.goi_lai(lambda: acad.Documents.Item(i))
    if ac.goi_lai(lambda: d.Name).lower() in ("mbbt_goc.dxf", "mbbt_pccc.dwg"):
        ac.goi_lai(lambda: d.Close(False))
doc = ac.goi_lai(lambda: acad.Documents.Open(F)); ac.cho_san_sang(acad)
ac.goi_lai(lambda: setattr(acad, "ActiveDocument", doc))
bl = doc.Blocks
for i in range(ac.goi_lai(lambda: bl.Count)):
    b = ac.goi_lai(lambda: bl.Item(i))
    if not ac.goi_lai(lambda: b.IsXRef): continue
    ten = ac.goi_lai(lambda: b.Name); n = ac.goi_lai(lambda: b.Count)
    duong = ac.goi_lai(lambda: b.Path)
    long = []
    for j in range(n):
        e = ac.goi_lai(lambda: b.Item(j))
        if ac.goi_lai(lambda: e.ObjectName) == "AcDbBlockReference":
            try:
                bb = doc.Blocks.Item(ac.goi_lai(lambda: e.Name))
                if bb.IsXRef: long.append(bb.Name)
            except Exception: pass
    print(f"{'RONG ' if n == 0 else 'OK   '}{ten:28s} {n:6d}  {duong}  {'long:' + ','.join(long) if long else ''}", flush=True)
ac.goi_lai(lambda: acad.ZoomExtents())
