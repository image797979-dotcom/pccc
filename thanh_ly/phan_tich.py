# -*- coding: utf-8 -*-
"""Phân tích tin rao Chợ Tốt đã quét: chuẩn hoá model, tính giá thị trường (trung vị theo nhóm
hãng / model / dung lượng / tình trạng), lọc tin rao thấp hơn thị trường ≥ 30 %, chấm chất lượng
theo mô tả, tải ảnh và xuất Excel để người dùng chọn mua.

Dùng:
  python phan_tich.py du_lieu/chotot_20261104_0803.json
  python phan_tich.py "du_lieu/chotot_*.json" --von 1000000 --lech 0.30 --ra ket_qua/so_sanh_gia.xlsx
  python phan_tich.py ... --vung "Hồ Chí Minh"      # chỉ lấy cơ hội ở một tỉnh/thành
  python phan_tich.py ... --khong-anh               # không tải ảnh (nhanh)
"""
import argparse
import datetime as dt
import glob
import io
import json
import os
import re
import statistics
import sys
import time
import unicodedata

import requests
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from PIL import Image as PILImage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ma_tham_so import tai_ma  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DANH_MUC = {5010: "Điện thoại", 5040: "Máy tính bảng", 5050: "Máy ảnh, máy quay", 5090: "Thiết bị đeo"}
TINH_TRANG = {1: "Mới", 2: "Cũ", 3: "Cũ đã sửa"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
# ký tự điều khiển và surrogate lẻ: Excel/openpyxl không nhận
LAM_SACH = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff]")

# ----------------------------------------------------------------- từ khoá chất lượng
# Phủ định cần xoá trước khi tìm lỗi: "không lỗi", "chưa sửa", "bao test lỗi", "lỗi đổi"...
PHU_DINH = re.compile(
    r"(không|ko|k|chưa|chẳng|hok|hông|0|khong|chua)\s+(có\s+|co\s+|bị\s+|bi\s+)?"
    r"(lỗi|loi|bệnh|benh|hư|hu|hỏng|hong|sửa|sua|bung|trầy|tray|cấn|móp|mop|nứt|nut|vỡ|vo|bể|be|loang|lưu ảnh|sọc|soc|ám|lock|khoá|khóa|icloud|xước|rớt|rơi|va đập|lỗi lầm|bệnh tật|hư hỏng|qua sửa)"
    r"[^,.;\n]{0,18}"
    r"|bao\s+(test\s+)?(lỗi|loi)[^,.;\n]{0,15}"
    r"|(nếu|neu)\s+(có\s+)?(lỗi|loi)[^,.;\n]{0,15}"
    r"|(có\s+)?(lỗi|loi)\s+(là\s+|la\s+)?(đổi|doi|trả|tra|hoàn|hoan)[^,.;\n]{0,10}"
    r"|1\s*đổi\s*1[^,.;\n]{0,15}"
)
NANG = ["không lên", "ko lên", "k lên", "sập nguồn", "mất nguồn", "liệt", "chết", "xác ", "xác,", "xác.", "xác\n",
        "rã máy", "linh kiện", "icloud", "bypass", "treo táo", "treo logo", "chữa cháy", "hư ", "hư,", "hư.", "hỏng",
        "lỗi", "sọc", "nứt", "bể ", "bể,", "bể.", "vỡ", "mất vân tay", "mất face", "loang", "lưu ảnh", "ám màn",
        "lúc được lúc không", "chập chờn", "bệnh", "không nhận sim", "mất sóng", "phồng pin", "không sạc", "ko sạc",
        "không nghe", "không rung", "mất âm", "bung keo", "không bật", "khoá mạng", "khóa mạng", "bị khoá", "bị khóa",
        "nợ cước", "mất imei", "đen màn", "màn đen", "không hiển thị", "cảm ứng kém", "cảm ứng lỗi", "liệt cảm",
        "thay main", "main lỗi", "lỗi main", "ngấm nước", "vô nước", "rớt nước", "không nhận sạc", "mất wifi",
        "mất bluetooth", "không lấy nét", "lỗi lấy nét", "mốc", "rễ tre", "bụi cảm biến", "shutter cao", "kẹt"]
NANG_KO_DAU = ["khong len", "ko len", "k len", "sap nguon", "mat nguon", "liet", "chet ", "chet,", "treo tao",
               "treo logo", "linh kien", "icloud", "bypass", "soc man", "nut man", "vo man", "be man", "mat van tay",
               "mat face", "luu anh", "chap chon", "khong nhan sim", "phong pin", "khong sac", "ko sac", "loi man",
               "loi cam", "loi pin", "loi loa", "loi mic", "loi sac", "loi wifi", "loi face", "loi van tay",
               "loi nguon", "bi loi", "co loi", "loi nhe", "loi nho", "hu man", "hu pin", "hu loa", "hu cam",
               "hong man", "chua chay", "ngam nuoc", "vo nuoc", "mat imei", "hu main", "loi main"]
NHE = ["trầy", "xước", "cấn", "móp", "thay màn", "thay pin", "pin yếu", "chai pin", "đã sửa", "qua sửa chữa",
       "thay vỏ", "thay kính", "ép kính", "độ vỏ", "thay cam", "thay loa", "pin 7", "pin 8", "ố vàng", "ố màn",
       "màn ố", "ngả màu", "bong tróc", "hao pin", "sụt pin", "đã thay", "pin kém", "pin tụt", "nhám", "mẻ",
       "rạn", "lỏng", "mờ", "bay sơn", "xuống cấp"]
NHE_KO_DAU = ["tray", "xuoc", "mop", "thay man", "thay pin", "pin yeu", "chai pin", "da sua", "ep kinh", "thay vo",
              "hao pin", "sut pin", "pin kem"]
TOT = ["nguyên zin", "zin", "chưa sửa", "chưa bung", "chưa qua sửa", "fullbox", "full box", "like new", "likenew",
       "99%", "98%", "97%", "pin 9", "pin 10", "còn bảo hành", "bh hãng", "bảo hành hãng", "mới 100", "nguyên seal",
       "chính hãng", "vn/a", "nguyên hộp", "đẹp keng", "không lỗi", "ko lỗi", "không trầy", "không bệnh", "bao test",
       "đầy đủ hộp", "bao xài", "bao zin", "nguyên bản", "còn bh", "bh đến", "bảo hành đến", "nguyên tem",
       "chưa tháo", "hoạt động tốt", "mọi chức năng", "đầy đủ chức năng", "full chức năng", "còn mới",
       "máy đẹp", "đẹp 99", "đẹp 98", "shutter thấp", "ít shot"]
LUA_DAO = ["chuyển khoản trước", "ck trước", "cọc trước", "đặt cọc", "chuyển cọc", "không gặp", "chỉ ship",
           "ship cod toàn quốc", "ship toàn quốc", "zalo riêng", "inbox zalo", "telegram"]
