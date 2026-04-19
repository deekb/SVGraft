import io
from pypdf import PdfWriter
from .debug import debug

def merge_pdfs_in_memory(pdf_byte_list):
    writer = PdfWriter()

    debug(f"Merging {len(pdf_byte_list)} PDFs")

    for pdf in pdf_byte_list:
        writer.append(io.BytesIO(pdf))

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.getvalue()