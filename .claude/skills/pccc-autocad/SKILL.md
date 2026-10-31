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
| `references/trinh-bay-ban-ve.md` | **Đọc trước khi vẽ bất kỳ tờ nào.** Quy cách trình bày theo hồ sơ mẫu đã duyệt: thứ tự tờ, bố cục A3, màu nét, ký hiệu, cách dim từng hệ, ghi chú và bảng mẫu, lỗi cần tránh |
| `references/layer-ky-hieu.md` | Đọc khi vẽ mới, khi tạo layer/block, hoặc khi bản vẽ của người dùng không theo quy ước |
| `scripts/thong_so.json` | Bảng số liệu mà script dùng. Nếu người dùng sửa số theo bản gốc tiêu chuẩn thì sửa ở đây |
| `scripts/rai_thiet_bi.py` | Rải sprinkler / đầu báo khói / đầu báo nhiệt trong các polyline phòng |
| `scripts/thong_ke.py` | Thống kê block, chiều dài, diện tích từ nhiều DXF/DWG ra Excel |
| `scripts/ky_hieu.py` | **Bộ ký hiệu thống nhất** theo hồ sơ mẫu (block, layer, kiểu chữ), vẽ ống `ve_ong`, bảng "GHI CHÚ:" ký hiệu. Mọi thiết bị đều phải chèn qua module này |
| `scripts/trinh_bay.py` | Quy cách tờ: dim style `PCCC`, `dim_theo_truc` (sprinkler), `dim_dau_bao` (báo cháy), vòng bán kính họng, khung A3 + cột tên, tiêu đề, ghi chú, bảng bình chữa cháy, bảng khối tích, tờ phân cách hạng mục |
| `scripts/so_do.py` | Sơ đồ nguyên lý báo cháy (zone theo tầng, mạch chuông, bảng tính ắc quy Phụ lục C TCVN 7568-14:2025), chữa cháy (trục đứng, nhánh tầng, trạm bơm, bể, họng tiếp nước, bảng ký hiệu và thông số bơm), đèn sự cố và chỉ dẫn thoát nạn. Số lượng lấy từ mặt bằng |
| `scripts/acad_msp.py` | Model space AutoCAD qua COM có API giống ezdxf: truyền vào các hàm `ky_hieu`/`trinh_bay`/`so_do` để vẽ thẳng lên bản vẽ đang mở |
| `scripts/ong.py` | Đi ống sprinkler kiểu xương cá (trục đứng → ống chính → nhánh) và chọn DN sơ bộ theo số đầu phun phía sau |
| `scripts/thuy_luc.py` | Tính thuỷ lực sơ bộ: vùng tính toán xa trục nhất, Hazen–Williams, cân bằng lưu lượng tại điểm rẽ; áp lực bơm; họng nước. Giả thiết nằm ở `thong_so.json` → `thuy_luc` |
| `scripts/tim_phong.py` | Tự dựng polyline phòng từ nét tường, cột và cửa. Dùng khi bản vẽ nhập từ PDF hoặc chưa có polyline phòng |
| `scripts/acad_com.py` | Tiện ích COM dùng chung (kết nối, thử lại khi AutoCAD bận, tạo layer/block) |

Chạy script bằng đường dẫn tuyệt đối tới thư mục `scripts/` của skill. Mỗi script có `--help`.

## Quy cách trình bày (bắt buộc)