NGUON_GOC = [("xách tay", "xách tay"), ("chính hãng", "chính hãng"), ("vn/a", "VN/A chính hãng"),
             ("ll/a", "LL/A (Mỹ)"), ("za/a", "ZA/A (Singapore)"), ("j/a", "J/A (Nhật)"), ("kh/a", "KH/A (Hàn)"),
             ("trả bảo hành", "máy trả bảo hành"), ("tbh", "máy trả bảo hành"), ("hàng công ty", "hàng công ty"),
             ("nội địa", "nội địa"), ("hàng nhật", "hàng Nhật"), ("nhật bãi", "Nhật bãi"), ("hàng mỹ", "hàng Mỹ"),
             ("quốc tế", "bản quốc tế"), ("bản lock", "bản lock"), ("mở khoá", "đã mở khoá"), ("refurbished", "refurbished"),
             ("cpo", "CPO"), ("tân trang", "tân trang"), ("dựng", "có thể là máy dựng")]
ROMAN = {"ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6"}
HAU_TO = ("pro", "plus", "max", "mini", "s", "r", "x", "ii", "iii", "ultra", "lite", "active", "classic", "fe", "se")
BO_TU_MAY_ANH = {"may", "anh", "quay", "mirrorless", "dslr", "camera", "body", "kit", "lens", "ong", "kinh", "fullbox",
                 "like", "new", "likenew", "dep", "moi", "cu", "ban", "can", "gia", "re", "chinh", "hang", "kem",
                 "tang", "zin", "full", "box", "phu", "kien", "den", "trang", "bac", "xam", "do", "vang", "hong",
                 "xanh", "mau", "va", "nhat", "noi", "dia", "xach", "tay", "chup", "hinh", "the", "nho", "pin", "sac",
                 "tui", "dung", "con", "bao", "hanh", "thanh", "ly", "gap", "bo", "combo", "goi", "cho", "nguoi",
                 "co", "size", "inch", "mm", "f", "is", "usm", "stm", "oss", "vr", "ed", "dx", "fx"}


