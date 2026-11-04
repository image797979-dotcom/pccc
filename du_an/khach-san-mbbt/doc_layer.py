import ezdxf, collections, pickle, sys
doc = ezdxf.readfile("MBBT_bind.dxf")
msp = doc.modelspace()
print(collections.Counter(e.dxftype() for e in msp).most_common())
for ins in msp.query("INSERT"):
    n = ins.dxf.name
    if not (n.startswith("CT-") or n.startswith("SP ") or n.startswith("XR_")): continue
    blk = doc.blocks[n]
    c = collections.Counter((e.dxf.layer.split("$0$")[-1], e.dxftype()) for e in blk)
    print(n, tuple(round(v) for v in ins.dxf.insert), len(blk), c.most_common(12))
