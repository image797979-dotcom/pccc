"""Mở file Excel bằng Excel (COM, ẩn), tính lại toàn bộ, kiểm tra ô lỗi (#...), lưu giá trị tính sẵn.
  python tinh_lai_excel.py file.xlsx [thư mục chép tới ...]
Ví dụ (chép thêm vào thư mục dự án gốc, cạnh 4.MBBT.dwg):
  python tinh_lai_excel.py BOQ_PCCC_YERSIN.xlsx "D:/dự án/khách sạn/YERSIN" """
import os, sys, time
import pythoncom, win32com.client


def thu(ham, n=60):
    for i in range(n):
        try:
            return ham()
        except pythoncom.com_error:
            if i == n - 1:
                raise
            time.sleep(1)


f = os.path.abspath(sys.argv[1])
xl = win32com.client.DispatchEx("Excel.Application")
try:
    thu(lambda: setattr(xl, "DisplayAlerts", False))
    wb = thu(lambda: xl.Workbooks.Open(f))
    thu(lambda: xl.CalculateFull())
    loi, n_ct = [], 0
    for ws in thu(lambda: wb.Worksheets):
        for c in thu(lambda: ws.UsedRange):
            if thu(lambda: c.HasFormula):
                n_ct += 1
            v = thu(lambda: c.Text)
            if isinstance(v, str) and v.startswith("#"):
                loi.append((ws.Name, c.Address, v))
    print("công thức:", n_ct, "– ô lỗi:", len(loi), loi[:10])
    th = thu(lambda: wb.Worksheets("TỔNG HỢP"))
    for r in range(5, 47):
        b, dvt = thu(lambda: th.Cells(r, 2).Value), thu(lambda: th.Cells(r, 4).Value)
        if b and dvt:
            print(f"{r:3d} {b[:44]:44s} {dvt:5s} {thu(lambda: th.Cells(r, 5).Text):>8s} -> {thu(lambda: th.Cells(r, 7).Text):>8s}")
    dc = thu(lambda: wb.Worksheets("ĐỐI CHIẾU"))
    print("đối chiếu:", [thu(lambda: dc.Cells(r, 4).Text) for r in range(4, 17)])
    thu(lambda: wb.Save())
    thu(lambda: wb.Close(False))
finally:
    thu(lambda: xl.Quit())
import shutil
for d in sys.argv[2:]:
    if os.path.isdir(d):
        shutil.copy2(f, d)
        print("đã chép tới", os.path.join(d, os.path.basename(f)))