def bo_dau(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def chua(text, tu_khoa):
    return [t for t in tu_khoa if t in text]


def cham_chat_luong(subject, body, cond):
    """Trả về (điểm, ghi chú, loại_nặng, cảnh báo lừa đảo)."""
    goc = f"{subject}\n{body}".lower()
    goc_kd = bo_dau(goc)
    tot = chua(goc, TOT)
    sach = PHU_DINH.sub(" ", goc)
    sach_kd = PHU_DINH.sub(" ", goc_kd)
    nang = chua(sach, NANG) + chua(sach_kd, NANG_KO_DAU)
    if re.search(r"(?<!un)\block\b", sach) and "lock" not in nang:
        nang.append("lock")
    nhe = chua(sach, NHE) + chua(sach_kd, NHE_KO_DAU)
    lua = chua(goc, LUA_DAO)
    diem = min(len(set(tot)), 3) - min(len(set(nhe)), 3) - (5 if nang else 0)
    diem += {1: 1, 3: -1}.get(cond, 0)
    ghi = []
    if nang:
        ghi.append("LỖI/HỎNG: " + ", ".join(sorted(set(x.strip(" ,.\n") for x in nang)))[:120])
    if nhe:
        ghi.append("hao mòn: " + ", ".join(sorted(set(x.strip() for x in nhe)))[:80])
    if tot:
        ghi.append("điểm cộng: " + ", ".join(sorted(set(tot)))[:90])
    return diem, "; ".join(ghi), bool(nang), lua


def nguon_goc_tu_mo_ta(subject, body):
    t = f"{subject} {body}".lower()
    ra = []
    for k, v in NGUON_GOC:
        if k in t and v not in ra:
            ra.append(v)
    return ", ".join(ra)


def model_tu_tieu_de(subject):
    """Rút khoá model từ tiêu đề (máy ảnh, đồng hồ... khi không có trường model)."""
    toks = re.findall(r"[a-z0-9][a-z0-9\-\.]*", bo_dau(subject))
    toks = [t for t in toks if t not in BO_TU_MAY_ANH]
    for i, t in enumerate(toks):
        if not any(ch.isdigit() for ch in t):
            continue
        if re.fullmatch(r"\d+(%|mm|k|gb|tb|mp|x|inch|in|p|gh|h|w|mah|ram)", t) or re.fullmatch(r"(19|20)\d\d", t):
            continue
        model = t
        if t.isdigit() and i > 0:
            model = toks[i - 1] + t
        j = i + 1
        if j < len(toks) and toks[j] in ("mark", "mk"):
            model += "mark"
            j += 1
        if j < len(toks) and (toks[j] in ROMAN or toks[j] in HAU_TO or (toks[j].isdigit() and len(toks[j]) == 1)):
            model += ROMAN.get(toks[j], toks[j])
        return re.sub(r"[\-\.]", "", model)
    # không có số: đồng hồ "Watch SE", "Watch Ultra"...
    for i, t in enumerate(toks):
        if t in ("se", "ultra") and i > 0:
            return t
    return ""


MODEL_CHUNG = {"dòng khác", "khác", "hãng khác", "dong khac", "khac", "other"}
BIEN_THE = {"lite", "pro", "plus", "max", "mini", "ultra", "fe", "neo", "prime", "se", "note", "promax", "redmi", "poco"}


def khoa_model(model, hang, cg):
    """Khoá nhóm từ tên model; '' nếu model/hãng chung chung (không so giá được)."""
    if not model or model.lower().strip() in MODEL_CHUNG or hang.lower() in ("hãng khác", "khác"):
        return ""
    k = re.sub(r"\s+", "", model.lower())
    if cg == 5090 and hang == "Apple":
        k = re.sub(r"^s(\d)$", r"series\1", k)
        k = {"watchse": "se", "applewatchse": "se"}.get(k, k)
    return k


def khac_model(subject, model):
    """Phát hiện tiêu đề ghi model khác mục 'Dòng máy' người bán chọn (chọn sai → so giá sai)."""
    if not model:
        return ""
    td, md = subject.lower(), model.lower()
    so_md, so_td = set(re.findall(r"\d+", md)), set(re.findall(r"\d+", td))
    if so_md and not (so_md & so_td):
        return f"khác model: tiêu đề không có số '{'/'.join(sorted(so_md))}' của model đã chọn"
    if "iphone" in md:
        chu_md = set(re.findall(r"\b(xs|xr|x|se)\b", md))
        chu_td = set(re.findall(r"\b(xs|xr|x|se)\b", td))
        if chu_md and not (chu_md & chu_td):
            return "khác model: tiêu đề không khớp iPhone đã chọn"
        if not so_md and re.search(r"\bip(?:hone)?\s*\d{1,2}", td):
            return "khác model: tiêu đề ghi iPhone số, mục chọn là bản chữ"
    bt_td = BIEN_THE & set(re.findall(r"[a-z]+", td))
    bt_md = BIEN_THE & set(re.findall(r"[a-z]+", md))
    if bt_td - bt_md:
        return "biến thể khác: tiêu đề có '" + ", ".join(sorted(bt_td - bt_md)) + "' nhưng model đã chọn không có"
    return ""


def chuan_hoa(ad, ma):
    cg = ad.get("category")
    params = {p["id"]: p["value"] for p in ad.get("params", []) if "id" in p}

    def ten(truong):
        code = ad.get(truong)
        if code is None:
            return ""
        return ma.get(truong, {}).get(str(code), f"mã {code}")

    hang = ten("mobile_brand") or ten("tablet_brand") or ten("camera_brand") or ten("video_camera_brand") or ten("swatch_brand")
    model = params.get("mobile_model") or params.get("tablet_model") or ""
    if not model and cg in (5050, 5090):
        model = model_tu_tieu_de(ad.get("subject", ""))
    if not model:
        model = ten("tablet_model") or ten("swatch_model")
        if model.lower() in ("khác", "dòng khác") or model.startswith("mã "):
            model = ""
    dung_luong = params.get("mobile_capacity") or params.get("tablet_capacity") or ten("tablet_capacity") or ""
    cond = ad.get("elt_condition")
    body = ad.get("body") or ""
    subject = ad.get("subject") or ""
    diem, ghi_chu, nang, lua = cham_chat_luong(subject, body, cond)
    list_time = ad.get("list_time") or 0
    dang_luc = dt.datetime.fromtimestamp(list_time / 1000) if list_time else None
    loai_may_anh = ten("camera_type") if cg == 5050 else (ten("swatch_type") if cg == 5090 else "")
    brand_code = ad.get("mobile_brand") or ad.get("tablet_brand") or ad.get("camera_brand") or ad.get("video_camera_brand") or ad.get("swatch_brand")
    r = {
        "list_id": ad.get("list_id"), "danh_muc": DANH_MUC.get(cg, str(cg)), "cg": cg,
        "tieu_de": subject, "hang": hang, "brand_code": brand_code, "model": model,
        "model_key": khoa_model(model, hang, cg), "khac_model": khac_model(subject, model) if cg in (5010, 5040) else "",
        "dung_luong": dung_luong, "loai": loai_may_anh,
        "cond": cond, "tinh_trang": ten("elt_condition") or "", "tinh_trang_ngan": TINH_TRANG.get(cond, "Cũ"),
        "phien_ban": ten("elt_lock"), "xuat_xu": ten("elt_origin"), "bao_hanh": params.get("elt_warranty") or ten("elt_warranty"),
        "nguon_goc_mo_ta": nguon_goc_tu_mo_ta(subject, body),
        "gia": ad.get("price") or 0, "gia_khong_hop_le": bool(ad.get("is_price_not_valid")),
        "nguoi_ban": "Cửa hàng" if ad.get("company_ad") else "Cá nhân", "ten_nguoi_ban": ad.get("account_name") or "",
        "tinh": ad.get("region_name") or "", "quan": ad.get("area_name") or "", "phuong": ad.get("ward_name") or "",
        "dang_luc": dang_luc, "mo_ta": body, "anh": ad.get("image") or (ad.get("images") or [""])[0], "so_anh": ad.get("number_of_images") or 0,
        "link": f"https://www.chotot.com/{ad.get('list_id')}.htm", "diem": diem, "ghi_chu": ghi_chu, "nang": nang, "lua": lua,
    }
    return {k: (LAM_SACH.sub("", v) if isinstance(v, str) else v) for k, v in r.items()}


# ----------------------------------------------------------------- giá thị trường
def thong_ke(gias):
    gias = sorted(gias)
    n = len(gias)
    q = statistics.quantiles(gias, n=4) if n >= 2 else [gias[0]] * 3
    return {"n": n, "min": gias[0], "p25": q[0], "med": statistics.median(gias), "p75": q[2], "max": gias[-1]}


def khoa_nhom(r, muc):
    """Khoá nhóm theo mức chi tiết: 1 = hãng+model+dung lượng+tình trạng, 2 = bỏ dung lượng, 3 = bỏ tình trạng."""
    if not r["model_key"]:
        return None
    k = [r["cg"], r["brand_code"], r["model_key"]]
    if r["cg"] in (5050, 5090):
        k.append(r["loai"])
    if muc == 1:
        k += [r["dung_luong"], r["tinh_trang_ngan"]]
    elif muc == 2:
        k += ["", r["tinh_trang_ngan"]]
    else:
        k += ["", ""]
    return tuple(k)


def gan_gia_thi_truong(rows, n_toi_thieu=5):
    hop_le = [r for r in rows if r["gia"] >= 100000 and not r["gia_khong_hop_le"]]
    nhom = {}
    for muc in (1, 2, 3):
        for r in hop_le:
            k = khoa_nhom(r, muc)
            if k:
                nhom.setdefault(k, []).append(r["gia"])
    tk = {k: thong_ke(v) for k, v in nhom.items()}
    for r in rows:
        r.update({"med": None, "n_nhom": 0, "p25": None, "p75": None, "muc_nhom": "", "lech": None})
        for muc, nmin in ((1, n_toi_thieu), (2, n_toi_thieu), (3, n_toi_thieu + 1)):
            k = khoa_nhom(r, muc)
            s = tk.get(k)
            if s and s["n"] >= nmin:
                r.update({"med": s["med"], "n_nhom": s["n"], "p25": s["p25"], "p75": s["p75"],
                          "muc_nhom": {1: "model+dung lượng+tình trạng", 2: "model+tình trạng", 3: "model"}[muc]})
                break
        if r["med"] and r["gia"] > 0:
            r["lech"] = (r["med"] - r["gia"]) / r["med"]
    bang = []
    for k, s in tk.items():
        cg, brand, model_key, *rest = k
        if s["n"] < 3:
            continue
        bang.append({"k": k, "cg": cg, "brand_code": brand, "model_key": model_key, **s,
                     "dung_luong": rest[-2], "tinh_trang": rest[-1], "loai": rest[0] if len(rest) == 3 else ""})
    return bang


def thanh_khoan(n):
    return "Rất cao" if n >= 60 else "Cao" if n >= 25 else "Trung bình" if n >= 10 else "Thấp"


def uu_tien(r, von, tuoi_gio):
    if r["nang"]:
        return "Loại"
    if r["lech"] is not None and r["lech"] >= 0.6 or r.get("khac_model"):
        return "C"
    if r["lua"] or r["nguoi_ban"] == "Cửa hàng" or r["diem"] < 0:
        return "C"
    if r["diem"] >= 1 and tuoi_gio <= 48 and r["n_nhom"] >= 10:
        return "A"
    return "B"


def canh_bao(r, tuoi_gio):
    cb = []
    if r["lech"] is not None and r["lech"] >= 0.6:
        cb.append("giá quá thấp (≥60 %): nghi lừa đảo hoặc máy lỗi chưa khai")
    if r.get("khac_model"):
        cb.append(r["khac_model"])
    if r["lua"]:
        cb.append("mô tả yêu cầu cọc/chuyển khoản/ship: chỉ giao dịch trực tiếp")
    if r["nguoi_ban"] == "Cửa hàng":
        cb.append("tin cửa hàng: giá có thể là giá 1 phụ kiện/1 cấu hình thấp")
    if tuoi_gio > 72:
        cb.append("tin đã đăng > 3 ngày, có thể đã bán")
    if r["n_nhom"] < 10:
        cb.append("ít tin so sánh, giá thị trường kém chắc chắn")
    if r["so_anh"] <= 1:
        cb.append("chỉ 1 ảnh")
    if not r["phien_ban"] and r["cg"] in (5010, 5040) and r["hang"] == "Apple":
        cb.append("chưa rõ quốc tế/lock")
    return "; ".join(cb)


# ----------------------------------------------------------------- ảnh
def tai_anh(rows, thu_muc, kich=118):
    os.makedirs(thu_muc, exist_ok=True)
    for r in rows:
        if not r["anh"]:
            r["anh_file"] = None
            continue
        fn = os.path.join(thu_muc, f"{r['list_id']}.jpg")
        r["anh_file"] = fn if os.path.exists(fn) else None
        if r["anh_file"]:
            continue
        try:
            resp = requests.get(r["anh"], headers=HEADERS, timeout=20)
            im = PILImage.open(io.BytesIO(resp.content)).convert("RGB")
            im.thumbnail((kich, kich))
            im.save(fn, "JPEG", quality=80)
            r["anh_file"] = fn
        except Exception as e:  # noqa: BLE001
            print("  không tải được ảnh", r["list_id"], e)
            r["anh_file"] = None
        time.sleep(0.15)


# ----------------------------------------------------------------- Excel
FONT = "Arial"
F_CHU = Font(name=FONT, size=10)
F_DAM = Font(name=FONT, size=10, bold=True)
F_TIEU_DE = Font(name=FONT, size=14, bold=True)
F_DAU = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_LINK = Font(name=FONT, size=10, color="0563C1", underline="single")
F_VAO = Font(name=FONT, size=10, color="0000FF")
TO_DAU = PatternFill("solid", fgColor="1F4E78")
TO_A = PatternFill("solid", fgColor="C6EFCE")
TO_B = PatternFill("solid", fgColor="FFEB9C")
TO_C = PatternFill("solid", fgColor="FFC7CE")
TO_VAO = PatternFill("solid", fgColor="FFFF99")
VIEN = Border(*(Side(style="thin", color="BFBFBF"),) * 4)
GIUA = Alignment(horizontal="center", vertical="center", wrap_text=True)
TRAI = Alignment(horizontal="left", vertical="top", wrap_text=True)
PHAI = Alignment(horizontal="right", vertical="center")
VND = "#,##0"
PCT = "0%"


def ghi_dau(ws, hang, cot_dau):
    for i, t in enumerate(cot_dau, 1):
        c = ws.cell(row=hang, column=i, value=t)
        c.font, c.fill, c.alignment, c.border = F_DAU, TO_DAU, GIUA, VIEN
    ws.row_dimensions[hang].height = 32


def dat_rong(ws, rong):
    for i, w in enumerate(rong, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def sheet_co_hoi(wb, ten, rows, tieu_de, mo_ta, co_anh):
    ws = wb.create_sheet(ten)
    ws["A1"] = tieu_de
    ws["A1"].font = F_TIEU_DE
    ws["A2"] = mo_ta
    ws["A2"].font = F_CHU
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:T2")
    ws.row_dimensions[2].height = 45
    cot = ["Ưu tiên", "Ảnh", "Danh mục", "Tên tin", "Hãng", "Model", "Dung lượng", "Tình trạng", "Phiên bản",
           "Xuất xứ (khai báo)", "Nguồn gốc theo mô tả", "Bảo hành", "Giá rao (đ)", "Giá thị trường trung vị (đ)",
           "Số tin so sánh", "Thanh khoản", "Lệch giá", "Giá bán dự kiến (đ)", "Lợi nhuận dự kiến (đ)", "Tỷ suất",
           "Điểm chất lượng", "Ghi chú chất lượng", "Cảnh báo", "Người bán", "Tỉnh/TP", "Quận/Huyện", "Phường/Xã",
           "Đăng lúc", "Tuổi tin (giờ)", "Mô tả", "Nguồn", "Link"]
    HANG_DAU = 4
    ghi_dau(ws, HANG_DAU, cot)
    dat_rong(ws, [8, 17, 13, 34, 10, 18, 10, 11, 10, 12, 18, 12, 13, 15, 8, 11, 8, 14, 14, 8, 8, 40, 40, 10, 14, 15, 14, 16, 8, 70, 9, 12])
    bay_gio = dt.datetime.now()
    for i, r in enumerate(rows):
        h = HANG_DAU + 1 + i
        tuoi = (bay_gio - r["dang_luc"]).total_seconds() / 3600 if r["dang_luc"] else None
        gia_tri = [r["uu_tien"], None, r["danh_muc"], r["tieu_de"], r["hang"], r["model"], r["dung_luong"],
                   r["tinh_trang"] or r["tinh_trang_ngan"], r["phien_ban"], r["xuat_xu"], r["nguon_goc_mo_ta"], r["bao_hanh"],
                   r["gia"], r["med"], r["n_nhom"], thanh_khoan(r["n_nhom"]),
                   f"=(N{h}-M{h})/N{h}", f"=ROUND(N{h}*'Tổng quan'!$C$7,-4)", f"=R{h}-M{h}", f"=S{h}/M{h}",
                   r["diem"], r["ghi_chu"], r["canh_bao"], r["nguoi_ban"], r["tinh"], r["quan"], r["phuong"],
                   r["dang_luc"], round(tuoi, 1) if tuoi is not None else None, r["mo_ta"][:1500], "Chợ Tốt", "Mở tin"]
        for j, v in enumerate(gia_tri, 1):
            c = ws.cell(row=h, column=j, value=v)
            c.font, c.border = F_CHU, VIEN
            c.alignment = TRAI if j in (4, 11, 22, 23, 30) else GIUA
        for col in ("M", "N", "R", "S"):
            ws[f"{col}{h}"].number_format = VND
        for col in ("Q", "T"):
            ws[f"{col}{h}"].number_format = PCT
        ws[f"AB{h}"].number_format = "dd/mm/yyyy hh:mm"
        lk = ws[f"AF{h}"]
        lk.hyperlink, lk.font = r["link"], F_LINK
        ws[f"A{h}"].fill = {"A": TO_A, "B": TO_B, "C": TO_C}.get(r["uu_tien"], TO_C)
        ws[f"A{h}"].font = F_DAM
        ws.row_dimensions[h].height = 92 if co_anh else 60
        if co_anh and r.get("anh_file"):
            ws.add_image(XLImage(r["anh_file"]), f"B{h}")
    cuoi = HANG_DAU + len(rows)
    ws.freeze_panes = f"E{HANG_DAU + 1}"
    if rows:
        ws.auto_filter.ref = f"A{HANG_DAU}:{get_column_letter(len(cot))}{cuoi}"
    return ws


def sheet_gia_thi_truong(wb, bang, ten_hang):
    ws = wb.create_sheet("Giá thị trường")
    ws["A1"] = "Giá thị trường theo nhóm (trung vị của các tin rao đang hiển thị trên Chợ Tốt, toàn quốc)"
    ws["A1"].font = F_TIEU_DE
    ws["A2"] = ("Nhóm = danh mục + hãng + model (+ dung lượng, tình trạng). Số tin càng nhiều thì giá càng đáng tin và "
                "món đó càng dễ bán lại (thanh khoản). P25/P75 là mức giá mà 25 % và 75 % số tin rao nằm dưới.")
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A2:L2")
    ws.row_dimensions[2].height = 30
    cot = ["Danh mục", "Hãng", "Model", "Loại", "Dung lượng", "Tình trạng", "Số tin", "Thanh khoản",
           "Thấp nhất (đ)", "P25 (đ)", "Trung vị (đ)", "P75 (đ)", "Cao nhất (đ)", "Ngưỡng mua ≤ −30 % (đ)"]
    ghi_dau(ws, 4, cot)
    dat_rong(ws, [14, 11, 24, 14, 10, 11, 8, 11, 13, 13, 13, 13, 13, 16])
    bang = sorted(bang, key=lambda b: (-b["n"], b["cg"], b["model_key"]))
    for i, b in enumerate(bang):
        h = 5 + i
        vals = [DANH_MUC.get(b["cg"], b["cg"]), ten_hang(b["cg"], b["brand_code"]), b["model_key"], b["loai"],
                b["dung_luong"], b["tinh_trang"], b["n"], thanh_khoan(b["n"]), b["min"], b["p25"], b["med"], b["p75"],
                b["max"], f"=ROUND(K{h}*(1-'Tổng quan'!$C$6),-4)"]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=h, column=j, value=v)
            c.font, c.border, c.alignment = F_CHU, VIEN, (GIUA if j <= 8 else PHAI)
        for col in "IJKLMN":
            ws[f"{col}{h}"].number_format = VND
    ws.freeze_panes = "D5"
    if bang:
        ws.auto_filter.ref = f"A4:N{4 + len(bang)}"


def sheet_thanh_khoan(wb, bang, ten_hang, von):
    ws = wb.create_sheet("Thanh khoản")
    ws["A1"] = "Model dễ bán lại trong tầm vốn: nhóm có nhiều tin rao nhất với giá trung vị dưới 3 lần vốn"
    ws["A1"].font = F_TIEU_DE
    ws["A2"] = ("Nhiều tin rao = nhiều người mua bán = dễ thoát hàng nhanh. Dùng bảng này để quyết định nên săn model nào, "
                "rồi đối chiếu với sheet 'Cơ hội mua ngay'.")
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A2:J2")
    cot = ["Danh mục", "Hãng", "Model", "Dung lượng", "Tình trạng", "Số tin", "Thanh khoản", "Trung vị (đ)", "P25 (đ)",
           "Giá nên mua để lời 30 % khi bán ở P25 (đ)"]
    ghi_dau(ws, 4, cot)
    dat_rong(ws, [14, 11, 24, 10, 11, 8, 11, 13, 13, 20])
    loc = [b for b in bang if b["med"] <= von * 3 and b["tinh_trang"] and (b["dung_luong"] != "" or b["cg"] in (5050, 5090))]
    loc = sorted(loc, key=lambda b: -b["n"])[:120]
    for i, b in enumerate(loc):
        h = 5 + i
        vals = [DANH_MUC.get(b["cg"], b["cg"]), ten_hang(b["cg"], b["brand_code"]), b["model_key"], b["dung_luong"],
                b["tinh_trang"], b["n"], thanh_khoan(b["n"]), b["med"], b["p25"], f"=ROUND(I{h}/1.3,-4)"]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=h, column=j, value=v)
            c.font, c.border, c.alignment = F_CHU, VIEN, (GIUA if j <= 7 else PHAI)
        for col in "HIJ":
            ws[f"{col}{h}"].number_format = VND
    ws.freeze_panes = "D5"
    if loc:
        ws.auto_filter.ref = f"A4:J{4 + len(loc)}"


