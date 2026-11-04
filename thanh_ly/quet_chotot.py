# -*- coding: utf-8 -*-
"""Quét tin rao đồ công nghệ trên Chợ Tốt qua API công khai, lưu JSON thô.

Mặc định quét toàn quốc 4 danh mục: điện thoại (5010), máy tính bảng (5040),
máy ảnh/máy quay (5050), thiết bị đeo (5090). Mỗi trang 50 tin, API trả tối đa
10.000 tin cho một bộ lọc, nên điện thoại được chia 2 dải giá.

Dùng:
  python quet_chotot.py                      # quét đầy đủ → du_lieu/chotot_<giờ>.json
  python quet_chotot.py --gio 3 --vung 13000 # chỉ tin đăng 3 giờ gần nhất ở TP HCM (dùng cho quét định kỳ)
  python quet_chotot.py --toi-da 1000        # thử nhanh
Mã vùng region_v2: 13000 TP HCM, 12000 Hà Nội, 3017 Đà Nẵng (bỏ trống = toàn quốc).
"""
import argparse
import datetime as dt
import json
import os
import sys
import time

import requests

API = "https://gateway.chotot.com/v1/public/ad-listing"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
    "Accept": "application/json",
}
DANH_MUC = {5010: "Điện thoại", 5040: "Máy tính bảng", 5050: "Máy ảnh, Máy quay", 5090: "Thiết bị đeo thông minh"}
# (danh mục, dải giá, số tin tối đa) — dải giá rộng hơn ngân sách để tính giá thị trường của từng model
VIEC_MAC_DINH = [
    (5010, "100000-1500000", 8000),
    (5010, "1500000-6000000", 5000),
    (5040, "100000-8000000", 5000),
    (5050, "100000-8000000", 5000),
    (5090, "50000-5000000", 3000),
]
BO_TRUONG = {
    "image_thumbnails", "videos", "avatar", "seller_info", "cta_buttons", "pty_characteristics",
    "special_display_images", "inspection_images", "label_campaigns", "ad_features", "ad_labels",
    "business_days", "specific_service_offered", "fee_type", "location",
}
HERE = os.path.dirname(os.path.abspath(__file__))


def log(*a):
    print(dt.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def lay_trang(params, lan_thu=4):
    for lan in range(lan_thu):
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=40)
            if r.status_code == 200:
                return r.json()
            log(f"  HTTP {r.status_code} tại o={params.get('o')}, thử lại")
        except (requests.RequestException, ValueError) as e:
            log(f"  lỗi {e!r}, thử lại")
        time.sleep(2 * (lan + 1))
    return None


def quet(cg, gia=None, vung=None, toi_da=5000, gio=None, ca_nhan=False, nghi=0.35):
    """Trả về danh sách tin (mới nhất trước). gio=N: dừng khi gặp tin cũ hơn N giờ."""
    ads, da_thay, o = [], set(), 0
    moc_ms = None
    if gio:
        moc_ms = (time.time() - gio * 3600) * 1000
    tong_api = None
    while o < toi_da:
        p = {"cg": cg, "limit": 50, "o": o, "st": "s,k", "key_param_included": "true"}
        if gia:
            p["price"] = gia
        if vung:
            p["region_v2"] = vung
        if ca_nhan:
            p["f"] = "p"
        d = lay_trang(p)
        if not d:
            log(f"  bỏ qua cg={cg} từ o={o} (API không trả)")
            break
        tong_api = d.get("total")
        lo = d.get("ads", [])
        if not lo:
            break
        moi, qua_cu = 0, False
        for a in lo:
            lid = a.get("list_id")
            if lid in da_thay:
                continue
            if moc_ms and a.get("list_time", 0) < moc_ms:
                qua_cu = True
                break
            da_thay.add(lid)
            ads.append({k: v for k, v in a.items() if k not in BO_TRUONG})
            moi += 1
        o += 50
        if o % 500 == 0:
            log(f"  cg={cg} {gia or ''} {vung or 'toàn quốc'}: {len(ads)} tin (API total {tong_api})")
        if qua_cu or (moi == 0 and o > 100):
            break
        time.sleep(nghi)
    log(f"xong cg={cg} ({DANH_MUC.get(cg, cg)}) {gia or ''} {vung or 'toàn quốc'}: {len(ads)} tin, API total {tong_api}")
    return ads


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vung", type=int, default=None, help="region_v2, ví dụ 13000 = TP HCM; bỏ trống = toàn quốc")
    ap.add_argument("--gio", type=float, default=None, help="chỉ lấy tin đăng trong N giờ gần nhất")
    ap.add_argument("--toi-da", type=int, default=None, help="số tin tối đa mỗi việc (ghi đè mặc định)")
    ap.add_argument("--danh-muc", type=int, nargs="*", default=None, help="chỉ quét các mã danh mục này")
    ap.add_argument("--ca-nhan", action="store_true", help="chỉ tin của người bán cá nhân")
    ap.add_argument("--ra", default=None, help="file JSON đầu ra")
    args = ap.parse_args()

    viec = VIEC_MAC_DINH
    if args.gio:  # quét định kỳ: chỉ dải giá mua được, một việc mỗi danh mục
        viec = [(5010, "100000-2500000", 3000), (5040, "100000-3000000", 2000),
                (5050, "100000-3000000", 2000), (5090, "50000-2500000", 1500)]
    if args.danh_muc:
        viec = [v for v in viec if v[0] in args.danh_muc]
    bat_dau = dt.datetime.now()
    tat_ca, thay = [], set()
    for cg, gia, toi_da in viec:
        for a in quet(cg, gia, args.vung, args.toi_da or toi_da, args.gio, args.ca_nhan):
            if a["list_id"] not in thay:
                thay.add(a["list_id"])
                tat_ca.append(a)
    ra = args.ra or os.path.join(HERE, "du_lieu", f"chotot_{bat_dau:%Y%m%d_%H%M}.json")
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    with open(ra, "w", encoding="utf-8") as f:
        json.dump({"quet_luc": bat_dau.isoformat(timespec="seconds"), "vung": args.vung, "gio": args.gio,
                   "viec": viec, "so_tin": len(tat_ca), "ads": tat_ca}, f, ensure_ascii=False)
    co_params = sum(1 for a in tat_ca if a.get("params"))
    log(f"Lưu {len(tat_ca)} tin → {ra} ({co_params} tin có params tên model); mất {dt.datetime.now() - bat_dau}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
