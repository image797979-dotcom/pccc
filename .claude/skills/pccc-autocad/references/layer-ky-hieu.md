# Quy ước layer và ký hiệu PCCC

Dùng thống nhất bộ layer này để các script rải thiết bị và thống kê nhận đúng đối tượng. Nếu bản vẽ của người dùng đã có quy ước riêng, **theo quy ước của họ**: chỉ cần truyền `--layer-phong`, `--loc-layer` hoặc sửa phần `ky_hieu` trong `scripts/thong_so.json`.

| Layer | Màu (ACI) | Nội dung |
| --- | --- | --- |
| PCCC-PHONG | 8 | Polyline KÍN bao từng phòng/khu vực, là đầu vào cho script rải |
| PCCC-SPR | 1 (đỏ) | Đầu phun sprinkler (block `PCCC_SPR`) |
| PCCC-ONG-SPR | 1 | Ống nhánh, ống chính sprinkler |
| PCCC-ONG-HONG | 5 (xanh dương) | Ống cấp nước họng vách tường |
| PCCC-HONG | 5 | Họng nước vách tường (block `PCCC_HONG`) |
| PCCC-BAO-KHOI | 6 (tím) | Đầu báo khói (block `PCCC_DBK`) |
| PCCC-BAO-NHIET | 30 (cam) | Đầu báo nhiệt (block `PCCC_DBN`) |
| PCCC-NUT-AN | 6 | Nút ấn báo cháy (block `PCCC_NA`) |
| PCCC-CHUONG-DEN | 6 | Chuông, đèn báo cháy (block `PCCC_CD`) |
| PCCC-CAP-BC | 6 | Cáp tín hiệu báo cháy |
| PCCC-TU-BC | 6 | Tủ trung tâm báo cháy |
| PCCC-BINH | 3 (xanh lá) | Bình chữa cháy (block `PCCC_BINH`) |
| PCCC-EXIT | 2 (vàng) | Đèn Exit, đèn sự cố |
| PCCC-TEXT | 7 | Ghi chú, ký hiệu chữ |
| PCCC-DIM | 7 | Kích thước |

Mẹo:
- Ống và cáp nên vẽ bằng LINE hoặc LWPOLYLINE hở, mỗi đường kính một layer con (ví dụ `PCCC-ONG-SPR-D25`, `PCCC-ONG-SPR-D50`). Khi đó `thong_ke.py --loc-layer PCCC-ONG` tách được chiều dài theo từng đường kính.
- Phòng hình chữ L hoặc chữ U vẫn vẽ thành một polyline kín. Script tự bổ sung thiết bị cho vùng góc, nhưng nên kiểm tra lại bằng mắt.
- Block thiết bị nên tạo ở layer 0 bên trong định nghĩa block, rồi chèn vào layer PCCC-… tương ứng. Như vậy màu đi theo layer.
