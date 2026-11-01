"""Thử các tờ thuyết minh bằng ezdxf (không cần AutoCAD), xuất PNG để soát bố cục."""
import json, sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".claude", "skills",
                                "pccc-autocad", "scripts"))
import ezdxf
from ezdxf.addons.drawing import matplotlib as dm
import ky_hieu as kh, trinh_bay as tb
import thuyet_minh as tm
TL = 125; kh.TY_LE = TL
TK = json.load(open("thiet_ke.json", encoding="utf-8"))
aq = {"C20": 18.56, "chon_Ah": 24}
for ten, f in [("quy_mo", lambda m, G: tm.to_quy_mo(m, G)), ("bc", lambda m, G: tm.to_tm_bao_chay(m, G, TK, aq)),
               ("cc", lambda m, G: tm.to_tm_chua_chay(m, G, TK)), ("cs", lambda m, G: tm.to_tm_chieu_sang(m, G, TK)),
               ("dien", lambda m, G: tm.to_tm_dien(m, G, TK))]:
    doc = ezdxf.new("R2018", setup=True); tb.dam_bao(doc, TL); kh.dam_bao_tat_ca(doc)
    msp = doc.modelspace()
    tb.khung_a3(msp, (0, 0), TL, {"so_to": "X"})
    f(msp, (0, 0))
    dm.qsave(msp, f"thu/tm_{ten}.png", dpi=110, bg="#FFFFFF")
    print("ok", ten)