def sheet_toan_bo(wb, rows):
    ws = wb.create_sheet("Toàn bộ tin")
    cot = ["Danh mục", "Tên tin", "Hãng", "Model", "Dung lượng", "Tình trạng", "Phiên bản", "Xuất xứ", "Bảo hành",
           "Giá rao (đ)", "Trung vị nhóm (đ)", "Số tin nhóm", "Lệch giá", "Điểm chất lượng", "Lỗi/hỏng", "Người bán",
           "Tỉnh/TP", "Quận/Huyện", "Đăng lúc", "Mô tả (rút gọn)", "Link"]
    ghi_dau(ws, 1, cot)
    dat_rong(ws, [13, 36, 10, 18, 9, 10, 9, 10, 11, 12, 13, 8, 8, 8, 8, 9, 14, 14, 15, 60, 34])
    for i, r in enumerate(rows):
        h = 2 + i
        vals = [r["danh_muc"], r["tieu_de"], r["hang"], r["model"], r["dung_luong"], r["tinh_trang_ngan"], r["phien_ban"],
                r["xuat_xu"], r["bao_hanh"], r["gia"], r["med"], r["n_nhom"] or None, r["lech"], r["diem"],
                "x" if r["nang"] else "", r["nguoi_ban"], r["tinh"], r["quan"], r["dang_luc"],
                re.sub(r"\s+", " ", r["mo_ta"])[:250], r["link"]]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=h, column=j, value=v)
            c.font = F_CHU
        ws[f"J{h}"].number_format = ws[f"K{h}"].number_format = VND
        ws[f"M{h}"].number_format = PCT
        ws[f"S{h}"].number_format = "dd/mm/yyyy hh:mm"
    ws.freeze_panes = "C2"
    if rows:
        ws.auto_filter.ref = f"A1:U{1 + len(rows)}"


