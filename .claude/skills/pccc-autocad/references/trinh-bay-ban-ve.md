# Quy cách trình bày hồ sơ PCCC (theo hồ sơ mẫu đã duyệt)

Hồ sơ mẫu là bộ **KS 32 Dã Tượng** (khách sạn kết hợp nhà ở 8 tầng + tum, 33 tờ A3, 10/2026). Các con số dưới đây đo trực tiếp từ PDF (chữ, màu, độ dày nét, kích thước khung). Mọi dự án sau **trình bày theo quy cách này**, trừ khi người dùng yêu cầu khác. Code tương ứng nằm ở `scripts/ky_hieu.py` (ký hiệu, ống, bảng ký hiệu) và `scripts/trinh_bay.py` (dim, khung tên, ghi chú, bảng).

Mọi kích thước ghi theo **mm trên giấy**. Kích thước trong model = mm giấy × tỷ lệ in (1:125 → ×125).

## 1. Bộ hồ sơ: thứ tự tờ

| # | Tờ | Nội dung chính |
| --- | --- | --- |
| 1 | Bìa | Quốc hiệu, "HỒ SƠ XIN PHÉP THẨM ĐỊNH VỀ PHÒNG CHÁY CHỮA CHÁY", công trình, địa chỉ, chủ đầu tư, đơn vị tư vấn, nơi/ngày |
| 2 | Bản đồ vị trí + quy mô | Bảng QUY MÔ CÔNG TRÌNH (chiều cao PCCC, khối tích, nhóm nhà F, bậc chịu lửa, cấp nguy hiểm cháy kết cấu, viện dẫn QCVN 06 bảng 4/5/6); bảng KHỐI TÍCH theo tầng; sơ đồ vị trí, trụ cấp nước đô thị (lưu lượng, khoảng cách ≤ 200 m); vật liệu hoàn thiện (bảng B.8/B.9 QCVN 06); chiều cao công trình và chiều cao PCCC |
| 3 | Mặt cắt | Mặt cắt có cao độ từng tầng và **Hpccc** ghi đỏ |
| — | **HẠNG MỤC: HỆ THỐNG BÁO CHÁY** | Tờ phân cách (`trinh_bay.to_bia_hang_muc`) |
| 5–9 | Mặt bằng báo cháy từng tầng | Tầng giống nhau gộp một tờ ("TẦNG 3-6", "TẦNG 7-8") |
| 10 | Mặt cắt hệ báo cháy | |
| 11 | Sơ đồ nguyên lý báo cháy | Bảng tính nguồn ắc quy tủ trung tâm (Phụ lục C TCVN 7568-14:2025), sơ đồ zone theo tầng (số lượng thiết bị mỗi zone "x09"), hình khoảng cách lớn nhất giữa các đầu báo |
| 12 | Chi tiết lắp đặt điển hình | Trung tâm, nút ấn/chuông, đầu báo, chống cháy lan xuyên tường/sàn |
| — | **HẠNG MỤC: HỆ THỐNG CHỮA CHÁY** | |
| 14 | Thuyết minh chữa cháy | Tiêu chuẩn áp dụng, mô tả hệ, lưu lượng, cột áp, thể tích bể |
| 15–19 | Mặt bằng chữa cháy từng tầng | Sprinkler + họng + bình trên **cùng một tờ** |
| 20 | Sơ đồ nguyên lý chữa cháy | Bảng ký hiệu van/phụ kiện, bảng thông số bơm |
| 21 | Sơ đồ không gian + bảng tính thuỷ lực | |
| 22–23 | Chi tiết phòng bơm, họng tiếp nước, đầu phun, giá treo | |
| — | **HẠNG MỤC: ĐÈN CHIẾU SÁNG SỰ CỐ, CHỈ DẪN THOÁT NẠN** | |
| 25–29 | Mặt bằng chiếu sáng sự cố | |
| 30 | Thuyết minh + chi tiết đèn, catalogue | |
| — | **HẠNG MỤC: HỆ THỐNG CẤP ĐIỆN PHỤC VỤ PCCC** | |
| 32–33 | Thuyết minh điện + sơ đồ nguyên lý (ATS, phụ tải ưu tiên) | |

## 2. Bố cục một tờ mặt bằng (A3 ngang)

