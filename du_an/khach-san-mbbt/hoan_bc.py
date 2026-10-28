"""Hoàn tất file báo cháy đang mở: thêm layout sơ đồ nguyên lý (lần chạy đầu lỗi ở bước này), lưu."""
import sys
sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac, layout_so_do
acad = ac.ket_noi()
doc = ac.goi_lai(lambda: acad.ActiveDocument)
print(doc.Name)
las = ac.goi_lai(lambda: doc.Layouts)
print([ac.goi_lai(lambda: las.Item(i)).Name for i in range(ac.goi_lai(lambda: las.Count))])
doc = layout_so_do.them_layout(acad, "BC - SƠ ĐỒ NGUYÊN LÝ BÁO CHÁY", (60000, 0), 80, "BC-05 TẦNG 3")
ac.goi_lai(lambda: setattr(doc, "ActiveSpace", 1)); ac.goi_lai(lambda: acad.ZoomExtents())
ac.goi_lai(lambda: doc.Save()); print("đã lưu")
