"""Tính thuỷ lực SƠ BỘ cho sprinkler (mạng nhánh cây) và họng nước vách tường.

Sprinkler, cho một tầng:
  1. Vùng tính toán: diện tích A (theo nhóm) ở phía xa trục đứng nhất — lấy các đầu phun xa trục
     nhất (theo chiều dài đường ống) cho tới khi tổng diện tích bảo vệ ≥ A.
  2. Mỗi đầu trong vùng cần q ≥ max(cường độ × diện tích bảo vệ, K·√P_min).
  3. Đi ngược từ các đầu về trục đứng: tổn thất ma sát Hazen–Williams (nhân hệ số phụ kiện);
     tại điểm rẽ, nhánh có áp thấp hơn được nâng lưu lượng theo Q' = Q·√(P_cao/P_thấp).
  4. Từ chân trục: cộng tổn thất van khống chế tầng, van báo động, ma sát trục đứng và chênh cao.

Hazen–Williams (đơn vị mét hệ): p [bar] = 6,05·10^5 · L · Q^1,85 / (C^1,85 · d^4,87),
Q [l/phút], d [mm], L [m].

KẾT QUẢ CHỈ ĐỂ CHỌN SƠ BỘ. Hồ sơ thiết kế cần tính lại bằng phần mềm/thuyết minh đầy đủ theo
TCVN 7336:2021 (gồm hình dạng vùng tính toán, phụ kiện thực tế, đường đặc tính bơm).
"""
import math
from collections import defaultdict

G_BAR_M = 0.0981  # 1 m cột nước = 0,0981 bar


def ma_sat(Q_lpm, dn, L_m, tl):
    d = tl["ong"]["d_trong_mm"][str(dn)]
    C = tl["ong"]["C_hazen_williams"]
    return 6.05e5 * L_m * tl["ong"]["he_so_phu_kien"] * Q_lpm ** 1.85 / (C ** 1.85 * d ** 4.87)


def _khoa(p):
    return (round(p[0]), round(p[1]))


def tinh_tang_spr(mang, nhom, tl, dn_theo):
    """mang: {"truc": [x, y], "doan": [[p1, p2, n, loai]], "dau": [[x, y, dt_bao_ve, ten]]} (mm).
    nhom: dict thông số nhóm (cuong_do_l_s_m2, dien_tich_tinh_toan_m2, ...).
    Trả về dict: Q (l/phút) và P (bar) tại chân trục trên tầng, danh sách đầu hoạt động..."""
    K = tl["sprinkler"]["K_l_phut_bar05"]
    Pmin = tl["sprinkler"]["P_min_dau_bar"]
    i_tt = nhom["cuong_do_l_s_m2"] * 60  # l/phút/m²
    A_tt = nhom["dien_tich_tinh_toan_m2"]

    # cây ống: cạnh có hướng từ trục đứng ra
    ke = defaultdict(list)
    for p1, p2, n, _ in mang["doan"]:
        a, b = _khoa(p1), _khoa(p2)
        L = (abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])) / 1000
        ke[a].append((b, dn_theo(n), L))
        ke[b].append((a, dn_theo(n), L))
    goc = _khoa(mang["truc"])
    cha, xa, con = {goc: None}, {goc: 0.0}, defaultdict(list)
    hang = [goc]
    while hang:
        u = hang.pop()
        for v, dn, L in ke[u]:
            if v not in cha:
                cha[v], xa[v] = u, xa[u] + L
                con[u].append((v, dn, L))
                hang.append(v)
    dau = {_khoa(d[:2]): d[2] for d in mang["dau"]}
    dau = {k: v for k, v in dau.items() if k in xa}

    # nhánh gốc (phía trục) chứa mỗi đầu
    def nhanh_goc(k):
        while cha[k] is not None and cha[k] != goc:
            k = cha[k]
        return k

    xa_nhat = max(dau, key=lambda k: xa[k])
    phia = nhanh_goc(xa_nhat)
    ung_vien = sorted(dau, key=lambda k: (nhanh_goc(k) != phia, -xa[k]))
    hoat_dong, tong_dt = [], 0.0
    for k in ung_vien:
        if tong_dt >= A_tt:
            break
        hoat_dong.append(k)
        tong_dt += dau[k]
    hd = set(hoat_dong)

    chi_tiet = {}

    def giai(u):
        cac = []
        if u in hd:
            q = max(i_tt * dau[u], K * math.sqrt(Pmin))
            cac.append((q, (q / K) ** 2))
        for v, dn, L in con[u]:
            r = giai(v)
            if r:
                Qv, Pv = r
                cac.append((Qv, Pv + ma_sat(Qv, dn, L, tl)))
        if not cac:
            return None
        P = max(p for _, p in cac)
        Q = sum(q * math.sqrt(P / p) for q, p in cac)
        chi_tiet[u] = (Q, P)
        return Q, P

    Q, P = giai(goc)
    # lưu lượng thực tế từng đầu hoạt động (sau cân bằng)
    q_dau = []
    for k in hoat_dong:
        Pk = chi_tiet[k][1] if k in chi_tiet else Pmin
        q_dau.append((k, xa[k], dau[k]))
    k1 = max(hoat_dong, key=lambda k: xa[k])
    q1 = max(i_tt * dau[k1], K * math.sqrt(Pmin))
    return {
        "Q_lpm": Q, "P_bar": P, "so_dau_hd": len(hoat_dong), "dien_tich_hd_m2": tong_dt,
        "dau_bat_loi": {"vi_tri": k1, "q_lpm": q1, "P_bar": (q1 / K) ** 2, "dt_bao_ve_m2": dau[k1],
                        "chieu_dai_ong_toi_truc_m": xa[k1]},
        "Q_toi_thieu_lpm": i_tt * A_tt,
    }


