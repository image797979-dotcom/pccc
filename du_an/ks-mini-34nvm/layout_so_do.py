"""Thêm layout A3 có viewport 1:TL nhìn vào vùng model G (khung A3 vẽ sẵn ở model)."""
import sys
sys.path.insert(0, r"C:\Users\Administrator\Documents\pccc\.claude\skills\pccc-autocad\scripts")
import acad_com as ac


def them_layout(acad, ten, G, TL, mau_ten=None):
    doc = ac.goi_lai(lambda: acad.ActiveDocument)
    las = ac.goi_lai(lambda: doc.Layouts)
    W, H = 420 * TL, 297 * TL
    try:
        lay = ac.goi_lai(lambda: las.Item(ten), so_lan=2)
        moi = False
    except Exception:
        lay = ac.goi_lai(lambda: las.Add(ten))
        moi = True
        if mau_ten:
            mau = ac.goi_lai(lambda: las.Item(mau_ten))
            ac.goi_lai(lambda: lay.CopyFrom(mau))  # chỉ chép thiết lập in, không chép đối tượng
            ac.goi_lai(lambda: setattr(lay, "Name", ten))
    if not moi:  # chạy lại: bỏ viewport A3 cũ, giữ viewport tổng của layout
        blk = ac.goi_lai(lambda: lay.Block)
        for j in range(ac.goi_lai(lambda: blk.Count) - 1, -1, -1):
            e = ac.goi_lai(lambda: blk.Item(j))
            if ac.goi_lai(lambda: e.ObjectName) == "AcDbViewport" and abs(ac.goi_lai(lambda: e.Width) - 420) < 1:
                ac.goi_lai(lambda: e.Delete())
    ac.goi_lai(lambda: setattr(doc, "ActiveLayout", lay))
    ac.cho_san_sang(acad)
    doc = ac.goi_lai(lambda: acad.ActiveDocument)  # tham chiếu cũ mất sau khi đổi layout
    ps = ac.goi_lai(lambda: doc.PaperSpace)
    vp = ac.goi_lai(lambda: ps.AddPViewport(ac.diem(210.0, 148.5), 420.0, 297.0))
    ac.goi_lai(lambda: vp.Display(True))
    ac.goi_lai(lambda: setattr(vp, "ViewportOn", True))
    # viewport chỉ kích hoạt được khi đang hiện trên màn hình giấy
    ac.goi_lai(lambda: acad.ZoomWindow(ac.diem(-5, -9), ac.diem(425, 306)))
    ac.cho_san_sang(acad)
    ac.goi_lai(lambda: setattr(doc, "MSpace", True))
    ac.goi_lai(lambda: setattr(doc, "ActivePViewport", vp))
    ac.goi_lai(lambda: acad.ZoomCenter(ac.diem(G[0] + W / 2, G[1] + H / 2), float(H)))  # cao H -> 1:TL
    ac.goi_lai(lambda: setattr(doc, "MSpace", False))
    ac.goi_lai(lambda: setattr(vp, "DisplayLocked", True))
    return doc
