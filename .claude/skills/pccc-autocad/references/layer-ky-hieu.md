# Quy ước layer và ký hiệu PCCC

Màu và ký hiệu mô phỏng hồ sơ mẫu đã duyệt (xem `trinh-bay-ban-ve.md`). Block nào cũng tạo qua `scripts/ky_hieu.py`. Màu được đặt trực tiếp trong block (S đỏ, H xanh lá…), còn layer dùng để lọc và thống kê. Nếu bản vẽ của người dùng đã có quy ước riêng, **theo quy ước của họ**: truyền `--layer-phong`, `--loc-layer`, hoặc sửa `KY_HIEU` trong `ky_hieu.py`.

| Layer | Màu (ACI) | Nét | Nội dung |
| --- | --- | --- | --- |
| (nền kiến trúc) | 8 | mảnh nhất | `trinh_bay.lam_mo_kien_truc(doc)` đổi mọi layer không phải PCCC sang xám |
| PCCC-PHONG | 8 | | Polyline KÍN bao từng phòng, đầu vào cho script rải. Đóng băng khi in |
| PCCC-SPR | 1 | | Đầu phun sprinkler (`PCCC_SPR`) |
| PCCC-ONG-SPR-D25, -D32, -D40 | 6 (tím) | 0,13 | Đường tim ống nhánh, một nét |
| PCCC-ONG-SPR-D50 … -D100 | 1 (đỏ) | 0,18 | Đường tim ống chính |
| PCCC-VIEN-ONG | 1 | 0,50 | Hai nét viền của ống DN ≥ 50 (không tính chiều dài) |
| PCCC-ONG-HONG-Dxx | như trên | | Ống cấp họng vách tường |
| PCCC-TEXT-DN | 6 | | Nhãn "DN25", 1,8 mm giấy |
| PCCC-HONG | 1 | | Hộp họng FHR (`PCCC_FHR`), họng tiếp nước |
| PCCC-BINH | 1 | | Bình ABC, CO2, tủ dụng cụ phá dỡ |
| PCCC-BAO-KHOI | 1 | | Đầu báo khói "S" (`PCCC_DBK`) |
| PCCC-BAO-NHIET | 3 | | Đầu báo nhiệt "H" (`PCCC_DBN`) |
| PCCC-NUT-AN | 3 | | Nút nhấn khẩn |
| PCCC-CHUONG-DEN | 3 | | Chuông + đèn, đèn báo cháy phòng |
| PCCC-TU-BC | 1 | | Tủ trung tâm FACP, đèn FIRE ngoài nhà |
| PCCC-CAP-BC | 6 | DASHED 0,30 | Cáp báo cháy chống cháy |
| PCCC-EXIT | 3 | | EXIT, đèn sự cố, SDTNP, mặt nạ |
| PCCC-DIM | 173 | 0,30 | Dim thiết bị, style `PCCC` (chữ đỏ 4,2 mm, gạch chéo) |
| PCCC-BAN-KINH | 173 | DASHED | Vòng bán kính phục vụ họng nước |
| PCCC-TEXT | 7 | | Ghi chú, bảng |
| PCCC-KHUNG | 7 | 0,5 | Khung tên A3 |
| PCCC-CU | 8 | | Ký hiệu cũ của bản vẽ hiện trạng (đóng băng, không xoá) |

Mẹo:
- Ống vẽ bằng `ky_hieu.ve_ong(msp, diem, "spr", dn)`. Hàm này tự đặt layer theo DN, thêm viền cho ống lớn và ghi nhãn DN. `thong_ke.py --loc-layer PCCC-ONG` tách chiều dài theo từng DN.
- Block định nghĩa theo mm giấy và chèn với hệ số = tỷ lệ in. Đặt `ky_hieu.TY_LE` (hoặc truyền `ty_le`) đúng tỷ lệ của tờ, nếu không ký hiệu sẽ to hoặc nhỏ sai.