```
┌──────────────────────────────────────────────────────────┬────────┐
│ GHI CHÚ: (3,7 mm, góc trên-trái)                         │ phát   │
│ - ...                                                    │ hành   │
│                                                          │ chủ ĐT │
│          ┌── dim trục kiến trúc (đen 4,0 mm) ──┐         │ đơn vị │
│          │ ┌─ dim thiết bị (đỏ 4,2 mm) ─┐      │         │ GĐ     │
│     ○C ──┼─┼──── mặt bằng 1:125 ────────┼──────┼── ○     │ chủ trì│
│     ○A ──┴─┴────────────────────────────┴──────┘         │ TK     │
│               ①  ②  ③  ④  ⑤  ⑥  ⑦                       │ dự án  │
│               MẶT BẰNG TẦNG 1 (5,35 mm, giữa)            │ ngày   │
│ GHI CHÚ:                     ┌ hộp ghi chú TC (khung đỏ)┐ │ sửa đổi│
│ ┌──┬─────────────┐           └──────────────────────────┘ │ số tờ  │
│ │ký│ mô tả       │  (bảng bình chữa cháy ở tờ chữa cháy)  │        │
└─┴──┴─────────────┴───────────────────────────────────────┴────────┘
```

- Khổ A3 420×297, khung trong cách mép 5 mm (trái/phải) và 4 mm (trên/dưới), nét khung 0,5 mm.
- **Cột thông tin bên phải rộng 41,6 mm**, từ trên xuống: mục đích phát hành (ô đánh dấu: Tham khảo / Thiết kế sơ bộ / Trình duyệt / Đấu thầu / Thi công / Hoàn công), chấp thuận của chủ đầu tư, đơn vị thiết kế (logo, tên, địa chỉ, MST), Giám đốc, Chủ trì thiết kế, Thiết kế, Dự án + địa chỉ, ngày + ký hiệu tờ, bảng sửa đổi. Dùng `trinh_bay.khung_a3(msp, goc, ty_le, tt)`; tên người và công ty lấy từ người dùng, **không tự điền**.
- **Tỷ lệ mặt bằng 1:125** (lưới 5 m in ra 40 mm). Không ghi tỷ lệ dưới tên hình.
- Tên hình "MẶT BẰNG TẦNG …" chữ Arial 5,35 mm, đặt giữa, dưới hàng bong bóng trục.
- Ghi chú chung của hệ đặt **góc trên-trái** (chữ 3,7 mm, không khung).
- Bảng ký hiệu "GHI CHÚ:" đặt **góc dưới-trái**, chỉ gồm thiết bị có trên tờ.
- Góc dưới-phải: hộp ghi chú tiêu chuẩn (khung đỏ mảnh, chữ 2,3 mm) và hộp ghi chú công năng (kho, chiều cao hàng hoá, đường thoát nạn, tủ điện). Ở tờ chữa cháy, chỗ này là **bảng bình chữa cháy** rộng ~204 mm.

## 3. Màu, nét, chữ

| Đối tượng | Màu (RGB đo được → ACI) | Nét in | Chữ |
| --- | --- | --- | --- |
| Nền kiến trúc (tường, cửa, đồ đạc) | xám (89,89,89) → ACI 8 (251 gần nhất) | mảnh nhất | tên phòng xám 2,4 mm |
| Cột | xám đậm tô đặc | | |
| Trục, dim trục kiến trúc | đen / xám | 0,04 | 4,0 mm Arial; bong bóng trục 4,6 mm |
| **Dim thiết bị** | chữ **đỏ** (ACI 1), đường dim + gạch chéo **xanh tím** (91,91,184) → ACI 173 | 0,30 | 4,2 mm, font hẹp (Arial Narrow) |
| Cáp báo cháy | **tím** ACI 6, nét đứt | 0,30 | |
| Ống chính (DN ≥ 50) | **đỏ**, vẽ **hai nét viền** (khoảng 2,8 mm giấy), có bịt đầu | 0,5–0,6 | "DN80" tím 1,8 mm |
| Ống nhánh (DN < 50) | **tím**, một nét | 0,13 | "DN25" tím 1,8 mm, xoay theo ống |
| Vòng bán kính phục vụ họng nước | xanh tím, nét đứt | 0,13 | |
| Ghi chú, bảng | đen | | Arial 2,3–3,7 mm |

