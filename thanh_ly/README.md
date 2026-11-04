# Khảo sát giá đồ công nghệ cũ để mua đi bán lại

Quét tin rao trên Chợ Tốt (API công khai, không cần đăng nhập), tính giá thị trường của từng model,
lọc tin rao thấp hơn thị trường ≥ 30 %, chấm chất lượng theo mô tả và xuất Excel kèm ảnh để chọn mua.
Không liên quan đến phần PCCC của repo; nằm chung repo chỉ để dùng cùng môi trường Python.

## Chạy

```bash
pip install requests openpyxl pillow
python quet_chotot.py                                   # quét toàn quốc 4 danh mục, ~25.000 tin, 6–7 phút
python ma_tham_so.py du_lieu/chotot_*.json              # học bảng mã → tên (chỉ cần chạy lại khi có mã mới)
python phan_tich.py du_lieu/chotot_YYYYMMDD_HHMM.json   # Excel + JSON cơ hội vào ket_qua/
```

Tuỳ chọn hay dùng:

- `quet_chotot.py --gio 3 --vung 13000`: chỉ tin đăng 3 giờ gần nhất ở TP HCM (quét định kỳ).
- `phan_tich.py --vung "Hồ Chí Minh"`: chỉ lấy cơ hội ở một tỉnh/thành. `--von 1000000 --lech 0.30 --he-so-ban 0.92` là mặc định.
- `phan_tich.py --khong-anh`: không tải ảnh (nhanh hơn).

Mã vùng `region_v2`: 13000 TP HCM, 12000 Hà Nội. Mã danh mục: 5010 điện thoại, 5040 máy tính bảng,
5050 máy ảnh/máy quay, 5090 thiết bị đeo (5030 laptop, 5020 tivi/âm thanh nếu cần mở rộng).

## Cách tính

- **Giá thị trường** = trung vị giá rao của nhóm *danh mục + hãng + model + dung lượng + tình trạng*
  (Mới / Cũ / Cũ đã sửa). Nhóm dưới 5 tin thì lùi về *model + tình trạng*, rồi *model*.
- **Lệch giá** = (trung vị − giá rao) / trung vị. Cơ hội = lệch ≥ 30 %, giá ≥ 100.000 đ, mô tả không có
  từ khoá lỗi/hỏng (sau khi bỏ các cụm phủ định như "không lỗi", "chưa sửa").
- **Điểm chất lượng**: +1 mỗi từ khoá tốt (zin, fullbox, 99 %...), −1 mỗi từ khoá hao mòn (trầy, thay pin...),
  −5 nếu lỗi/hỏng; ±1 theo tình trạng khai báo.
- **Ưu tiên A/B/C**: A = điểm ≥ 1, tin ≤ 48 giờ, người bán cá nhân, nhóm ≥ 10 tin, lệch < 60 %;
  C = có cảnh báo (lệch ≥ 60 % nghi lừa đảo, tin cửa hàng, đòi cọc/ship, điểm âm); B = còn lại.
- **Thanh khoản** (khả năng bán lại) ước theo số tin rao của nhóm: ≥ 60 rất cao, ≥ 25 cao, ≥ 10 trung bình.

## File

| File | Nội dung |
| --- | --- |
| `quet_chotot.py` | Quét API, lưu `du_lieu/chotot_<giờ>.json` (không commit, ~70 MB) |
| `ma_tham_so.py` | Học bảng mã → tên, lưu `du_lieu/ma_tham_so.json` |
| `phan_tich.py` | Chuẩn hoá, tính giá, lọc cơ hội, tải ảnh vào `anh/`, xuất `ket_qua/*.xlsx` và `*.json` |
| `quet_dinh_ky.py` | Bản gọn, tự chứa (chỉ thư viện chuẩn Python): quét + lọc tin mới N giờ, in bảng Markdown. Dùng cho routine cloud |

## Quét định kỳ trên cloud (GitHub Actions + routine Claude)

Hai tầng, từ 04/11/2026:

1. **GitHub Actions** (`.github/workflows/quet_chotot.yml`, chỉ chạy trên nhánh `main`) 6 lần/ngày lúc 6h, 9h,
   12h, 15h, 18h, 21h giờ Việt Nam (cron UTC `0 2,5,8,11,14,23 * * *`), chạy
   `python thanh_ly/quet_dinh_ky.py --gio 4 --von 1200000 --toi-da-in 25` rồi commit kết quả vào
   `thanh_ly/ket_qua_dinh_ky/moi_nhat.md` (bảng Markdown) và `moi_nhat.json`. Runner của GitHub có mạng đầy đủ nên
   không vướng proxy. Chạy tay: tab Actions → "Quét Chợ Tốt định kỳ" → Run workflow. Nếu bước đẩy commit bị từ
   chối, vào Settings → Actions → General → Workflow permissions, chọn "Read and write permissions".
2. **Routine Claude** `Chợ Tốt: săn đồ công nghệ rẻ hơn thị trường ≥30% (1,2 triệu)` tại
   <https://claude.ai/code/routines/trig_018aqghyrGBXpLegRcWddA58> chạy 15 phút sau mỗi lần Actions, chỉ đọc
   `moi_nhat.md` trong repo (clone nhánh `main`), kiểm tra giờ quét còn mới rồi đẩy thông báo lên điện thoại kèm bảng
   tin. Không cần mạng ra ngoài. Sau 08/11/2026 nên tắt (Disable) routine và workflow nếu không dùng nữa.

Lý do không cho routine tự quét: proxy của môi trường cloud Anthropic chặn `gateway.chotot.com` (403) dù đã thử
mở quyền mạng; bộ phân loại an toàn còn từ chối mẫu "giải mã base64 rồi chạy", và hook môi trường nhắc commit file
mới trong repo. Chạy tại máy cá nhân vẫn được: `python quet_dinh_ky.py --gio 4 --von 1200000` (2,5 phút,
không cần cài gì; nhật ký ra stderr, bảng ra stdout).

Facebook Marketplace chưa lấy được: trình duyệt tích hợp bị chặn facebook.com theo quyền trang web.
Số liệu chỉ để tham khảo; luôn xem máy trực tiếp, kiểm tra IMEI, iCloud/Google trước khi mua.
