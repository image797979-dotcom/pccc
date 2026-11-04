# -*- coding: utf-8 -*-
"""Quét định kỳ Chợ Tốt: tìm tin MỚI đăng (N giờ gần nhất) rao thấp hơn giá thị trường ≥ 30 %,
mô tả không có từ khoá lỗi/hỏng, in bảng Markdown và ghi JSON. Chỉ dùng thư viện chuẩn Python 3
(không cần cài gì), tự chứa để chạy trên cloud (routine) hoặc máy cá nhân.

Dùng:
  python quet_dinh_ky.py --gio 4 --von 1200000            # tin 4 giờ gần nhất, giá ≤ 1,2 triệu, toàn quốc
  python quet_dinh_ky.py --gio 4 --von 1200000 --vung 13000   # chỉ TP HCM (12000 = Hà Nội)
  python quet_dinh_ky.py ... --lech 0.30 --ra ket_qua/dinh_ky.json
Giá thị trường = trung vị giá rao của nhóm hãng + model + dung lượng + tình trạng, tính từ cùng lần quét
(toàn quốc, 4 danh mục: điện thoại, máy tính bảng, máy ảnh/máy quay, thiết bị đeo).
"""
import argparse
import datetime as dt
import json
import os
import re
import statistics
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

API ="https://gateway.chotot.com/v1/public/ad-listing"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
           "Accept": "application/json"}
DANH_MUC = {5010: "Điện thoại", 5040: "Máy tính bảng", 5050: "Máy ảnh, máy quay", 5090: "Thiết bị đeo"}
# (danh mục, dải giá, số tin tối đa) — dải rộng hơn ngân sách để có giá thị trường của model
VIEC = [(5010, "100000-3000000", 4000), (5040, "100000-4000000", 2500), (5050, "100000-4000000", 2500), (5090, "50000-3000000", 1500)]
TINH_TRANG = {1: "Mới", 2: "Cũ", 3: "Cũ đã sửa"}
HANG = {  # mã → tên, học từ trang chi tiết Chợ Tốt (ma_tham_so.py)
    "mobile_brand": {1: "Apple", 2: "Samsung", 3: "Asus", 5: "HTC", 6: "Huawei", 7: "Lenovo", 8: "LG", 10: "Nokia", 11: "Oppo",
                     12: "Vivo", 14: "Sony", 15: "Xiaomi", 16: "Masstel", 18: "Nokia", 20: "Hãng khác", 22: "Google", 34: "Realme", 72: "Honor"},
    "tablet_brand": {1: "Apple", 2: "Asus", 3: "Lenovo", 4: "Samsung", 5: "Hãng khác", 6: "Huawei", 14: "Xiaomi", 16: "Oppo", 18: "Amazon"},
    "camera_brand": {1: "Canon", 2: "Fujifilm", 3: "Sony", 4: "Nikon", 5: "Olympus", 7: "Panasonic", 9: "Khác", 28: "Pentax"},
    "video_camera_brand": {17: "GoPro", 19: "Khác"},
    "swatch_brand": {1: "Apple", 2: "Samsung", 3: "Xiaomi", 4: "Fitbit", 6: "Garmin", 7: "Khác", 8: "Huawei", 17: "Amazfit"},
}
LOAI_MAY_ANH = {1: "Máy ảnh", 2: "Máy quay", 3: "Ống kính", 4: "Khác"}
PHIEN_BAN = {1: "Quốc tế", 2: "Khoá mạng (lock)"}
XUAT_XU = {1: "Việt Nam", 2: "Ấn Độ", 3: "Hàn Quốc", 4: "Thái Lan", 5: "Nhật Bản", 6: "Trung Quốc", 7: "Nước khác", 8: "Mỹ", 9: "Đức", 10: "Đài Loan"}