def sheet_ke_hoach(wb, muc_tieu=5000000):
    ws = wb.create_sheet("Kế hoạch 4 ngày")
    dat_rong(ws, [34, 16, 16, 16, 16, 16, 16])
    ws["A1"] = "Bài toán vốn: 1 triệu → 5 triệu trong 4 ngày"
    ws["A1"].font = F_TIEU_DE
    dong = [("Vốn ban đầu (đ)", "='Tổng quan'!C5", VND, False),
            ("Mục tiêu (đ)", muc_tieu, VND, True),
            ("Số vòng mua–bán làm được trong 4 ngày (mỗi vòng 1–2 ngày)", 3, "0", True),
            ("Tỷ suất lợi nhuận mỗi vòng CẦN có để đạt mục tiêu", "=(B4/B3)^(1/B5)-1", "0.0%", False),
            ("Tỷ suất mỗi vòng THƯỜNG đạt: mua rẻ hơn thị trường theo ngưỡng, bán ở hệ số bán nhanh",
             "=1/(1-'Tổng quan'!C6)*'Tổng quan'!C7-1", "0.0%", False),
            ("Vốn sau 4 ngày với tỷ suất thường đạt (đ)", "=B3*(1+B7)^B5", VND, False)]
    for i, (nhan, gt, fmt, vao) in enumerate(dong):
        h = 3 + i
        a = ws.cell(row=h, column=1, value=nhan)
        a.font, a.border, a.alignment = F_CHU, VIEN, Alignment(wrap_text=True, vertical="center")
        b = ws.cell(row=h, column=2, value=gt)
        b.number_format, b.border = fmt, VIEN
        if vao:
            b.fill, b.font = TO_VAO, F_VAO
        else:
            b.font = F_CHU
        ws.row_dimensions[h].height = 30
    ws["A10"] = "Bảng kịch bản: vốn cuối kỳ (đ) = vốn × (1 + tỷ suất mỗi vòng)^số vòng"
    ws["A10"].font = F_DAM
    ws["A11"] = "Tỷ suất mỗi vòng ↓ / số vòng →"
    ws["A11"].font = F_DAM
    for j, k in enumerate(range(1, 7), 2):
        c = ws.cell(row=11, column=j, value=k)
        c.font, c.border, c.alignment = F_DAM, VIEN, GIUA
    for i, r in enumerate((0.15, 0.25, 0.35, 0.5, 0.75, 1.0)):
        h = 12 + i
        a = ws.cell(row=h, column=1, value=r)
        a.number_format, a.font, a.border = "0%", F_CHU, VIEN
        for j in range(2, 8):
            col = get_column_letter(j)
            c = ws.cell(row=h, column=j, value=f"=$B$3*(1+$A{h})^{col}$11")
            c.number_format, c.font, c.border = VND, F_CHU, VIEN
    ws["A19"] = "Kết luận số học"
    ws["A19"].font = F_DAM
    ket_luan = [
        "Để 1 triệu thành 5 triệu trong 3 vòng cần lời ~71 % mỗi vòng, 4 vòng cần ~50 %, 2 vòng cần ~124 %. "
        "Mua rẻ hơn thị trường 30 % rồi bán ở 92 % giá thị trường chỉ cho ~31 % mỗi vòng → sau 3 vòng được ~2,3 triệu.",
        "Vì vậy mục tiêu 5 triệu trong 4 ngày là KHÔNG thực tế với vốn 1 triệu nếu không chấp nhận rủi ro rất cao "
        "(mua máy lỗi, hàng trộm cắp, bị lừa). Mục tiêu hợp lý: 1,5–2,5 triệu sau 4 ngày; hoà vốn là kết quả phổ biến với người mới.",
        "Cách tăng tỷ suất thật: (1) chỉ mua tin cá nhân vừa đăng (< 24 giờ) đang cần bán gấp, trả giá thêm 10–15 %; "
        "(2) chọn model thanh khoản 'Cao/Rất cao' để bán trong 1 ngày; (3) đăng bán ở nhiều nơi cùng lúc (Chợ Tốt + nhóm Facebook địa phương); "
        "(4) gộp phụ kiện (sạc, hộp) để bán được giá; (5) xem máy trực tiếp, tuyệt đối không cọc/chuyển khoản trước.",
        "Kiểm tra bắt buộc khi mua: IMEI (*#06#) khớp hộp và không bị báo mất; iPhone kiểm tra iCloud đã đăng xuất, "
        "Android kiểm tra tài khoản Google; test cảm ứng, camera, loa, mic, sạc, sim, pin; hỏi hoá đơn/giấy tờ nếu có. "
        "Mua đồ trộm cắp là vi phạm pháp luật dù không biết.",
    ]
    for i, t in enumerate(ket_luan):
        c = ws.cell(row=20 + i, column=1, value=t)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.font = F_CHU
        ws.merge_cells(start_row=20 + i, start_column=1, end_row=20 + i, end_column=7)
        ws.row_dimensions[20 + i].height = 48
    ws["A25"] = "Lịch 4 ngày đề xuất"
    ws["A25"].font = F_DAM
    lich = [
        ("Ngày 1 (hôm nay)", "Chọn 3–5 tin ưu tiên A ở gần nhà từ sheet 'Cơ hội mua ngay' (model thanh khoản Cao/Rất cao), gọi hỏi còn hàng, hẹn xem máy. "
                             "Mua 1 món tốt nhất ≤ 1 triệu sau khi test. Chụp ảnh đẹp, đăng bán ngay tối cùng ngày trên Chợ Tốt và nhóm Facebook địa phương ở mức ≈ 92–95 % giá trung vị."),
        ("Ngày 2", "Trả lời khách, hẹn giao dịch trực tiếp nơi công cộng. Bán xong, tái đầu tư toàn bộ vốn vào 1–2 món từ sheet 'Cơ hội mua ngay' hoặc 'Cơ hội vòng sau' (nếu vốn đã > 1,2 triệu). "
                   "Chạy lại quét để bắt tin mới (tin rẻ hết trong vài giờ)."),
        ("Ngày 3", "Vòng 2: bán món thứ hai; nếu chưa bán được, giảm 5 % mỗi 12 giờ thay vì ôm hàng. Mua vòng 3 nếu còn thời gian giao dịch trong ngày 4."),
        ("Ngày 4", "Chốt bán tất cả hàng tồn trước tối, kể cả hoà vốn; không mua mới sau trưa ngày 4. Tổng kết lợi nhuận thực tế, ghi lại model nào bán nhanh để làm tiếp."),
    ]
    for i, (ng, nd) in enumerate(lich):
        h = 26 + i
        ws.cell(row=h, column=1, value=ng).font = F_DAM
        c = ws.cell(row=h, column=2, value=nd)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.font = F_CHU
        ws.merge_cells(start_row=h, start_column=2, end_row=h, end_column=7)
        ws.row_dimensions[h].height = 62


