# Công cụ AI cho bản vẽ AutoCAD hệ thống PCCC

Tổng hợp các skill, MCP server và công cụ dùng để vẽ bản vẽ phòng cháy chữa cháy (PCCC) trong AutoCAD với Claude. Cập nhật: 20/10/2026.

## Tình trạng chung

- Chưa có skill Claude nào làm riêng cho PCCC, cả trong danh mục chính thức lẫn trên GitHub.
- Các công cụ dưới đây đều theo NFPA. Chưa có công cụ nào theo tiêu chuẩn Việt Nam (TCVN 7336 – sprinkler, TCVN 5738 – báo cháy, QCVN 06).
- Connector chính thức duy nhất là **Autodesk Product Help**, chỉ tra cứu tài liệu, không vẽ được.

## 1. MCP server AutoCAD dùng được cho bản vẽ PCCC

| Công cụ | Điểm phù hợp với PCCC | Yêu cầu |
| --- | --- | --- |
| [U-C4N/Autocad-MCP](https://github.com/U-C4N/Autocad-MCP) | 240+ công cụ, P&ID (ISA-5.1), mặt bằng, bóc khối lượng ống và cáp; chạy được không cần AutoCAD (ezdxf) | Python; AutoCAD tùy chọn |
| [C48H74/autocad-mcp](https://github.com/C48H74/autocad-mcp) | Thiên về đường ống: thuộc tính block (TAG), layer, xuất/nhập Excel; ví dụ có hệ nước chữa cháy | Python 3.11+, Windows + AutoCAD cho chế độ COM |
| [puran-water/autocad-mcp](https://github.com/puran-water/autocad-mcp) | Ký hiệu P&ID, chạy AutoLISP; có skill đi kèm `puran-water/autocad-drafting` | AutoCAD LT 2024+ (Windows) |
| [MCP Connector for AutoCAD – AUTOM8LABS](https://autom8labs.io/products/mcp-connector-autocad/docs/) | Có skill cho Claude Desktop (`autocad-connector.zip`) | Plugin cài vào AutoCAD |

Yêu cầu chung: Windows 10/11, AutoCAD hoặc AutoCAD LT 2024 trở lên, dùng qua Claude Desktop hoặc Claude Code.

## 2. LISP PCCC truyền thống

- **Fire Fighting Programs (Tharwat)**: LISP bố trí sprinkler và vẽ ống chữa cháy – https://autolispprograms.wordpress.com/fire-fighting/
- **Fire Sprinkler** trên Autodesk App Store: hỗ trợ AutoCAD 2016 trở lên.

## 3. Phần mềm chuyên dụng (trả phí)

- **AutoSprink**: xuất DWG, khoảng 10.000 USD.
- **HydraCAD**.

## Lệnh clone

```bash
git clone https://github.com/U-C4N/Autocad-MCP.git
git clone https://github.com/C48H74/autocad-mcp.git
git clone https://github.com/puran-water/autocad-mcp.git puran-autocad-mcp
git clone https://github.com/puran-water/autocad-drafting.git
```

## Hướng phát triển

- Viết skill PCCC riêng (SKILL.md) theo TCVN/QCVN: quy tắc bố trí đầu phun, đầu báo, họng nước, quy ước layer và ký hiệu; ghép với một MCP server ở mục 1.
- Viết LISP hoặc script Python (ezdxf) tự rải sprinkler trong polyline phòng theo mức nguy hiểm.

> Các repo trên là của bên thứ ba. Đọc kỹ mã nguồn trước khi cài.
