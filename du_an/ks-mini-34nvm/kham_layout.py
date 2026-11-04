import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import acad_com as ac
acad = ac.ket_noi()
F = os.path.abspath(r"NVM\MBBT.dwg")
doc = None
for i in range(acad.Documents.Count):
    d = acad.Documents.Item(i); print("open:", d.FullName)
    if d.FullName.lower() == F.lower(): doc = d
doc = doc or ac.goi_lai(lambda: acad.Documents.Open(F))
ac.cho_san_sang(acad)
las = doc.Layouts
for i in range(las.Count):
    L = las.Item(i)
    if L.Name == "Model": continue
    print("==", L.Name, L.ConfigName, L.CanonicalMediaName)
    b = L.Block
    for j in range(b.Count):
        e = b.Item(j); t = e.ObjectName
        if t == "AcDbViewport":
            print("  VP", [round(v) for v in e.Center][:2], round(e.Width), round(e.Height), "scale", e.CustomScale, "tâm", [round(v) for v in e.ViewCenter][:2] if hasattr(e,'ViewCenter') else "")
        elif t == "AcDbBlockReference":
            at = []
            if e.HasAttributes:
                at = [(a.TagString, a.TextString[:30]) for a in e.GetAttributes()]
            print("  BLK", e.EffectiveName, [round(v) for v in e.InsertionPoint][:2], round(e.XScaleFactor, 3), at)
        else:
            print("  ", t, e.Layer)