Người dùng đã chốt hồ sơ **KS 32 Dã Tượng** (khách sạn 8 tầng, 33 tờ A3) làm chuẩn trình bày cho mọi dự án. Đọc `references/trinh-bay-ban-ve.md` trước khi vẽ. Tóm tắt:
- **A3 ngang, mặt bằng 1:125**, khung cách mép 5/4 mm, cột thông tin bên phải rộng 41,6 mm (`trinh_bay.khung_a3`). Tên người, công ty và logo lấy từ người dùng, không tự điền.
- Góc trên-trái: ghi chú chung của hệ. Dưới mặt bằng, ở giữa: "MẶT BẰNG TẦNG …" (5,35 mm). Góc dưới-trái: bảng "GHI CHÚ:" ký hiệu. Góc dưới-phải: hộp ghi chú tiêu chuẩn (khung đỏ), hoặc bảng bình chữa cháy ở tờ chữa cháy.
- Nền kiến trúc chuyển xám (`lam_mo_kien_truc`). Thiết bị theo màu bản mẫu. Dim thiết bị chữ **đỏ** 4,2 mm, nét và gạch chéo **xanh tím** (ACI 173).
- Sprinkler, họng và bình nằm **chung một tờ** chữa cháy. Ống chính DN ≥ 50 vẽ hai nét đỏ, nhánh một nét tím, nhãn DN tím xoay theo ống (`ky_hieu.ve_ong`).
- Bộ hồ sơ có đủ: bìa → vị trí + quy mô → mặt cắt → [báo cháy] → [chữa cháy] → [chiếu sáng sự cố] → [điện PCCC]. Mỗi hạng mục mở đầu bằng tờ phân cách "HẠNG MỤC: …".
- Trước khi xuất, **đối chiếu chéo** số liệu giữa các tờ: tổng khối tích, số thiết bị trên sơ đồ nguyên lý so với mặt bằng, thông số bơm và thể tích bể ở thuyết minh, sơ đồ và bảng tính. Bản mẫu từng sai ở đúng các chỗ này (mục 9 của tài liệu tham chiếu).

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
- Nếu dò tự động hỏng (vách ngăn vẽ không liền nét, rèm cửa nằm chung layer cửa, như dự án 34 NVM), khai báo phòng bằng tay: mỗi phòng là hợp các hình chữ nhật trừ WC, thang, rồi bắt dính mép vào mặt tường thật (xem `du_an/ks-mini-34nvm/phong_tay.py`). Đọc toạ độ từ ảnh tường có lưới 500 mm.
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

**Ký hiệu thống nhất:** chỉ dùng block trong `ky_hieu.py` (mô phỏng hồ sơ mẫu): "S" đỏ trong vòng tròn là đầu báo khói, "H" xanh lá là đầu báo nhiệt, sprinkler là hai vòng tròn đồng tâm có dấu chéo màu đỏ, hộp họng "FHR" luôn kèm 1 bình ABC + 1 bình CO2. Block tính theo mm giấy: đặt `ky_hieu.TY_LE` bằng tỷ lệ in của tờ trước khi chèn. Không tự tạo block riêng ở từng script. Mỗi tờ mặt bằng đặt một bảng ký hiệu bằng `ky_hieu.ve_bang`, chỉ gồm các thiết bị có trên tờ đó. Ký hiệu cũ của bản vẽ thì chuyển sang layer `PCCC-CU` và đóng băng, không xoá.

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
- Dim nằm trên layer `PCCC-DIM`, style `PCCC` của `trinh_bay.dam_bao` (chữ đỏ, gạch chéo xanh tím, chữ trên đường dim), cỡ chữ theo `--ty-le`. Hồ sơ mẫu in 1:125.
- **Kiểu dim theo hồ sơ mẫu, dùng khi dựng tờ hoàn chỉnh:**
  - Đầu báo: `trinh_bay.dim_dau_bao`, gồm 2 dim vuông góc tới tường gần nhất và 1 dim chéo tới góc phòng. **Dim chéo chỉ ghi khi ≤ 7,2 m (đầu báo khói) hoặc ≤ 5,1 m (đầu báo nhiệt)**: chọn góc xa nhất trong giới hạn; dài hơn thì không ghi (quy ước của người dùng, theo TCVN 7568-1:2025 Hình 2/7). Góc xa nhất vượt giới hạn thì báo trong cảnh báo. Phòng có hàng từ 3 đầu báo thẳng hàng trở lên, hoặc phòng dạng hành lang: dim **chuỗi** tường → đầu báo → … → tường dọc hàng, thêm 1 dim vuông góc và dim chéo ở hai đầu hàng (`trinh_bay.dim_bao_chay_phong`, xử lý cả phòng). `rai_thiet_bi.py` đã dùng cách này cho đầu báo.
  - Sprinkler: `trinh_bay.dim_theo_truc`, chuỗi đặt **ngoài nhà** dưới hàng dim trục, đi qua trục lưới và các cột đầu phun; chuỗi dọc tương tự ở cạnh nhà; hành lang thì dim chuỗi dọc ống chính. Chuỗi tường → đầu phun → tường của `rai_thiet_bi.py` chỉ dùng cho phòng lớn không chia.
  - Họng nước: `trinh_bay.vong_phuc_vu`, vòng nét đứt bán kính bằng chiều dài vòi.

