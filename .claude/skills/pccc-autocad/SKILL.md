---
name: pccc-autocad
description: Vẽ và kiểm tra bản vẽ phòng cháy chữa cháy (PCCC) trong AutoCAD theo tiêu chuẩn Việt Nam (QCVN 06:2022, TCVN 7336 sprinkler, TCVN 5738 báo cháy, TCVN 3890 bình chữa cháy). Gồm rải tự động đầu phun sprinkler, đầu báo khói và đầu báo nhiệt trong phòng, thống kê khối lượng (đếm thiết bị, chiều dài ống/cáp, diện tích) ra Excel, xử lý hàng loạt file DWG/DXF, và quy ước layer/ký hiệu PCCC. Dùng skill này mỗi khi người dùng nhắc tới PCCC, chữa cháy, báo cháy, sprinkler, đầu phun, đầu báo, họng nước, bình chữa cháy, thẩm duyệt PCCC, hoặc muốn vẽ, bố trí hay bóc khối lượng hệ thống chữa cháy trên bản vẽ CAD, kể cả khi họ không nói rõ tên tiêu chuẩn.
---

# PCCC trong AutoCAD theo TCVN/QCVN

Skill này giúp kỹ sư PCCC làm nhanh các việc lặp lại trên bản vẽ: rải thiết bị theo khoảng cách tiêu chuẩn, đếm và bóc khối lượng, chuẩn hoá layer. Phần **quyết định thiết kế** (phân nhóm nguy hiểm cháy, có bắt buộc trang bị hay không, tính thuỷ lực) vẫn thuộc về kỹ sư. Mọi con số skill đưa ra chỉ là đề xuất, cần người có chứng chỉ kiểm tra trước khi nộp thẩm duyệt.

## Tệp trong skill

| Tệp | Khi nào đọc / chạy |
| --- | --- |
| `references/tieu-chuan.md` | Đọc **trước** khi đưa ra bất kỳ con số tiêu chuẩn nào (khoảng cách, diện tích, cường độ phun) |
| `references/layer-ky-hieu.md` | Đọc khi vẽ mới, khi tạo layer/block, hoặc khi bản vẽ của người dùng không theo quy ước |
| `scripts/thong_so.json` | Bảng số liệu mà script dùng. Nếu người dùng sửa số theo bản gốc tiêu chuẩn thì sửa ở đây |
| `scripts/rai_thiet_bi.py` | Rải sprinkler / đầu báo khói / đầu báo nhiệt trong các polyline phòng |
| `scripts/thong_ke.py` | Thống kê block, chiều dài, diện tích từ nhiều DXF/DWG ra Excel |
| `scripts/acad_com.py` | Tiện ích COM dùng chung (kết nối, thử lại khi AutoCAD bận, tạo layer/block) |

Chạy script bằng đường dẫn tuyệt đối tới thư mục `scripts/` của skill. Mỗi script có `--help`.

## Quy trình

### 1. Hỏi đủ thông tin trước khi vẽ
Kết quả bố trí phụ thuộc hoàn toàn vào các thông số dưới đây. Đoán sai thì cả bản vẽ sai, nên khi người dùng chưa nói thì hỏi:
- **Hệ thống** cần làm: sprinkler, báo cháy (khói/nhiệt), họng nước, bình chữa cháy?
- **Sprinkler:** nhóm nguy hiểm cháy của phòng (1, 2, 3, 4.1…) theo phụ lục TCVN 7336. Có thể gợi ý nhóm dựa trên công năng, nhưng để người dùng chốt.
- **Báo cháy:** chiều cao trần từng khu vực.
- **Bản vẽ:** file DXF/DWG nào, hay bản vẽ đang mở trong AutoCAD? Đơn vị là mm hay m? Phòng đã có polyline kín bao quanh chưa, nằm trên layer nào?

### 2. Chọn cách làm việc với bản vẽ
- **AutoCAD đang mở (COM, `--com`):** người dùng thấy kết quả ngay trên màn hình. Cần Windows và AutoCAD bản đầy đủ (bản LT không có COM). Cài thư viện: `pip install pywin32`.
- **File DXF (ezdxf, `--dxf`):** không cần mở AutoCAD, chạy nhanh, hợp với xử lý hàng loạt. Cài: `pip install ezdxf`. File DWG thì mở bằng COM, hoặc nhờ người dùng lưu sang DXF.
- **AutoLISP:** khi người dùng muốn một lệnh gõ được ngay trong AutoCAD, hoặc dùng AutoCAD LT 2024 trở lên (LT chạy được LISP nhưng không có COM). Viết file `.lsp`, hướng dẫn nạp bằng `APPLOAD`.

