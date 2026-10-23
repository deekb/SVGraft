import io
from pypdf import PdfWriter
import pymupdf
from .debug import debug


def merge_pdfs_in_memory(pdf_byte_list):
    writer = PdfWriter()

    debug(f"Merging {len(pdf_byte_list)} pages")

    for pdf in pdf_byte_list:
        writer.append(io.BytesIO(pdf))

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.getvalue()


def pdf_to_svg_first_page(file_stream):
    doc = pymupdf.open("pdf", file_stream)
    page = doc[0]
    return page.get_svg_image()