Chỉ dùng `--khong-dim` khi người dùng nói rõ là không cần. Khi đặt thiết bị bằng cách khác (vẽ tay qua COM, AutoLISP, họng nước, bình chữa cháy…), cũng phải tự thêm dim theo cùng quy tắc trên. Script không xét dầm, cột, đèn, miệng gió hay vật cản. Hãy nói rõ điều này khi báo kết quả.

### 3b. Đường ống
- **Sprinkler:** trục đứng đặt cạnh thang chính. Ống chính chạy theo hàng đầu phun hành lang. Ống nhánh vuông góc tới từng cột đầu phun; các đầu cùng hoành độ dùng chung nhánh. Van khống chế kèm công tắc dòng chảy đặt ở chỗ rẽ từ trục đứng. Mỗi DN vẽ trên một layer riêng (`PCCC-ONG-SPR-D25`…) để thống kê.
- **Họng nước:** trục đứng DN100 cạnh hộp, nhánh DN50 vào hộp. Tầng có phòng bơm thì thêm ống cấp DN100 từ trạm bơm tới chân trục.
- **Vị trí hộp họng (quy ước của người dùng):** đặt ở lối đi chung, dễ tiếp cận: gắn lên tường lõi chung (tường thang máy, tường buồng thang), quay mặt ra sảnh hoặc hành lang. Không đặt trong phòng, sát cửa phòng hay trong tầm mở cánh cửa. Giữ cùng toạ độ ở mọi tầng để trục đứng thẳng. Xem ảnh kiểm tra để chắc hộp không nằm trong cung mở cửa.
- DN ghi phía dưới hoặc bên phải ống, vì chữ dim nằm phía trên trùng tuyến ống. Ghi chú trục đứng đặt sau tường, ngoài hành lang. Trục đứng được dim tới trục lưới gần nhất.
- **Luôn nói rõ** đường kính chỉ là chọn sơ bộ theo bảng ống nguy cơ thấp. TCVN 7336 yêu cầu tính thuỷ lực (áp lực và lưu lượng tại đầu bất lợi nhất, chọn bơm, bể) trước khi thi công.

### 3b2. Sơ đồ nguyên lý
- Mỗi hệ một tờ, dùng `so_do.bao_chay`, `so_do.chua_chay`, `so_do.chieu_sang` sau khi đã vẽ `trinh_bay.khung_a3`.
- **Số lượng phải đếm từ mặt bằng đã dựng**, không chép từ hồ sơ cũ. Bản mẫu từng ghi x09 đầu khói/tầng trên sơ đồ trong khi mặt bằng có 13, nên bảng ắc quy cũng sai theo.
- Dòng điện thiết bị dùng tính ắc quy (`so_do.DONG_THIET_BI`) đang lấy theo hồ sơ mẫu. Phải nhắc người dùng thay bằng số trong catalogue thiết bị thực tế.
- Thông số bơm và thể tích bể trên sơ đồ phải **trùng** với thuyết minh và bảng tính thuỷ lực.