Dùng font Unicode (Arial). Bản mẫu còn lẫn font VNI (chữ bị lỗi khi xuất PDF ở một số bảng), nên **không dùng VNI**. Arial Narrow trên Windows **thiếu dấu tiếng Việt**: chỉ dùng cho chữ số dim.

## 4. Ký hiệu thiết bị (block trong `ky_hieu.py`)

| Thiết bị | Hình | Cỡ (mm giấy) |
| --- | --- | --- |
| Đầu báo khói | vòng tròn đỏ + chữ **S** đỏ đậm | Ø3,4 |
| Đầu báo nhiệt | vòng tròn xanh lá + chữ **H** | Ø3,4 |
| Nút nhấn khẩn | ô vuông bo góc xanh lá, chữ "FIRE" + ba gạch "///" | 3×3 |
| Chuông + đèn | ô vuông bo góc xanh lá, chuông tròn có lưới | 3×3 |
| Tủ trung tâm | khung đỏ, chữ "FACP" xanh nhạt | 8×2,4 |
| Đèn FIRE ngoài nhà | khung đỏ, chữ "FIRE" đỏ | 6×2,2 |
| Đèn báo cháy phòng | khung xanh dương, bóng đèn có tia | 2,4×3,2 |
| Sprinkler | hai vòng tròn đồng tâm + dấu chéo, đỏ | Ø3,5 |
| Hộp họng nước (FHR) | khung đỏ, tam giác tô đặc, chữ "FHR" | 6×2,2 |
| Bình ABC / CO2 | ô bo góc đỏ, vòng tròn ghi "ABC"/"CO2" | 2,6×2,6 |
| Tủ dụng cụ phá dỡ | khung đỏ, hình rìu | 4×2,6 |
| EXIT / EXIT chỉ hướng | khung xanh lá, chữ "EXIT" (+ mũi tên) | 4×1,6 |
| Đèn chiếu sáng sự cố | hai bóng tròn đỏ | 3,2 |
| Sơ đồ thoát nạn phòng | khung tím chữ "SDTNP", đặt cạnh cửa trong mỗi phòng | 4×1,6 |
| Hộp mặt nạ | khung đỏ, mặt nạ tô đặc | 3,2×1,6 |

Hộp họng luôn đi kèm **1 bình ABC + 1 bình CO2** đặt sát bên (cụm ở hành lang cạnh thang).

## 5. Ghi kích thước — quy tắc bắt buộc

### Báo cháy (`trinh_bay.dim_dau_bao`)
Mỗi đầu báo có **ba dim**:
1. Một dim vuông góc tới bức tường gần nhất theo phương ngang.
2. Một dim vuông góc tới bức tường gần nhất theo phương dọc.
3. **Một dim chéo tới góc phòng** (ưu tiên phía đối diện hai dim kia) để chứng minh vùng bảo vệ. **Chỉ ghi khi dim ≤ 7,2 m với đầu báo khói, ≤ 5,1 m với đầu báo nhiệt** (TCVN 7568-1:2025, Hình 2 và Hình 7). Chọn góc xa nhất trong giới hạn đó; nếu dài hơn thì không ghi dim chéo.
Hành lang, hoặc phòng có hàng từ 3 đầu báo thẳng hàng trở lên (khu kỹ thuật tầng 1 của bản mẫu: 2327 – 4796 – 5075 – 4999 – 4963 – 2234): một chuỗi dim tường → đầu báo → … → tường dọc hàng thay cho dim vuông góc từng đầu báo, vì dim tới tường của phòng dài sẽ rất dài và chồng nhau. Dùng `trinh_bay.dim_bao_chay_phong` để xử lý cả phòng.

### Sprinkler (`trinh_bay.dim_theo_truc`)
- **Chuỗi ngang đặt ngoài nhà**, ngay dưới hàng dim trục kiến trúc. Chuỗi đi qua **trục lưới và các cột đầu phun** (ví dụ ①→1101→2350→1200→②→750→1601→1500→③…). Không dim tới tường.
- Chuỗi dọc đặt ngoài nhà bên trái hoặc phải: trục → hàng đầu phun → trục (1151 – 2000 – 1050).
- Đầu phun hành lang: chuỗi dọc theo ống chính (1900 – 3500 – … – 1901).
- Phòng lớn không chia (tầng 1, tum): chuỗi tường → hàng → hàng → tường (1000 – 3801 – 1000).

