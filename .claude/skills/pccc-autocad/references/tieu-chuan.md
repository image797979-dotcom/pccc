# Tiêu chuẩn PCCC Việt Nam: số liệu dùng khi vẽ

> **Lưu ý quan trọng:** Các số dưới đây là giá trị tham khảo, được tóm tắt để vẽ và bố trí sơ bộ. Tiêu chuẩn được sửa đổi thường xuyên. Trước khi đưa vào hồ sơ thẩm duyệt, phải đối chiếu **bản gốc hiện hành** và để kỹ sư PCCC có chứng chỉ kiểm tra. Khi trả lời người dùng, luôn ghi rõ con số lấy từ đâu và nhắc họ đối chiếu.

## Mục lục
1. Văn bản áp dụng
2. Sprinkler (TCVN 7336:2021)
3. Báo cháy tự động (TCVN 5738:2021)
4. Họng nước chữa cháy vách tường
5. Bình chữa cháy xách tay (TCVN 3890)
6. Những gì skill KHÔNG tự quyết

## 1. Văn bản áp dụng

| Văn bản | Nội dung chính |
| --- | --- |
| Luật PCCC và CNCH số 55/2024/QH15 (hiệu lực 01/7/2025) và các nghị định hướng dẫn | Khung pháp lý, thẩm duyệt, nghiệm thu |
| QCVN 06:2022/BXD (và Sửa đổi 1:2023) | An toàn cháy cho nhà và công trình: bậc chịu lửa, lối thoát nạn, ngăn cháy, phân nhóm nguy hiểm cháy F |
| TCVN 7336:2021 | Hệ thống sprinkler tự động: thiết kế và lắp đặt |
| TCVN 5738:2021 | Hệ thống báo cháy tự động: yêu cầu kỹ thuật |
| TCVN 3890:2023 | Phương tiện PCCC cho nhà và công trình: trang bị, bố trí |
| TCVN 2622:1995 | Một phần yêu cầu cấp nước chữa cháy, đã được QCVN 06 thay thế phần lớn. Chỉ dùng phần còn hiệu lực |

Nhóm nguy hiểm cháy của phòng (nhóm 1, 2, 3, 4.1, 4.2...) để chọn thông số sprinkler nằm trong **phụ lục của TCVN 7336:2021**. Ví dụ thường gặp (phải kiểm tra lại theo phụ lục):
- Nhóm 1: văn phòng, khách sạn, bệnh viện, trường học, nhà ở (các phòng không chứa nhiều chất cháy).
- Nhóm 2: gara/bãi đỗ xe, nhà hàng, kho hàng nhỏ, sản xuất chế biến gỗ/dệt nhẹ…
- Nhóm 3 trở lên: kho hàng hoá cháy được chất cao, sản xuất cao su, nhựa…

Khi người dùng không nói rõ nhóm, **hỏi lại**, không tự đoán.

## 2. Sprinkler (TCVN 7336:2021), hệ nước

| Nhóm | Cường độ phun (l/s.m²) | Diện tích tính toán (m²) | Thời gian (phút) | Diện tích tối đa mỗi đầu (m²) | Khoảng cách tối đa giữa các đầu (m) |
| --- | --- | --- | --- | --- | --- |
| 1 | 0,08 | 60 | 30 | 12 | 4 |
| 2 | 0,12 | 120 | 60 | 12 | 4 |
| 3 | 0,24 | 120 | 60 | 12 | 4 |
| 4.1 | 0,30 | 180 | 60 | 12 | 4 |

Từ nhóm 4.2 trở lên, hệ bọt và các nhóm đặc biệt: tra bản gốc, chưa có trong `thong_so.json`.

Quy tắc bố trí hay dùng:
- Khoảng cách từ đầu phun tới tường ≤ 1/2 khoảng cách giữa các đầu.
- **Quy ước của người dùng:** đầu phun cách tường **tối thiểu 500 mm**, bố trí **đối xứng đều** so với phòng (`cach_tuong_min_m` trong `thong_so.json`).
- Khoảng cách tối thiểu giữa hai đầu phun là khoảng 1,5 m, để đầu này không làm ướt đầu kia.
- Tấm dội cách trần khoảng 0,08–0,30 m. Có dầm hoặc vật cản thì xét riêng.
- Lưu lượng tính toán sơ bộ: Q = cường độ × diện tích tính toán. Ví dụ nhóm 2: 0,12 × 120 = 14,4 l/s.

## 3. Báo cháy tự động (TCVN 5738:2021)

**Đầu báo khói điểm**

| Chiều cao trần (m) | Diện tích bảo vệ tối đa 1 đầu (m²) | Khoảng cách tối đa giữa các đầu (m) | Khoảng cách tối đa tới tường (m) |
| --- | --- | --- | --- |
| ≤ 3,5 | 85 | 9,0 | 4,5 |
| > 3,5 đến 6 | 70 | 8,5 | 4,0 |
| > 6 đến 10 | 65 | 8,0 | 4,0 |
| > 10 đến 12 | 55 | 7,5 | 3,5 |

**Đầu báo nhiệt điểm**

| Chiều cao trần (m) | Diện tích bảo vệ tối đa 1 đầu (m²) | Khoảng cách tối đa giữa các đầu (m) | Khoảng cách tối đa tới tường (m) |
| --- | --- | --- | --- |
| ≤ 3,5 | 25 | 5,0 | 2,5 |
| > 3,5 đến 6 | 20 | 4,5 | 2,0 |
| > 6 đến 9 | 15 | 4,0 | 2,0 |

Các điểm khác cần nhắc người dùng (tra bản gốc để có con số chính xác):
- Số đầu báo tối thiểu trong mỗi phòng hoặc khu vực, nhất là khi tín hiệu báo cháy dùng để điều khiển hệ thống khác.
- Trần có dầm cao, trần giả hay sàn kỹ thuật thì phải bố trí thêm đầu báo trong khoang.
- Nút ấn báo cháy: đặt ở lối thoát nạn và chân cầu thang, chiều cao lắp đặt theo tiêu chuẩn.

## 4. Họng nước chữa cháy vách tường

- Tâm van họng đặt cao khoảng 1,25 m so với sàn.
- Số họng và số lăng phun cùng lúc, lưu lượng mỗi họng và bán kính hoạt động (chiều dài cuộn vòi + tầm phun đặc) lấy theo QCVN 06:2022 tuỳ loại và khối tích công trình. Tra bảng trong quy chuẩn.

## 5. Bình chữa cháy xách tay (TCVN 3890:2023)

- Số lượng và khoảng cách bố trí phụ thuộc mức nguy hiểm cháy và loại đám cháy (A, B, C, E…). Tra bảng trong tiêu chuẩn.
- Đặt ở nơi dễ thấy, dễ lấy, gần lối ra vào. Treo thì đỉnh bình không cao quá mức tiêu chuẩn cho phép.

## 6. Những gì skill KHÔNG tự quyết

- Phân nhóm nguy hiểm cháy F (QCVN 06) và nhóm sprinkler: người dùng phải xác nhận.
- Tính thuỷ lực chi tiết (tổn thất áp, chọn bơm, bể nước): chỉ tính sơ bộ và ghi rõ là sơ bộ.
- Việc có bắt buộc trang bị hệ thống hay không: phụ thuộc phụ lục của nghị định hiện hành, phải tra.