def sheet_tong_quan(wb, meta, so, von, lech, he_so, vung):
    ws = wb.active
    ws.title = "Tổng quan"
    dat_rong(ws, [46, 10, 18, 70])
    ws["A1"] = "So sánh giá đồ công nghệ cũ trên Chợ Tốt — tìm tin rao thấp hơn thị trường ≥ 30 %"
    ws["A1"].font = F_TIEU_DE
    ws["A2"] = (f"Quét lúc {meta['quet_luc']} (giờ Việt Nam) qua API công khai gateway.chotot.com, {meta['so_tin']:,} tin, "
                "4 danh mục: điện thoại, máy tính bảng, máy ảnh/máy quay, thiết bị đeo. Phạm vi: toàn quốc.")
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws["A2"].font = F_CHU
    ws.merge_cells("A2:D2")
    ws.row_dimensions[2].height = 30
    ws["A4"] = "Tham số (ô vàng có thể sửa, các sheet khác tính lại theo)"
    ws["A4"].font = F_DAM
    tham_so = [("Vốn ban đầu (đ)", von, VND, "Theo yêu cầu: 1 triệu"),
               ("Ngưỡng lệch giá để coi là cơ hội (so với trung vị)", lech, "0%", "Theo yêu cầu: > 30 %"),
               ("Hệ số bán nhanh (giá bán dự kiến = trung vị × hệ số)", he_so, "0%", "Giả định: bán dưới giá thị trường 8 % để bán trong 1–2 ngày")]
    for i, (a, b, fmt, d) in enumerate(tham_so):
        h = 5 + i
        ws.cell(row=h, column=1, value=a).font = F_CHU
        c = ws.cell(row=h, column=3, value=b)
        c.number_format, c.fill, c.font, c.border = fmt, TO_VAO, F_VAO, VIEN
        ws.cell(row=h, column=4, value=d).font = F_CHU
    ws["A9"] = "Kết quả"
    ws["A9"].font = F_DAM
    kq = [("Tin đã quét", "=COUNTA('Toàn bộ tin'!A:A)-1"),
          ("Tin có đủ nhóm để tính giá thị trường", so["co_med"]),
          ("Cơ hội mua ngay (≤ 1,2 × vốn, lệch ≥ ngưỡng, không lỗi nặng)", "=COUNTA('Cơ hội mua ngay'!A:A)-3"),
          ("   trong đó ưu tiên A", "=COUNTIF('Cơ hội mua ngay'!A:A,\"A\")"),
          ("Cơ hội vòng sau (1,2 × vốn đến 3 triệu)", "=COUNTA('Cơ hội vòng sau'!A:A)-3"),
          ("Tin rẻ bị loại vì mô tả có lỗi/hỏng", so["loai_loi"]),
          ("Tin rẻ bị loại vì đăng quá 7 ngày (đã bán hoặc có vấn đề)", so["qua_cu"]),
          ("Tin rẻ bị loại vì tiêu đề ghi model khác mục người bán chọn", so["loai_model"]),
          ("Vùng lọc cơ hội", vung or "Toàn quốc (lọc cột Tỉnh/TP theo nơi bạn ở)")]
    for i, (a, b) in enumerate(kq):
        ws.cell(row=10 + i, column=1, value=a).font = F_CHU
        c = ws.cell(row=10 + i, column=3, value=b)
        c.font, c.alignment = F_CHU, PHAI
    ws["A20"] = "Cách đọc"
    ws["A20"].font = F_DAM
    huong_dan = [
        "Giá thị trường = trung vị giá rao của các tin cùng hãng + model + dung lượng + tình trạng (Mới / Cũ / Cũ đã sửa) trên toàn quốc; nhóm dưới 5 tin thì lùi về cùng model. Đây là giá RAO, giá bán thật thường thấp hơn 5–10 %.",
        "Lệch giá = (trung vị − giá rao) / trung vị. Chỉ tin lệch ≥ ngưỡng, giá ≥ 100.000 đ, đăng trong 7 ngày, mô tả không có từ khoá lỗi/hỏng, tiêu đề khớp model đã chọn mới vào sheet cơ hội. Model 'Dòng khác'/'Hãng khác' không so giá được nên không xét.",
        "Ưu tiên A: điểm chất lượng ≥ 1, tin đăng ≤ 48 giờ, người bán cá nhân, nhóm ≥ 10 tin, lệch < 60 %. B: đạt ngưỡng nhưng thiếu một điều kiện. C: có cảnh báo (lệch ≥ 60 % nghi lừa đảo, tin cửa hàng, mô tả đòi cọc/ship, điểm chất lượng âm).",
        "Điểm chất lượng chấm tự động từ mô tả: +1 mỗi từ khoá tốt (zin, chưa sửa, fullbox, 99 %...), −1 mỗi từ khoá hao mòn (trầy, thay pin, ép kính...), −5 nếu có lỗi/hỏng. Chỉ là lọc sơ bộ, phải xem máy trực tiếp.",
        "Nguồn gốc: cột 'Xuất xứ (khai báo)' là trường người bán chọn trên Chợ Tốt; 'Nguồn gốc theo mô tả' rút từ chữ trong tin (xách tay, VN/A, LL/A, trả bảo hành, hàng công ty...). 'Phiên bản' = quốc tế hay khoá mạng.",
        "Nơi bán: Tỉnh/TP, Quận/Huyện, Phường/Xã do người bán khai; liên hệ qua nút trên trang tin (cột Link). Chợ Tốt ẩn số điện thoại với API công khai nên không có trong file.",
        "Facebook Marketplace: trình duyệt tích hợp của Claude bị chặn truy cập facebook.com theo quyền trang web, nên file này chỉ có dữ liệu Chợ Tốt. Muốn bổ sung Facebook cần cho phép trang hoặc dùng Claude trong Chrome đã đăng nhập.",
        "Lưu ý pháp lý và an toàn: không cọc, không chuyển khoản trước; gặp nơi công cộng; kiểm tra IMEI, iCloud/Google; hàng không rõ nguồn gốc giá quá rẻ có thể là hàng trộm cắp. Số liệu chỉ để tham khảo, quyết định mua là của bạn.",
    ]
    for i, t in enumerate(huong_dan):
        c = ws.cell(row=21 + i, column=1, value=f"{i + 1}. {t}")
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.font = F_CHU
        ws.merge_cells(start_row=21 + i, start_column=1, end_row=21 + i, end_column=4)
        ws.row_dimensions[21 + i].height = 46