### Họng nước
- Vẽ **vòng tròn nét đứt bán kính phục vụ** quanh hộp họng (`vong_phuc_vu`), bán kính bằng chiều dài cuộn vòi (20 m). Vòng tròn phải bao hết mặt bằng tầng.

## 6. Bố trí theo bản mẫu (rút ra để áp dụng)

- **Không bố trí đầu báo và sprinkler trong WC và buồng thang bộ.** Thêm ghi chú "KHÔNG BỐ TRÍ CÁP ĐIỆN TRÊN TRẦN NHÀ WC".
- Phòng khách sạn: mỗi phòng ngủ 1 đầu báo khói ở khoảng giữa phòng (ngoài WC), sprinkler 2 hàng × 1–2 cột trong phòng ngủ.
- Đầu phun trong phòng thẳng cột với nhánh: nhánh DN25 đi vuông góc từ ống chính hành lang xuyên qua phòng, các đầu cùng hoành độ chung một nhánh. Ống chính chạy giữa hành lang, đầu phun hành lang nằm ngay trên ống chính, bước ~3,5 m.
- Cáp báo cháy đi vuông góc, nối các đầu báo thành mạch, rồi về hộp nút ấn + chuông ở hành lang cạnh thang. Ghi "TẦNG x KẾT NỐI VỀ ZONE y, TỦ TRUNG TÂM BÁO CHÁY ĐẶT TẠI TẦNG 1" bằng đường dẫn chỉ.
- Mỗi tầng có một cụm nút ấn + chuông đèn tại hành lang. Mỗi phòng có đèn báo cháy phòng ngoài cửa. Đèn FIRE ngoài nhà đặt ở tầng 1.
- Chiếu sáng sự cố: EXIT trên cửa thang/lối ra, EXIT chỉ hướng dọc hành lang, đèn sự cố trên hành lang và thang, SDTNP trong mỗi phòng cạnh cửa, sơ đồ thoát nạn tầng cạnh thang máy.

## 7. Ghi chú và bảng mẫu (đã có sẵn trong `trinh_bay.py`)

- `GHI_CHU_BAO_CHAY`: trần treo kỹ thuật chỉ có cáp chiếu sáng/thông tin, nên không phải trang bị đầu báo trong không gian trần (Chú thích (2), Bảng A.2, Phụ lục A, QCVN 10:2025/BCA); không có trần hở.
- `GHI_CHU_TC_BAO_CHAY`: khoảng cách đầu báo khói tới mép cửa cấp gió ≥ 0,4 m (TCVN 7568-1:2025, mục 5.9.1.1.4 b); đầu báo nhiệt ≥ 0,6 m (mục 5.9.2.1.4 b).
- `GHI_CHU_CHUNG`: kho chứa vật dụng không cháy; hàng hoá cao ≤ 2,2 m; đường thoát nạn không giật cấp; không có tủ điện > 1 m³.
- `GHI_CHU_CHIEU_SANG`: pin 2 h; 10 lux trung bình, 1 lux nhỏ nhất; EXIT nhìn rõ từ 30 m; sơ đồ 600×400 (tầng) và 400×300 (phòng), mép dưới cao 1,5 ± 0,2 m; TCVN 13456:2022 mục 5.2.9.
- `bang_binh(...)`: bảng "BỐ TRÍ VÀ CÔNG SUẤT BÌNH CHỮA CHÁY VỚI MỐI NGUY HIỂM LOẠI A THEO TCVN 7435-1:2004". Cột: STT | loại bình | mức nguy hiểm | diện tích bảo vệ 1 bình | diện tích sàn | số bình tính toán (= S/S1) | dự phòng 10 % | tổng | số bình thiết kế | kết quả. Bản mẫu: mức CAO, 100 m²/bình. Kỹ sư chốt lại theo tiêu chuẩn.
- `bang_quy_mo(...)`: bảng khối tích theo tầng, **tự cộng tổng**.

Đây là ghi chú của công trình mẫu. Với dự án mới, đọc lại từng dòng và sửa cho đúng công trình (công năng kho, chiều cao hàng hoá, có trần treo hay không…).

## 8. Thuyết minh chữa cháy: cấu trúc theo bản mẫu

