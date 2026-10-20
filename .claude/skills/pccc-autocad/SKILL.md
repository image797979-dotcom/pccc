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
| `scripts/ky_hieu.py` | **Bộ ký hiệu thống nhất** (block, layer, kiểu chữ Arial) và bảng ký hiệu. Mọi thiết bị đều phải chèn qua module này |
| `scripts/tim_phong.py` | Tự dựng polyline phòng từ nét tường, cột và cửa. Dùng khi bản vẽ nhập từ PDF hoặc chưa có polyline phòng |
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

Nếu chưa có polyline phòng (thường gặp với bản vẽ nhập từ PDF), dùng `tim_phong.py` để dựng tự động.
- Cách làm: tô tường, cột và khung cửa sổ lên lưới 40 mm. Lỗ cửa được đóng bằng bán kính cung mở cửa nằm thẳng hàng với tường; cánh cửa không tính là vật cản. Vùng kín chính là phòng, tên phòng lấy từ chữ nằm trong vùng.
- Việc đầu tiên là dò layer tường/cửa của bản vẽ: vẽ từng layer một màu rồi xem ảnh. Bản vẽ PDF thường có tiền tố `PDFn_…$MB$` (hàm `_hau_to` đã bỏ tiền tố này).
- **Luôn xuất ảnh các phòng dò được để xem lại** trước khi rải thiết bị. Lỗi hay gặp:
  - Vách kính hoặc lan can vẽ trên layer khác: thêm layer đó vào nhóm vật cản.
  - Mặt ngoài nhà để trống: dùng `bao_theo_cot=True` để đóng biên theo hàng cột.
  - Sân mái bị nhận là phòng: loại vùng lớn không có tên.
  - Tên phòng nằm ngoài polygon: gán cho phòng gần nhất.
- Nếu mặt bằng nằm trong block (mỗi tầng một block, chèn nhiều lần cho nhiều bộ tờ), dò một lần trong toạ độ block rồi cộng thêm điểm chèn của từng lần chèn.

### 3. Rải thiết bị
```bash
python <skill>/scripts/rai_thiet_bi.py --com --loai sprinkler --nhom 2
python <skill>/scripts/rai_thiet_bi.py --dxf mat_bang.dxf --loai bao_khoi --tran 3.2 --ra mat_bang_bc.dxf
python <skill>/scripts/rai_thiet_bi.py --dxf mat_bang.dxf --loai bao_nhiet --tran 4 --chi-tinh
```
**Không bố trí đầu báo và sprinkler trong nhà vệ sinh và thang bộ** (quy ước của người dùng):
- WC nhận theo tên phòng (WC, VỆ SINH, TẮM). Phòng nhỏ không tên thì nhận theo thiết bị vệ sinh vẽ bên trong (layer `*VAT$DUNG*`); ở các tầng phòng ngủ, coi mọi vùng nhỏ không tên dưới 4 m² là WC hoặc hốc tủ.
- Thang bộ nhận theo dãy nét bậc thang (`tim_phong.vung_thang`). Cả buồng thang lẫn chiếu nghỉ được loại khỏi vùng bố trí, kể cả phần sảnh thang dính vào hành lang.
- Liệt kê các phòng đã bỏ qua trong báo cáo để người dùng kiểm tra lại.

**Ký hiệu thống nhất:** chỉ dùng block trong `ky_hieu.py`. Theo quy ước bản vẽ hiện trạng: "S" là đầu báo khói, "H" là đầu báo nhiệt; sprinkler là hình tròn có dấu chéo. Không tự tạo block riêng ở từng script. Mỗi tờ mặt bằng đặt một bảng ký hiệu bằng `ky_hieu.ve_bang`, chỉ gồm các thiết bị có trên tờ đó. Ký hiệu cũ của bản vẽ thì chuyển sang layer `PCCC-CU` và đóng băng, không xoá.