PHU_DINH = re.compile(
    r"(không|ko|k|chưa|khong|chua|chẳng)\s+(có\s+|co\s+|bị\s+|bi\s+)?"
    r"(lỗi|loi|bệnh|benh|hư|hu|hỏng|hong|sửa|sua|bung|trầy|tray|cấn|móp|mop|nứt|nut|vỡ|vo|bể|be|loang|sọc|soc|ám|lock|khoá|khóa|icloud|xước|lỗi lầm|bệnh tật|hư hỏng|qua sửa)"
    r"[^,.;\n]{0,18}"
    r"|bao\s+(test\s+)?(lỗi|loi)[^,.;\n]{0,15}|(nếu|neu)\s+(có\s+)?(lỗi|loi)[^,.;\n]{0,15}"
    r"|(có\s+)?(lỗi|loi)\s+(là\s+|la\s+)?(đổi|doi|trả|tra|hoàn|hoan)[^,.;\n]{0,10}|1\s*đổi\s*1[^,.;\n]{0,15}")
NANG = ["không lên", "ko lên", "k lên", "sập nguồn", "mất nguồn", "liệt", "chết", "xác ", "xác,", "xác.", "rã máy", "linh kiện",
        "icloud", "bypass", "treo táo", "treo logo", "chữa cháy", "hư ", "hư,", "hư.", "hỏng", "lỗi", "sọc", "nứt", "bể ", "bể,",
        "vỡ", "mất vân tay", "mất face", "loang", "lưu ảnh", "ám màn", "lúc được lúc không", "chập chờn", "bệnh", "không nhận sim",
        "mất sóng", "phồng pin", "không sạc", "ko sạc", "không nghe", "không rung", "bung keo", "khoá mạng", "khóa mạng", "bị khoá",
        "bị khóa", "nợ cước", "mất imei", "cảm ứng kém", "thay main", "lỗi main", "ngấm nước", "vô nước", "mốc", "rễ tre", "kẹt"]
NANG_KD = ["khong len", "ko len", "k len", "sap nguon", "mat nguon", "liet", "chet ", "treo tao", "treo logo", "linh kien", "icloud",
           "bypass", "soc man", "nut man", "vo man", "be man", "mat van tay", "mat face", "luu anh", "chap chon", "phong pin",
           "khong sac", "loi man", "loi cam", "loi pin", "loi loa", "loi mic", "loi sac", "loi wifi", "loi face", "loi van tay",
           "loi nguon", "bi loi", "co loi", "hu man", "hu pin", "hu loa", "hong man", "chua chay", "ngam nuoc", "mat imei"]
NHE = ["trầy", "xước", "cấn", "móp", "thay màn", "thay pin", "pin yếu", "chai pin", "đã sửa", "qua sửa chữa", "thay vỏ", "ép kính",
       "pin 7", "pin 8", "ố vàng", "hao pin", "đã thay", "pin kém", "mẻ", "rạn"]
TOT = ["nguyên zin", "zin", "chưa sửa", "chưa bung", "fullbox", "full box", "like new", "likenew", "99%", "98%", "pin 9", "pin 10",
       "còn bảo hành", "bh hãng", "mới 100", "nguyên seal", "chính hãng", "vn/a", "nguyên hộp", "không lỗi", "ko lỗi", "không trầy",
       "bao test", "đầy đủ hộp", "bao zin", "nguyên bản", "còn bh", "hoạt động tốt", "máy đẹp"]
LUA_DAO = ["chuyển khoản trước", "ck trước", "cọc trước", "đặt cọc", "chuyển cọc", "không gặp", "chỉ ship", "ship cod toàn quốc",
           "ship toàn quốc", "zalo riêng", "telegram"]
ROMAN = {"ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6"}
HAU_TO = ("pro", "plus", "max", "mini", "s", "r", "x", "ii", "iii", "ultra", "lite", "active", "classic", "fe", "se")
BO_TU = {"may", "anh", "quay", "mirrorless", "dslr", "camera", "body", "kit", "lens", "ong", "kinh", "fullbox", "like", "new", "likenew",
         "dep", "moi", "cu", "ban", "can", "gia", "re", "chinh", "hang", "kem", "tang", "zin", "full", "box", "phu", "kien", "den", "trang",
         "bac", "xam", "do", "vang", "hong", "xanh", "mau", "va", "nhat", "noi", "dia", "xach", "tay", "chup", "hinh", "the", "nho", "pin",
         "sac", "tui", "dung", "con", "bao", "hanh", "thanh", "ly", "gap", "bo", "combo", "goi", "cho", "nguoi", "co", "size", "inch",
         "mm", "f", "is", "usm", "stm", "oss", "vr", "ed", "dx", "fx"}


