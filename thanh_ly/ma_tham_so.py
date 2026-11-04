# -*- coding: utf-8 -*-
"""Học bảng mã → tên cho các trường mã số của Chợ Tốt (tình trạng, phiên bản, xuất xứ,
bảo hành, hãng, loại máy ảnh...) bằng cách đọc trang chi tiết của một ít tin đại diện.

Kết quả gộp vào du_lieu/ma_tham_so.json (đọc lại và chỉ tra mã còn thiếu).
Dùng: python ma_tham_so.py du_lieu/chotot_*.json [--toi-da 150]
"""
import argparse
import glob
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
FILE_MA = os.path.join(HERE, "du_lieu", "ma_tham_so.json")
API_CHI_TIET = "https://gateway.chotot.com/v1/public/ad-listing/{}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
TRUONG_MA = ["elt_condition", "elt_lock", "elt_origin", "elt_warranty", "mobile_brand", "tablet_brand",
             "tablet_capacity", "tablet_screen_size", "elt_cellular_type", "camera_brand", "camera_type",
             "lens_brand", "video_camera_brand", "swatch_brand", "swatch_type"]
# swatch_model, tablet_model không tra: tablet có tên trong params, đồng hồ rút model từ tiêu đề


def tai_ma():
    if os.path.exists(FILE_MA):
        with open(FILE_MA, encoding="utf-8") as f:
            return json.load(f)
    return {}


def luu_ma(ma):
    os.makedirs(os.path.dirname(FILE_MA), exist_ok=True)
    with open(FILE_MA, "w", encoding="utf-8") as f:
        json.dump(ma, f, ensure_ascii=False, indent=1, sort_keys=True)


def cap_thieu(ad, ma):
    return {(t, str(ad[t])) for t in TRUONG_MA if ad.get(t) is not None and str(ad[t]) not in ma.get(t, {})}


def hoc(ads, ma, toi_da=150, nghi=0.3):
    con_lai = set()
    for a in ads:
        con_lai |= cap_thieu(a, ma)
    print(f"cần tra {len(con_lai)} cặp (trường, mã)")
    so_goi = 0
    while con_lai and so_goi < toi_da:
        # chọn tin phủ nhiều cặp còn thiếu nhất
        tot = max(ads, key=lambda a: len(cap_thieu(a, ma) & con_lai))
        cap = cap_thieu(tot, ma) & con_lai
        if not cap:
            break
        try:
            r = requests.get(API_CHI_TIET.format(tot["list_id"]), headers=HEADERS, timeout=30)
            so_goi += 1
            d = r.json() if r.status_code == 200 else {}
        except (requests.RequestException, ValueError):
            d = {}
        ap = d.get("ad_params", {}) or {}
        for t, code in list(cap):
            ten = (ap.get(t) or {}).get("value")
            ma.setdefault(t, {})[code] = ten if ten else f"mã {code}"
            con_lai.discard((t, code))
        time.sleep(nghi)
    print(f"đã gọi {so_goi} trang chi tiết, còn thiếu {len(con_lai)} cặp")
    return ma


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--toi-da", type=int, default=150)
    args = ap.parse_args()
    ads = []
    for mau in args.files:
        for fn in glob.glob(mau):
            with open(fn, encoding="utf-8") as f:
                ads += json.load(f)["ads"]
    ma = tai_ma()
    ma = hoc(ads, ma, args.toi_da)
    luu_ma(ma)
    for t in TRUONG_MA:
        if ma.get(t):
            print(t, "→", json.dumps(dict(sorted(ma[t].items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0)), ensure_ascii=False)[:300])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
