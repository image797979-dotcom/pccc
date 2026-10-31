# Repo thiết kế PCCC trong AutoCAD

Repo gồm skill `pccc-autocad` (`.claude/skills/pccc-autocad/`) và script từng dự án (`du_an/<dự án>/`). Mở Claude Code tại thư mục này thì skill tự nạp. Mọi việc vẽ, bố trí, bóc khối lượng PCCC đều theo `SKILL.md` của skill.

## Quy ước làm việc của người dùng

- **Trình bày theo hồ sơ mẫu KS 32 Dã Tượng** (PDF 33 tờ A3, đã được duyệt): A3 ngang, mặt bằng 1:125, dim đỏ/xanh tím, dim chéo cho đầu báo, dim theo trục cho sprinkler. Quy cách đã rút vào `references/trinh-bay-ban-ve.md`, `scripts/trinh_bay.py`, `scripts/ky_hieu.py`. Bản gốc ở máy người dùng: `D:\dự án\căn hộ\KS 32 dã tượng.pdf` (font VNI; đổi sang Unicode bằng `du_an/ks-mini-34nvm/vni.py`).
- **Vẽ trực tiếp trong AutoCAD qua COM** để người dùng thấy quá trình. Mở AutoCAD sớm, không phân tích ngầm bằng ezdxf quá lâu. Luôn làm trên bản sao, không ghi đè bản vẽ gốc.
- **Mỗi hệ PCCC một file DWG riêng** (báo cháy; sprinkler; họng nước + bình; chiếu sáng sự cố), mỗi file kèm tờ sơ đồ nguyên lý và tờ thuyết minh. Bỏ khung tên của đơn vị kiến trúc, thay bằng khung A3 trống. Không tự điền tên người, công ty.
- **Thuyết minh** chép theo hồ sơ mẫu (quy mô, TM báo cháy, TM chữa cháy, TM chiếu sáng, TM điện), thay số liệu của công trình mới, lấy từ cùng nguồn với mặt bằng và sơ đồ để các tờ khớp nhau.
- **Không đặt đầu báo, sprinkler trong WC và buồng thang bộ.** Hộp họng đặt ở sảnh, hành lang chung, không trong phòng.
- **Hỏi trước khi vẽ:** hệ cần làm, nhóm nguy hiểm sprinkler, chiều cao trần. Không tự đoán.
- **Chữ số dim 2,5 mm, đường dim lệch 4 mm** khỏi tâm thiết bị.
- Trả lời bằng tiếng Việt. Số liệu tiêu chuẩn chỉ là sơ bộ, luôn nhắc đối chiếu bản gốc và để kỹ sư PCCC kiểm tra.

## GitHub

Repo `image797979-dotcom/pccc` đang **public**. Chỉ commit script, skill, JSON kết quả. Bản vẽ khách hàng (DWG), DXF trung gian (có file > 100 MB), PDF, Excel, ảnh kiểm tra **giữ ở máy**. Mỗi dự án mới thêm mục `.gitignore` tương ứng.

## Dự án

| Thư mục | Công trình | Trạng thái | Chạy lại |
| --- | --- | --- | --- |
| `du_an/khach-san-mbbt/` | KS MV YERSIN (7 Yersin, Bến Thành). Hầm, trệt, lửng, 2–7, sân thượng; nhóm 1, trần treo 3,2 m; kiến trúc dạng xref | 4 DWG (báo cháy, sprinkler, họng, chiếu sáng), 45 tờ PDF, BOQ Excel | `do_phong.py` (+ `--min`) → `thiet_ke.py` → `xuat_excel.py` → `ve_acad.py bc\|spr\|hong\|cs` → `in_tat_ca.py` |
| `du_an/ks-mini-34nvm/` | KS mini 34 NVM. Hầm, trệt, lửng, 2–6; **không sprinkler**; nhóm 1, trần ≤ 3,5 m; mỗi tầng là block `MBBT <tầng>` | 3 DWG (báo cháy, họng + bình, chiếu sáng), 33 tờ PDF gồm 5 tờ thuyết minh. Phòng khai báo tay (`phong_tay.py`). Viewport đổi 1:75 → 1:125 | `luu_dxf.py` → `lam_phang.py` → `phong_tay.py` → `thiet_ke.py` → `sh chay_tat_ca.sh` → `in_tat_ca.py` |
| `du_an/khach-san-8-tang/` | KS 8 tầng (thử nghiệm ban đầu) | Script thiết kế, thuỷ lực | |

Bản vẽ gốc của khách nằm ngoài repo (`D:\dự án\...`). Script dự án tìm thư viện skill theo đường dẫn tương đối (`../../.claude/skills/pccc-autocad/scripts`), nên clone repo ở thư mục nào cũng chạy được.

Điểm cần người dùng xác nhận ở 34 NVM: cao độ tầng suy từ dim mặt cắt (hầm −3,0 m là giả thiết); tầng hầm không có thang bộ trên bản vẽ; lưu lượng họng 2,5 l/s và thời gian 3 giờ (bản mẫu ghi 2,6 l/s, 0,5 giờ); nhóm F1.2, bậc II, S0 chép theo bản mẫu.

## Môi trường

Windows, AutoCAD bản đầy đủ (bản LT không có COM), Python 3. Cài thư viện: `pip install -r requirements.txt`.