### 3c. Thuỷ lực sơ bộ, bơm và bể
- Chạy `thuy_luc.tinh_tang_spr` cho **từng tầng** trên mạng ống đã vẽ, rồi `ap_luc_bom_spr` với cao độ sàn lấy từ mặt cắt. Tầng bất lợi là tầng cần áp lực bơm lớn nhất, thường là tầng trên cùng đủ diện tích tính toán.
- Họng nước: `tinh_hong` cho hộp họng cao nhất.
- Bơm chung cho cả hai hệ chạy đồng thời: Q = Q sprinkler + Q họng; H = lớn nhất của hai hệ × hệ số dự trữ. Kèm 1 bơm dự phòng và 1 bơm bù áp.
- Bể: Q sprinkler × thời gian theo nhóm + Q họng × thời gian chữa cháy họng. Ghi rõ là chưa gồm nước chữa cháy ngoài nhà.
- Trong báo cáo phải liệt kê **mọi giả thiết** (K đầu phun, áp tối thiểu, số cột nước, áp tại van họng, thời gian) và nhắc người dùng đối chiếu với TCVN 7336:2021 và QCVN 06:2022. Kết quả chỉ để chọn thiết bị ban đầu.

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
- `SelectionSet.Select` kiểu cửa sổ (window/crossing) chỉ bắt được đối tượng **đang hiện trên màn hình**. Phải `ZoomWindow` tới vùng cần chọn trước, nếu không sẽ chọn thiếu mà không báo lỗi. Muốn chọn toàn bản vẽ theo layer thì dùng kiểu 5 (all) kèm bộ lọc.
- Đối tượng tạo qua COM nhận màu/nét hiện hành (CECOLOR, CELTYPE). `acad_msp.MSP` đã tự đặt ByLayer; nếu vẽ COM bằng code khác thì phải tự đặt `Color = 256`.
- Dựng cả tờ trực tiếp trong AutoCAD: `acad_msp.nap_thu_vien(doc, ty_le)` rồi truyền `acad_msp.MSP(doc)` vào các hàm của `ky_hieu`/`trinh_bay` thay cho msp của ezdxf. Muốn vẽ vào paper space của một layout thì đặt `msp.ms = layout.Block`.
- **Bản vẽ kiến trúc dạng xref:** kiểm tra `Block.IsXRef` và số đối tượng trước khi làm. Xref rỗng nghĩa là thiếu file, phải xin thư mục xref (hoặc bản đã Bind/eTransmit). Muốn đọc hình học bằng ezdxf thì Bind trong một bản sao rồi SaveAs DXF; tường thường nằm trong block lồng, phải phá block đệ quy và bỏ layer `... @ tỷ lệ` (bản sao ký hiệu theo annotation scale).
- **Đóng rồi mở bản vẽ qua COM:** đóng bản vẽ đang kích hoạt trước rồi mới `Documents.Open` có thể làm AutoCAD báo "Invalid execution context" và treo (phải tắt AutoCAD). Mở bản mới trước, rồi mới đóng bản cũ.
- Sau `doc.ActiveLayout = ...` phải lấy lại `acad.ActiveDocument`; tham chiếu cũ báo lỗi ở `PaperSpace`. Không xoá viewport tổng của layout mới (Layouts.Add + CopyFrom chỉ chép thiết lập in).
- Viewport mới chỉ kích hoạt được (`MSpace`, `ActivePViewport`) khi đang hiện trên màn hình giấy: `ZoomWindow` paper space tới khung trước, rồi `ZoomCenter(tâm, chiều cao = 297 × tỷ lệ)` để được đúng 1:tỷ lệ.
- In PDF: đặt `ConfigName` làm khổ giấy về mặc định (ANSI A). Sau khi đổi máy in phải đặt lại `CanonicalMediaName` (ISO_full_bleed_A3), cửa sổ in, tỷ lệ 1:1; `PlotToFile(f, "DWG To PDF.pc3")` không cần đổi ConfigName.
- Bản vẽ khách sạn cải tạo hành lang chỉ rộng ~1,0 m: khép lỗ cửa bằng ngưỡng khe đơn thuần (≤ 1 m) sẽ lấp luôn hành lang. Nên chỉ khép khe nằm trong tầm cung cửa, cộng khe < 0,8 m (cửa trượt/xếp).
