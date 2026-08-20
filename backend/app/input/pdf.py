from typing import List, Tuple
import numpy as np
import pypdfium2 as pdfium

class PDFLoader:
    """
    Input layer PDF document loader using pypdfium2.
    Renders multi-page PDFs to high-resolution page images.
    """
    @staticmethod
    def render_pdf_pages(file_path_or_bytes, scale: float = 200/72) -> List[Tuple[int, np.ndarray, int, int]]:
        """
        Renders all pages of a PDF.
        Returns a list of tuples: [(page_number, np_array_img, width, height), ...]
        """
        pdf = pdfium.PdfDocument(file_path_or_bytes)
        pages_data = []
        for idx in range(len(pdf)):
            page = pdf.get_page(idx)
            pil_image = page.render(scale=scale).to_pil()
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            w, h = pil_image.size
            pages_data.append((idx + 1, np.array(pil_image), w, h))
        return pages_data