Nếu chưa có polyline phòng, hỏi người dùng có muốn tự vẽ trên layer `PCCC-PHONG` không. Nếu bản vẽ kiến trúc có sẵn layer tường/phòng thì đề xuất lấy từ đó, nhưng phải xác nhận trước khi dùng.

### 3. Rải thiết bị
```bash
python <skill>/scripts/rai_thiet_bi.py --com --loai sprinkler --nhom 2
python <skill>/scripts/rai_thiet_bi.py --dxf mat_bang.dxf --loai bao_khoi --tran 3.2 --ra mat_bang_bc.dxf
python <skill>/scripts/rai_thiet_bi.py --dxf mat_bang.dxf --loai bao_nhiet --tran 4 --chi-tinh
```
Cách tính: chia lưới đều trong hình bao của phòng sao cho bước ≤ khoảng cách tối đa, khoảng cách tới tường ≤ giới hạn, và diện tích mỗi thiết bị ≤ giới hạn. Sau đó giữ lại các điểm nằm trong phòng, rồi bổ sung thiết bị cho các vùng góc chưa phủ (phòng chữ L, chữ U).

Nên chạy `--chi-tinh` trước để báo cho người dùng số lượng và bước lưới, rồi mới vẽ thật. Script không xét dầm, cột, đèn, miệng gió hay vật cản. Hãy nói rõ điều này khi báo kết quả.

### 4. Thống kê khối lượng
```bash
python <skill>/scripts/thong_ke.py thu_muc_ban_ve/ --loc-layer PCCC- --ra khoi_luong.xlsx
python <skill>/scripts/thong_ke.py --com-dang-mo --ra khoi_luong.xlsx
```
File Excel có 4 sheet: block theo bản vẽ và layer, chiều dài theo layer (m), diện tích vùng kín (m²), và tổng hợp block của mọi bản vẽ. Muốn tách ống theo đường kính thì mỗi đường kính phải nằm trên một layer riêng (xem `layer-ky-hieu.md`).

### 5. Xử lý hàng loạt DWG
Với việc khác ngoài thống kê (đổi tên layer, thay block khung tên, xuất PDF, chuẩn hoá màu…), viết script mới dựa trên `acad_com.py`. Mở từng file bằng `Documents.Open`, làm việc, lưu, đóng. Trước khi chạy:
- Làm thử trên **1 file** và cho người dùng xem kết quả.
- Lưu ra file mới hoặc nhắc người dùng sao lưu. Ghi đè hàng loạt bản vẽ thì không hoàn tác được.

### 6. Báo kết quả
Trả lời bằng tiếng Việt, gồm:
- Số thiết bị theo từng phòng và tổng số, bước lưới thực tế.
- **Nguồn số liệu**: tên tiêu chuẩn, bảng hoặc dòng đã dùng (script in sẵn dòng "Thông số: …").
- Các cảnh báo của script (vùng bổ sung, khoảng cách quá gần) và những gì script không xét (vật cản, dầm, trần nghiêng).
- Một câu nhắc: số liệu cần đối chiếu bản gốc tiêu chuẩn hiện hành và để kỹ sư PCCC kiểm tra trước khi thẩm duyệt.

## Lưu ý kỹ thuật trên Windows
- AutoCAD hay báo `Call was rejected by callee` khi đang khởi động hoặc bận. Luôn gọi COM qua `goi_lai()` và `cho_san_sang()` trong `acad_com.py`. Đừng gọi trực tiếp.
- Toạ độ truyền vào COM phải là `VARIANT` mảng double: dùng `diem()` và `mang_2d()`.
- Nếu Claude chạy từ bản cài Microsoft Store, thư mục `AppData\Roaming` bị ảo hoá: file ghi bằng công cụ Write có thể không thấy được từ PowerShell. Khi gặp lỗi "không tìm thấy file", hãy chạy script bằng đường dẫn thật trong `AppData\Local\Packages\Claude_*\LocalCache\Roaming\...`, hoặc đặt file ngoài AppData.
- Khi in tiếng Việt ra console mà bị lỗi mã hoá, đặt `PYTHONIOENCODING=utf-8`.