1. Tiêu chuẩn áp dụng: QCVN 06:2022/BXD + Sửa đổi 01:2023; TCVN 2622:1995; QCVN 10:2025/BCA; TCVN 7336:2021; TCVN 4513:1998.
2. Ống sơn đỏ, ống thép tráng kẽm (STK).
3. Hệ gồm: trạm bơm; chữa cháy vách tường (tủ trong nhà, họng tiếp nước xe chữa cháy); sprinkler.
4. Nguồn bơm: lưới điện + máy phát dự phòng / bơm diesel. Hai chế độ tay và tự động, khởi động ≤ 30 s.
5. Họng vách tường: lưu lượng theo Phụ lục H, Bảng H.5 QCVN 10:2025/BCA (bản mẫu 1 họng × 2,6 l/s). Tủ 600×400×220, tâm họng cao +1,25 m, gồm van DN50, van giảm áp, lăng D13, vòi DN50 dài 20 m. Áp lực đầu lăng 2,5 kg/cm², cột nước đặc 12 m (Bảng H.7).
6. Bể nước: thể tích, nguồn cấp, van phao.
7–8. Lưu lượng bơm: Q = Q sprinkler + Q họng (bản mẫu 10 + 2,6 = 12,6 l/s).
9. Cột áp: tính tại điểm bất lợi nhất (xa và cao nhất), liệt kê bơm điện, bơm diesel, bơm bù.
10. Thể tích bể: Q sprinkler × thời gian + Q họng × thời gian.

Bảng tính thuỷ lực (tờ 21) theo các bước TCVN 7336:2021 Phụ lục B: dữ liệu (nhóm, diện tích tính toán, cường độ, số đầu, K) → lưu lượng đầu phun bất lợi q = K√P → tổn thất từng đoạn P = Q²L/(100·Kt) → đặc tính nhánh B = Q²/P → lưu lượng nhánh Q = √(B·P) → tổn thất cục bộ 20 % → cột áp bơm. Bảng có cột: Nhánh | Nút | Lưu lượng | Số đầu | DN | đường kính trong | vận tốc | chiều dài | Kt | áp suất | ghi chú.

## 9. Lỗi phát hiện trong bản mẫu (tránh lặp lại)

Khi kiểm tra bộ hồ sơ mẫu, các chỗ sau không khớp nhau. Hồ sơ mới phải **đối chiếu chéo** các số này giữa thuyết minh, sơ đồ nguyên lý và bảng tính:

| Chỗ | Ghi | Đúng ra |
| --- | --- | --- |
| Tờ 2, bảng khối tích | STT 1,1,1,2,3…; tổng chiều cao 28,8 m; tổng khối tích 6.175 m³ | STT 1–9; 3,3 + 7×3,1 + 3,0 = 28,0 m; 825 + 7×775 + 750 = **7.000 m³**. Khối tích ở bảng quy mô (6.175) cũng sai theo |
| Tờ 14, mục 9 | bơm điện/diesel 2,6 l/s | 12,6 l/s (đúng như mục 8 và tờ 21) |
| Tờ 14 / 20 / 21 | cột áp bơm chính 55 / **50** / 55 m; bơm bù 0,7 l/s–60 m / 0,7 l/s–**55** m / **2 l/s**–60 m | Thống nhất một bộ thông số ở cả ba tờ |
| Tờ 14 / 20 / 21 | bể 24 m³ / **23 m³** / 24 m³ (tính ra 22,68 m³) | Thống nhất 24 m³ |
| Tờ 15–19 | bảng ký hiệu chữa cháy thiếu sprinkler và ống; đầu phun trong phòng và ngoài hành lang dùng hai ký hiệu khác nhau | Một ký hiệu sprinkler, có trong bảng ký hiệu |
| Tờ 28 | "( NHÀ Ở RIÊNG LẺ)" lặp hai lần trong tên hình | |
| Nhiều tờ | font VNI lẫn Unicode (chữ lỗi khi trích PDF, "Tŕnh duyệt") | Chỉ dùng Unicode |

Trước khi xuất hồ sơ, chạy các kiểm tra sau: tổng bảng khối tích (`bang_quy_mo` tự cộng), số thiết bị trên sơ đồ nguyên lý (x09/zone) bằng số đếm trên mặt bằng (`thong_ke.py`), thông số bơm và bể giống nhau ở mọi tờ.