def log(*a):
    """Nhật ký ra stderr để stdout chỉ còn bảng kết quả (dùng được với > file.md)."""
    print(dt.datetime.now().strftime("%H:%M:%S"), *a, file=sys.stderr, flush=True)


def bo_dau(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D").lower()


def cham(subject, body, cond):
    goc = f"{subject}\n{body}".lower()
    goc_kd = bo_dau(goc)
    sach, sach_kd = PHU_DINH.sub(" ", goc), PHU_DINH.sub(" ", goc_kd)
    nang = [t for t in NANG if t in sach] + [t for t in NANG_KD if t in sach_kd]
    if re.search(r"(?<!un)\block\b", sach):
        nang.append("lock")
    nhe = [t for t in NHE if t in sach]
    tot = [t for t in TOT if t in goc]
    lua = [t for t in LUA_DAO if t in goc]
    diem = min(len(set(tot)), 3) - min(len(set(nhe)), 3) - (5 if nang else 0) + {1: 1, 3: -1}.get(cond, 0)
    ghi = "; ".join(x for x in [
        "LỖI: " + ", ".join(sorted(set(t.strip(" ,.") for t in nang)))[:80] if nang else "",
        "hao mòn: " + ", ".join(sorted(set(nhe)))[:60] if nhe else "",
        "tốt: " + ", ".join(sorted(set(tot)))[:60] if tot else ""] if x)
    return diem, ghi, bool(nang), bool(lua)


def model_tu_tieu_de(subject):
    toks = [t for t in re.findall(r"[a-z0-9][a-z0-9\-\.]*", bo_dau(subject)) if t not in BO_TU]
    for i, t in enumerate(toks):
        if not any(ch.isdigit() for ch in t):
            continue
        if re.fullmatch(r"\d+(%|mm|k|gb|tb|mp|x|inch|in|p|gh|h|w|mah|ram)", t) or re.fullmatch(r"(19|20)\d\d", t):
            continue
        model = toks[i - 1] + t if t.isdigit() and i > 0 else t
        j = i + 1
        if j < len(toks) and toks[j] in ("mark", "mk"):
            model, j = model + "mark", j + 1
        if j < len(toks) and (toks[j] in ROMAN or toks[j] in HAU_TO or (toks[j].isdigit() and len(toks[j]) == 1)):
            model += ROMAN.get(toks[j], toks[j])
        return re.sub(r"[\-\.]", "", model)
    for i, t in enumerate(toks):
        if t in ("se", "ultra") and i > 0:
            return t
    return ""


MODEL_CHUNG = {"dòng khác", "khác", "hãng khác", "other"}
BIEN_THE = {"lite", "pro", "plus", "max", "mini", "ultra", "fe", "neo", "prime", "se", "note", "promax", "redmi", "poco"}


def khoa_model(model, hang, cg):
    if not model or model.lower().strip() in MODEL_CHUNG or hang.lower() in ("hãng khác", "khác"):
        return ""
    k = re.sub(r"\s+", "", model.lower())
    if cg == 5090 and hang == "Apple":
        k = re.sub(r"^s(\d)$", r"series\1", k)
        k = {"watchse": "se"}.get(k, k)
    return k


def khac_model(subject, model):
    """Tiêu đề ghi model khác mục 'Dòng máy' người bán chọn → so giá sai."""
    if not model:
        return ""
    td, md = subject.lower(), model.lower()
    so_md, so_td = set(re.findall(r"\d+", md)), set(re.findall(r"\d+", td))
    if so_md and not (so_md & so_td):
        return "khác model"
    if "iphone" in md:
        chu_md, chu_td = set(re.findall(r"\b(xs|xr|x|se)\b", md)), set(re.findall(r"\b(xs|xr|x|se)\b", td))
        if (chu_md and not (chu_md & chu_td)) or (not so_md and re.search(r"\bip(?:hone)?\s*\d{1,2}", td)):
            return "khác model"
    if BIEN_THE & set(re.findall(r"[a-z]+", td)) - (BIEN_THE & set(re.findall(r"[a-z]+", md))):
        return "biến thể khác"
    return ""


def lay(cg, gia, toi_da, vung=None, nghi=0.3):
    ads, thay, o = [], set(), 0
    while o < toi_da:
        p = {"cg": cg, "limit": 50, "o": o, "st": "s,k", "key_param_included": "true", "price": gia}
        if vung:
            p["region_v2"] = vung
        d = None
        url = API + "?" + urllib.parse.urlencode(p)
        for lan in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40) as resp:
                    d = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                log(f"  HTTP {e.code} o={o}")
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
                log(f"  lỗi {e!r}")
            time.sleep(2 * (lan + 1))
        if not d or not d.get("ads"):
            break
        moi = 0
        for a in d["ads"]:
            if a["list_id"] not in thay:
                thay.add(a["list_id"])
                ads.append(a)
                moi += 1
        o += 50
        if moi == 0 and o > 100:
            break
        time.sleep(nghi)
    log(f"cg={cg} {DANH_MUC[cg]}: {len(ads)} tin")
    return ads


