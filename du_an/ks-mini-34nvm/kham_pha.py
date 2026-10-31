"""Mở bản sao bản vẽ trong AutoCAD, in thống kê xref / layer / block / layout / text để dò bản vẽ."""
import os, sys, collections
sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac
F = os.path.abspath(sys.argv[1])
acad = ac.ket_noi()
doc = None
for i in range(ac.goi_lai(lambda: acad.Documents.Count)):
    d = ac.goi_lai(lambda: acad.Documents.Item(i))
    if ac.goi_lai(lambda: d.FullName).lower() == F.lower():
        doc = d
if doc is None:
    doc = ac.goi_lai(lambda: acad.Documents.Open(F))
ac.cho_san_sang(acad)
ac.goi_lai(lambda: setattr(acad, "ActiveDocument", doc))
print("Doc", doc.Name, "INSUNITS", doc.GetVariable("INSUNITS"))
bl = doc.Blocks
for i in range(ac.goi_lai(lambda: bl.Count)):
    b = ac.goi_lai(lambda: bl.Item(i))
    if ac.goi_lai(lambda: b.IsXRef):
        print("XREF", b.Name, b.Count, b.Path)
ms = doc.ModelSpace
n = ac.goi_lai(lambda: ms.Count)
print("EXTMIN", doc.GetVariable("EXTMIN"), "EXTMAX", doc.GetVariable("EXTMAX"), "entities", n)
lay = collections.Counter(); typ = collections.Counter(); blk = collections.Counter(); txt = []
for i in range(n):
    e = ac.goi_lai(lambda: ms.Item(i))
    t = ac.goi_lai(lambda: e.ObjectName); l = ac.goi_lai(lambda: e.Layer)
    lay[l] += 1; typ[t] += 1
    if t == "AcDbBlockReference":
        blk[(ac.goi_lai(lambda: e.EffectiveName), l, tuple(round(v) for v in ac.goi_lai(lambda: e.InsertionPoint))[:2], round(ac.goi_lai(lambda: e.XScaleFactor),3))] += 1
    elif t in ("AcDbText", "AcDbMText"):
        p = e.InsertionPoint
        txt.append((e.TextString[:60], l, round(p[0]), round(p[1]), round(e.Height)))
print("TYPES", typ.most_common())
print("LAYERS"); [print(" ", k, v) for k, v in sorted(lay.items())]
print("BLOCKS"); [print(" ", k, v) for k, v in blk.most_common(80)]
lo = doc.Layouts
print("LAYOUTS", [(lo.Item(i).Name, lo.Item(i).Block.Count) for i in range(lo.Count)])
print("TEXTS", len(txt))
for t in sorted(txt, key=lambda t: (-t[3], t[2])): print(" ", t)
