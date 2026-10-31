"""PDF -> PNG (trang 1) để xem: python pdf_png.py vao.pdf ra.png [dpi]"""
import sys, pymupdf
d = pymupdf.open(sys.argv[1]); p = d[0]
p.get_pixmap(dpi=int(sys.argv[3]) if len(sys.argv) > 3 else 110).save(sys.argv[2])