def chuan(a):
    cg = a["category"]
    params = {p["id"]: p["value"] for p in a.get("params", []) if "id" in p}
    truong_hang = {5010: "mobile_brand", 5040: "tablet_brand", 5050: "camera_brand", 5090: "swatch_brand"}[cg]
    brand = a.get(truong_hang) or a.get("video_camera_brand")
    hang = HANG.get(truong_hang, {}).get(brand) or HANG["video_camera_brand"].get(a.get("video_camera_brand") or -1) or (f"mã {brand}" if brand else "")
    model = params.get("mobile_model") or params.get("tablet_model") or ""
    if not model and cg in (5050, 5090):
        model = model_tu_tieu_de(a.get("subject", ""))
    cond = a.get("elt_condition")
    diem, ghi, nang, lua = cham(a.get("subject", ""), a.get("body", ""), cond)
    return {"list_id": a["list_id"], "cg": cg, "danh_muc": DANH_MUC[cg], "tieu_de": a.get("subject", ""), "hang": hang, "brand": brand,
            "model": model, "model_key": khoa_model(model, hang, cg), "khac_model": khac_model(a.get("subject", ""), model) if cg in (5010, 5040) else "",
            "dung_luong": params.get("mobile_capacity") or params.get("tablet_capacity") or "",
            "loai": LOAI_MAY_ANH.get(a.get("camera_type"), "") if cg == 5050 else "", "cond": TINH_TRANG.get(cond, "Cũ"),
            "phien_ban": PHIEN_BAN.get(a.get("elt_lock"), ""), "xuat_xu": XUAT_XU.get(a.get("elt_origin"), ""), "bao_hanh": params.get("elt_warranty", ""),
            "gia": a.get("price") or 0, "nguoi_ban": "Cửa hàng" if a.get("company_ad") else "Cá nhân",
            "tinh": a.get("region_name", ""), "region_v2": a.get("region_v2"), "quan": a.get("area_name", ""), "phuong": a.get("ward_name", ""),
            "list_time": a.get("list_time") or 0, "mo_ta": (a.get("body") or "")[:400], "anh": a.get("image", ""),
            "so_anh": a.get("number_of_images") or 0, "link": f"https://www.chotot.com/{a['list_id']}.htm",
            "diem": diem, "ghi_chu": ghi, "nang": nang, "lua": lua}