def ap_luc_bom_spr(kq_tang, cao_do_san_m, L_cap_ngang_m, tl, dn_truc=100):
    """Áp lực cần tại đầu đẩy bơm (bar) để cấp cho tầng đó: cộng van, ma sát trục đứng, chênh cao."""
    sp = tl["sprinkler"]
    z = cao_do_san_m + sp["cao_tran_tren_san_m"]
    L_truc = z + L_cap_ngang_m
    thanh_phan = {
        "Áp lực cần tại chân trục trên tầng": kq_tang["P_bar"],
        "Van khống chế tầng + công tắc dòng chảy": sp["ton_that_van_khong_che_tang_bar"],
        "Van báo động (trạm kiểm tra)": sp["ton_that_van_bao_dong_bar"],
        f"Ma sát trục đứng + ống cấp DN{dn_truc} ({L_truc:.1f} m)": ma_sat(kq_tang["Q_lpm"], dn_truc, L_truc, tl),
        f"Chênh cao bơm → trần tầng ({z:.1f} m)": z * G_BAR_M,
    }
    return sum(thanh_phan.values()), thanh_phan


def tinh_hong(cao_do_san_cao_nhat_m, L_truc_m, L_cap_ngang_m, tl, dn_truc=100, dn_nhanh=50, L_nhanh_m=0.4):
    h = tl["hong"]
    Q = h["so_cot_nuoc"] * h["q_moi_cot_l_s"] * 60
    z = cao_do_san_cao_nhat_m + h["tam_van_tren_san_m"]
    thanh_phan = {
        "Áp lực cần tại van họng cao nhất": h["P_tai_van_bar"],
        f"Ma sát nhánh DN{dn_nhanh}": ma_sat(Q, dn_nhanh, L_nhanh_m, tl),
        f"Ma sát trục đứng + ống cấp DN{dn_truc} ({L_truc_m + L_cap_ngang_m:.1f} m)":
            ma_sat(Q, dn_truc, L_truc_m + L_cap_ngang_m, tl),
        f"Chênh cao bơm → van họng cao nhất ({z:.2f} m)": z * G_BAR_M,
    }
    return Q, sum(thanh_phan.values()), thanh_phan
