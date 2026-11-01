"""Chuyển chữ VNI-Windows (trích từ PDF hồ sơ mẫu) sang Unicode. Chỉ đổi từ không chứa ký tự tiếng Việt Unicode."""
import re
import unicodedata as ud

AC, GR, HK, TL, DT = "́", "̀", "̉", "̃", "̣"
CIRC, BREVE, HORN = "̂", "̆", "̛"
MU = {}   # ký tự VNI đứng sau nguyên âm -> (dấu mũ/trăng, dấu thanh, chỉ áp cho a?)
for lo, up, mu, th in [("á", "Á", CIRC, AC), ("à", "À", CIRC, GR), ("å", "Å", CIRC, HK), ("ã", "Ã", CIRC, TL),
                       ("ä", "Ä", CIRC, DT), ("â", "Â", CIRC, "")]:
    MU[lo] = MU[up] = (mu, th, "aeo")
for lo, up, mu, th in [("é", "É", BREVE, AC), ("è", "È", BREVE, GR), ("ú", "Ú", BREVE, HK), ("ü", "Ü", BREVE, TL),
                       ("ë", "Ë", BREVE, DT), ("ê", "Ê", BREVE, "")]:
    MU[lo] = MU[up] = (mu, th, "a")
THANH = {"ù": AC, "Ù": AC, "ø": GR, "Ø": GR, "û": HK, "Û": HK, "õ": TL, "Õ": TL, "ï": DT, "Ï": DT}
DON = {"ñ": "đ", "Ñ": "Đ", "í": "í", "Í": "Í", "ì": "ì", "Ì": "Ì", "æ": "ỉ", "Æ": "Ỉ", "ó": "ĩ", "Ó": "Ĩ",
       "ò": "ị", "Ò": "Ị"}
GOC = {"ô": "o" + HORN, "Ô": "O" + HORN, "ö": "u" + HORN, "Ö": "U" + HORN}
VN = re.compile("[Ạ-ỹĐđƠơƯư]")
DAU = re.compile("[ÑñÖöÙùØøÛûÕõÏïÒòÆæÔô" + "".join(MU) + "]")


def tu(w):
    if VN.search(w) or not DAU.search(w):
        return w
    ra, i = [], 0
    while i < len(w):
        c = w[i]
        goc = GOC.get(c) or (c if c.lower() in "aeouy" else None)
        if goc:
            i += 1
            m = w[i] if i < len(w) else ""
            if m in MU and goc[0].lower() in MU[m][2] and len(goc) == 1:
                goc += MU[m][0] + MU[m][1]
                i += 1
            elif m in THANH:
                goc += THANH[m]
                i += 1
            ra.append(ud.normalize("NFC", goc))
            continue
        ra.append(DON.get(c, c))
        i += 1
    return "".join(ra)


def doi(s):
    return re.sub(r"\S+", lambda m: tu(m.group()), s)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(doi(open(sys.argv[1], encoding="utf-8").read()))
