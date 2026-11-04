"""Mở bản sao MBBT_PCCC.dwg trong AutoCAD và in thống kê layer / block / layout để dò bản vẽ."""
import os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import acad_com as ac
F = os.path.abspath("MBBT_PCCC.dwg")
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
ms = doc.ModelSpace
n = ac.goi_lai(lambda: ms.Count)
print("Doc", doc.Name, "INSUNITS", doc.GetVariable("INSUNITS"), "entities", n)
print("EXTMIN", doc.GetVariable("EXTMIN"), "EXTMAX", doc.GetVariable("EXTMAX"))
lay = collections.Counter(); typ = collections.Counter(); blk = collections.Counter(); txt = []
for i in range(n):
    e = ac.goi_lai(lambda: ms.Item(i))
    t = ac.goi_lai(lambda: e.ObjectName); l = ac.goi_lai(lambda: e.Layer)
    lay[l] += 1; typ[t] += 1
    if t == "AcDbBlockReference":
        blk[(ac.goi_lai(lambda: e.EffectiveName), l, tuple(round(v) for v in ac.goi_lai(lambda: e.InsertionPoint)), round(ac.goi_lai(lambda: e.XScaleFactor),3))] += 1
    elif t in ("AcDbText", "AcDbMText"):
        p = e.InsertionPoint
        txt.append((e.TextString[:60], l, round(p[0]), round(p[1])))
print("TYPES", typ.most_common())
print("LAYERS"); [print(" ", k, v) for k, v in sorted(lay.items())]
print("BLOCKS"); [print(" ", k, v) for k, v in blk.most_common(60)]
print("LAYOUTS", [doc.Layouts.Item(i).Name for i in range(doc.Layouts.Count)])
print("TEXTS", len(txt))
for t in txt: print(" ", t)