**Nguyên tắc bố trí (quy ước của người dùng, áp dụng cả khi tự đặt thiết bị không qua script):**
- **Đối xứng đều so với phòng:** các bước bằng nhau, hàng ngoài cùng cách tường đúng nửa bước, nên lưới đối xứng qua tâm phòng. Làm vậy bản vẽ gọn và dễ kiểm tra, và thi công đi ống thẳng hàng.
- **Sprinkler cách tường tối thiểu 500 mm**, đồng thời không quá nửa khoảng cách tối đa giữa các đầu.
- Phòng chữ L, U, T (các cạnh vuông góc): chia thành ít hình chữ nhật nhất, rồi mỗi hình chữ nhật rải lưới đối xứng riêng.
- Phòng có tường xiên: rải lưới theo hình bao rồi bổ sung cho vùng chưa phủ (vẫn giữ ≥ 500 mm). Kết quả không đối xứng hoàn toàn, nên báo người dùng kiểm tra.

Cách tính số hàng: chọn số hàng ít nhất sao cho bước ≤ khoảng cách tối đa, nửa bước ≤ khoảng cách tối đa tới tường, và diện tích mỗi thiết bị ≤ giới hạn. Script cảnh báo nếu thiết bị nào gần tường hơn 500 mm (phòng quá hẹp) hoặc hai đầu gần nhau hơn khoảng cách tối thiểu.

Nên chạy `--chi-tinh` trước để báo cho người dùng số lượng và bước lưới, rồi mới vẽ thật.

**Luôn ghi kích thước (dim) khoảng cách thiết bị.** Đây là quy ước bắt buộc của người dùng: bản vẽ PCCC nộp thẩm duyệt phải thể hiện được khoảng cách giữa các thiết bị và khoảng cách từ thiết bị tới tường để cán bộ thẩm duyệt kiểm tra với tiêu chuẩn. Script dim sẵn theo mặc định:
- Lưới đều: với mỗi hình chữ nhật của phòng, một chuỗi dim ngang qua hàng gần tâm và một chuỗi dim dọc qua cột gần tâm, đi từ tường → thiết bị → … → tường.
- Thiết bị bổ sung ở góc phòng: dim tới tường gần nhất theo cả hai phương.
- Dim nằm trên layer `PCCC-DIM`, style `PCCC` (vạch chéo, chữ trên đường dim), cỡ chữ theo `--ty-le` (mặc định 1:100).

Chỉ dùng `--khong-dim` khi người dùng nói rõ là không cần. Khi đặt thiết bị bằng cách khác (vẽ tay qua COM, AutoLISP, họng nước, bình chữa cháy…), cũng phải tự thêm dim theo cùng quy tắc trên. Script không xét dầm, cột, đèn, miệng gió hay vật cản. Hãy nói rõ điều này khi báo kết quả.

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
- Số thiết bị theo từng phòng và tổng số, bước lưới thực tế, số kích thước đã ghi.
- **Nguồn số liệu**: tên tiêu chuẩn, bảng hoặc dòng đã dùng (script in sẵn dòng "Thông số: …").
- Các cảnh báo của script (vùng bổ sung, khoảng cách quá gần) và những gì script không xét (vật cản, dầm, trần nghiêng).
- Một câu nhắc: số liệu cần đối chiếu bản gốc tiêu chuẩn hiện hành và để kỹ sư PCCC kiểm tra trước khi thẩm duyệt.

## Lưu ý kỹ thuật trên Windows
- AutoCAD hay báo `Call was rejected by callee` khi đang khởi động hoặc bận. Luôn gọi COM qua `goi_lai()` và `cho_san_sang()` trong `acad_com.py`. Đừng gọi trực tiếp.
- Toạ độ truyền vào COM phải là `VARIANT` mảng double: dùng `diem()` và `mang_2d()`.
- Nếu Claude chạy từ bản cài Microsoft Store, thư mục `AppData\Roaming` bị ảo hoá: file ghi bằng công cụ Write có thể không thấy được từ PowerShell. Khi gặp lỗi "không tìm thấy file", hãy chạy script bằng đường dẫn thật trong `AppData\Local\Packages\Claude_*\LocalCache\Roaming\...`, hoặc đặt file ngoài AppData.
- Khi in tiếng Việt ra console mà bị lỗi mã hoá, đặt `PYTHONIOENCODING=utf-8`.