def khoa(r, muc):
    if not r["model_key"]:
        return None
    k = [r["cg"], r["brand"], r["model_key"], r["loai"]]
    return tuple(k + ([r["dung_luong"], r["cond"]] if muc == 1 else ["", r["cond"]] if muc == 2 else ["", ""]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gio", type=float, default=4, help="chỉ báo tin đăng trong N giờ gần nhất")
    ap.add_argument("--von", type=int, default=1200000, help="giá rao tối đa (đ)")
    ap.add_argument("--lech", type=float, default=0.30)
    ap.add_argument("--vung", type=int, default=None, help="region_v2 để lọc cơ hội (giá thị trường vẫn tính toàn quốc)")
    ap.add_argument("--toi-da-in", type=int, default=15)
    ap.add_argument("--ra", default=None, help="file JSON kết quả")
    args = ap.parse_args()
    bat_dau = dt.datetime.now()
    ads = []
    for cg, gia, toi_da in VIEC:
        ads += lay(cg, gia, toi_da)
    rows = [chuan(a) for a in ads if (a.get("price") or 0) >= 100000]
    if not rows:
        log("LỖI: không lấy được tin nào từ gateway.chotot.com (mạng bị chặn hoặc API đổi); không ghi kết quả")
        sys.exit(2)
    nhom = {}
    for muc in (1, 2, 3):
        for r in rows:
            k = khoa(r, muc)
            if k:
                nhom.setdefault(k, []).append(r["gia"])
    moc = time.time() * 1000 - args.gio * 3600 * 1000
    co_hoi, loai_loi = [], 0
    for r in rows:
        for muc, nmin in ((1, 5), (2, 5), (3, 6)):
            gias = nhom.get(khoa(r, muc), [])
            if len(gias) >= nmin:
                r["med"], r["n"] = statistics.median(gias), len(gias)
                break
        else:
            continue
        r["lech"] = (r["med"] - r["gia"]) / r["med"]
        if r["lech"] < args.lech or r["gia"] > args.von or r["list_time"] < moc:
            continue
        if args.vung and r["region_v2"] != args.vung:
            continue
        if r["cg"] == 5050 and r["loai"] in ("Ống kính", "Khác"):
            continue
        if r["nang"]:
            loai_loi += 1
            continue
        if r["khac_model"] == "khác model":
            continue
        if r["khac_model"]:
            r["ghi_chu"] = (r["khac_model"] + "; " + r["ghi_chu"]).strip("; ")
        r["loi_uoc"] = round(r["med"] * 0.92 - r["gia"], -3)
        r["uu_tien"] = ("C" if r["lech"] >= 0.6 or r["lua"] or r["nguoi_ban"] == "Cửa hàng" or r["diem"] < 0 or r["khac_model"]
                        else "A" if r["diem"] >= 1 and r["n"] >= 10 else "B")
        co_hoi.append(r)
    co_hoi.sort(key=lambda r: ({"A": 0, "B": 1, "C": 2}[r["uu_tien"]], -r["loi_uoc"]))
    print(f"\n## Quét lúc {bat_dau:%d/%m/%Y %H:%M} — {len(rows):,} tin, {len(co_hoi)} tin mới (≤ {args.gio:g} giờ) rẻ hơn thị trường ≥ {args.lech:.0%}, "
          f"giá ≤ {args.von:,} đ; {loai_loi} tin rẻ bị loại vì mô tả có lỗi/hỏng\n")
    print("| Ưu tiên | Danh mục | Tin | Giá rao | Trung vị (số tin) | Lệch | Lời ước tính | Chất lượng | Nơi bán | Đăng | Link |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in co_hoi[: args.toi_da_in]:
        tuoi = (time.time() * 1000 - r["list_time"]) / 3.6e6
        tin = f"{r['tieu_de'][:45]} ({r['model']} {r['dung_luong']} {r['cond']}{', ' + r['phien_ban'] if r['phien_ban'] else ''})"
        print(f"| {r['uu_tien']} | {r['danh_muc']} | {tin} | {r['gia']:,} | {r['med']:,.0f} ({r['n']}) | {r['lech']:.0%} | {r['loi_uoc']:,.0f} "
              f"| {r['diem']} {r['ghi_chu'][:50]} | {r['quan']}, {r['tinh']} ({r['nguoi_ban']}) | {tuoi:.1f} h | {r['link']} |")
    if args.ra:
        os.makedirs(os.path.dirname(os.path.abspath(args.ra)), exist_ok=True)
        with open(args.ra, "w", encoding="utf-8") as f:
            json.dump({"quet_luc": bat_dau.isoformat(timespec="minutes"), "so_tin": len(rows), "gio": args.gio, "von": args.von,
                       "co_hoi": co_hoi}, f, ensure_ascii=False, indent=1)
        log("ghi", args.ra)
    log(f"xong, mất {dt.datetime.now() - bat_dau}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