def gon(r):
    giu = ("list_id", "danh_muc", "tieu_de", "hang", "model", "dung_luong", "tinh_trang", "phien_ban", "xuat_xu",
           "nguon_goc_mo_ta", "bao_hanh", "gia", "med", "n_nhom", "lech", "loi_uoc", "diem", "ghi_chu", "canh_bao",
           "uu_tien", "nguoi_ban", "tinh", "quan", "phuong", "dang_luc", "mo_ta", "anh", "link")
    return {k: (v.isoformat(timespec="minutes") if isinstance(v, dt.datetime) else v) for k, v in r.items() if k in giu}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="file JSON đã quét (có thể dùng *)")
    ap.add_argument("--von", type=int, default=1000000)
    ap.add_argument("--lech", type=float, default=0.30)
    ap.add_argument("--he-so-ban", type=float, default=0.92)
    ap.add_argument("--vung", default=None, help="chỉ lấy cơ hội ở tỉnh/thành có tên chứa chuỗi này")
    ap.add_argument("--toi-da-co-hoi", type=int, default=80)
    ap.add_argument("--khong-anh", action="store_true")
    ap.add_argument("--ra", default=None)
    args = ap.parse_args()

    ads, meta = [], None
    for mau in args.files:
        for fn in sorted(glob.glob(mau)):
            with open(fn, encoding="utf-8") as f:
                d = json.load(f)
            meta = meta or {"quet_luc": d.get("quet_luc", ""), "so_tin": 0}
            ads += d["ads"]
    thay, duy_nhat = set(), []
    for a in ads:
        if a["list_id"] not in thay:
            thay.add(a["list_id"])
            duy_nhat.append(a)
    meta["so_tin"] = len(duy_nhat)
    ma = tai_ma()
    print(f"{len(duy_nhat):,} tin; chuẩn hoá...")
    rows = [chuan_hoa(a, ma) for a in duy_nhat]
    bang = gan_gia_thi_truong(rows)
    co_med = sum(1 for r in rows if r["med"])
    print(f"{co_med:,} tin có giá thị trường; {len(bang):,} nhóm giá")

    ten_hang_cache = {}
    for r in rows:
        if r["hang"] and r["brand_code"] is not None:
            ten_hang_cache[(r["cg"], r["brand_code"])] = r["hang"]

    def ten_hang(cg, code):
        return ten_hang_cache.get((cg, code), "")

    bay_gio = dt.datetime.now()
    ung_vien, loai_loi, qua_cu, loai_model = [], 0, 0, 0
    for r in rows:
        if r["lech"] is None or r["lech"] < args.lech or r["gia"] < 100000:
            continue
        if r["cg"] == 5050 and r["loai"] in ("Ống kính", "Khác"):
            continue  # phụ kiện, ống kính: khó so giá theo tiêu đề
        if args.vung and bo_dau(args.vung) not in bo_dau(r["tinh"]):
            continue
        if r["nang"]:
            loai_loi += 1
            continue
        tuoi = (bay_gio - r["dang_luc"]).total_seconds() / 3600 if r["dang_luc"] else 999
        if tuoi > 24 * 7:
            qua_cu += 1  # tin rẻ bất thường mà treo quá 1 tuần: đã bán hoặc có vấn đề
            continue
        if r["khac_model"].startswith("khác model"):
            loai_model += 1
            continue
        r["uu_tien"] = uu_tien(r, args.von, tuoi)
        r["canh_bao"] = canh_bao(r, tuoi)
        r["loi_uoc"] = r["med"] * args.he_so_ban - r["gia"]
        ung_vien.append(r)
    thu_tu = {"A": 0, "B": 1, "C": 2}
    ung_vien.sort(key=lambda r: (thu_tu.get(r["uu_tien"], 3), -r["loi_uoc"]))
    mua_ngay = [r for r in ung_vien if r["gia"] <= args.von * 1.2][: args.toi_da_co_hoi]
    vong_sau = [r for r in ung_vien if args.von * 1.2 < r["gia"] <= 3000000][: args.toi_da_co_hoi]
    print(f"{len(mua_ngay)} cơ hội mua ngay, {len(vong_sau)} cơ hội vòng sau ({len(ung_vien)} ứng viên); loại: {loai_loi} lỗi/hỏng, "
          f"{qua_cu} quá 7 ngày, {loai_model} tiêu đề khác model")

    if not args.khong_anh:
        print("tải ảnh...")
        tai_anh(mua_ngay + vong_sau, os.path.join(HERE, "anh"))

    wb = Workbook()
    sheet_tong_quan(wb, meta, {"co_med": co_med, "loai_loi": loai_loi, "qua_cu": qua_cu, "loai_model": loai_model},
                    args.von, args.lech, args.he_so_ban, args.vung)
    sheet_co_hoi(wb, "Cơ hội mua ngay", mua_ngay,
                 f"Cơ hội mua ngay: giá rao ≤ {args.von * 1.2:,.0f} đ, thấp hơn giá thị trường ≥ {args.lech:.0%}, mô tả không có lỗi/hỏng",
                 "Sắp theo ưu tiên (A tốt nhất) rồi theo lợi nhuận dự kiến. Lọc cột Tỉnh/TP theo nơi bạn ở. Luôn gọi hỏi còn hàng và xem máy trực tiếp; "
                 "cột Cảnh báo và Ghi chú chất lượng là lọc tự động từ mô tả, không thay cho việc kiểm tra.", not args.khong_anh)
    sheet_co_hoi(wb, "Cơ hội vòng sau", vong_sau,
                 f"Cơ hội vòng sau: giá rao {args.von * 1.2:,.0f}–3.000.000 đ, dùng khi vốn đã tăng sau vòng 1",
                 "Cùng tiêu chí với sheet 'Cơ hội mua ngay'. Món đắt hơn thường lời tuyệt đối cao hơn nhưng cần vốn và bán chậm hơn.", not args.khong_anh)
    sheet_gia_thi_truong(wb, bang, ten_hang)
    sheet_thanh_khoan(wb, bang, ten_hang, args.von)
    sheet_ke_hoach(wb)
    sheet_toan_bo(wb, sorted(rows, key=lambda r: (r["cg"], r["hang"], r["model_key"], r["gia"])))
    wb.calculation.fullCalcOnLoad = True
    ra = args.ra or os.path.join(HERE, "ket_qua", f"so_sanh_gia_chotot_{bay_gio:%Y%m%d_%H%M}.xlsx")
    os.makedirs(os.path.dirname(ra), exist_ok=True)
    wb.save(ra)
    print("Đã ghi", ra)
    with open(os.path.splitext(ra)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump({"quet_luc": meta["quet_luc"], "von": args.von, "lech": args.lech, "he_so_ban": args.he_so_ban,
                   "mua_ngay": [gon(r) for r in mua_ngay], "vong_sau": [gon(r) for r in vong_sau]}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
