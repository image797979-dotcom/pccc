"""Đọc khối lượng thực tế từ 4 bản vẽ PCCC (COM, chỉ đọc): đếm block, cộng chiều dài ống/cáp theo layer, theo tầng.

  python doc_ban_ve.py   ->  khoi_luong_ban_ve.json

Chỉ lấy đối tượng ở model space, layer bắt đầu bằng PCCC, nằm trong vùng mặt bằng (x < 40 m; phần sơ đồ nguyên lý
ở x >= 60 m bị bỏ). Tầng xác định theo cao độ model (mỗi tầng cách 23,44 m).
"""
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac
import pythoncom
from win32com.client import VARIANT

TANG_Y = {"HAM": 0, "TRET": 23440, "LUNG": 46880, "T2": 70320, "T3": 93760, "T4": 117200, "T5": 140640,
          "T6": 164080, "T7": 187520, "SAN_THUONG": 210960}
FILES = {"bc": "PCCC-01 BAO CHAY", "spr": "PCCC-02 SPRINKLER", "hong": "PCCC-03 HONG NUOC - BINH CHUA CHAY",
         "cs": "PCCC-04 CHIEU SANG SU CO - CHI DAN THOAT NAN"}
LAYER_DAI = ("PCCC-ONG-", "PCCC-CAP-")  # layer tính chiều dài (tim ống, cáp); PCCC-VIEN-ONG là nét viền, không tính


def tang_cua(x, y):
    if x > 40000 or x < -5000:
        return None
    for t, y0 in sorted(TANG_Y.items(), key=lambda kv: -kv[1]):
        if y >= y0 - 2500:
            if y > y0 + 22000:
                return None
            if x > 4200 and y - y0 < 7800:
                return None  # khoảng trống đông nam ngoài nhà: bảng ký hiệu (block mẫu), ghi chú
            return t
    return None


def doc(acad, ten):
    f = os.path.abspath(rf"YERSIN\{ten}.dwg")
    docs = ac.goi_lai(lambda: acad.Documents)
    doc = None
    for i in range(ac.goi_lai(lambda: docs.Count)):
        d = ac.goi_lai(lambda: docs.Item(i))
        if ac.goi_lai(lambda: d.FullName).lower() == f.lower():
            doc = d
    if doc is None:
        doc = ac.goi_lai(lambda: docs.Open(f, True))  # chỉ đọc
        ac.cho_san_sang(acad)
    ss_all = ac.goi_lai(lambda: doc.SelectionSets)
    try:
        ss_all.Item("KL").Delete()
    except Exception:
        pass
    ss = ac.goi_lai(lambda: ss_all.Add("KL"))
    ft = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_I2, [8, 67])
    fd = VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_VARIANT, ["PCCC*", 0])  # layer PCCC*, model space
    ac.goi_lai(lambda: ss.Select(5, None, None, ft, fd))
    n = ac.goi_lai(lambda: ss.Count)
    block = defaultdict(lambda: defaultdict(int))     # tầng -> tên block -> số
    dai = defaultdict(lambda: defaultdict(float))     # tầng -> layer -> mm
    for i in range(n):
        e = ac.goi_lai(lambda: ss.Item(i))
        loai = ac.goi_lai(lambda: e.ObjectName)
        if loai == "AcDbBlockReference":
            p = ac.goi_lai(lambda: e.InsertionPoint)
            t = tang_cua(p[0], p[1])
            if t:
                block[t][ac.goi_lai(lambda: e.EffectiveName)] += 1
        elif loai in ("AcDbLine", "AcDbPolyline"):
            lay = ac.goi_lai(lambda: e.Layer)
            if not lay.startswith(LAYER_DAI):
                continue
            if loai == "AcDbLine":
                p = ac.goi_lai(lambda: e.StartPoint)
            else:
                c = ac.goi_lai(lambda: e.Coordinates)
                p = (c[0], c[1])
            t = tang_cua(p[0], p[1])
            if t:
                dai[t][lay] += ac.goi_lai(lambda: e.Length)
    ac.goi_lai(lambda: ss.Delete())
    print(ten, "đối tượng PCCC:", n, flush=True)
    return {"block": {t: dict(v) for t, v in block.items()}, "dai_mm": {t: dict(v) for t, v in dai.items()}}


acad = ac.ket_noi()
kq = {he: doc(acad, ten) for he, ten in FILES.items()}
json.dump(kq, open("khoi_luong_ban_ve.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("đã lưu khoi_luong_ban_ve.json")
