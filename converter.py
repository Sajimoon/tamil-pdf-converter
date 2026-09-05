"""
Core conversion logic for the Tamil PDF -> Word converter.

Two paths:
  - convert_text_pdf: native/text-based PDFs, uses pdf2docx to preserve
    layout, tables, and formatting.
  - convert_scanned_pdf: scanned/image PDFs, rasterizes each page and
    runs Tesseract OCR configured for Tamil (lang='tam'), then writes
    the recognized text into a .docx with python-docx.
"""

import os
import platform

import pdfplumber
import pytesseract
from docx import Document
from docx.shared import Pt
from pdf2docx import Converter


def _configure_tesseract_path() -> None:
    """
    Make sure pytesseract can find the tesseract binary even if it's not
    on PATH. Priority:
      1. TESSERACT_CMD environment variable, if set.
      2. Common default Windows install location.
      3. Otherwise leave as-is (assume it's on PATH, e.g. Linux/macOS/Docker).
    """
    env_path = os.environ.get("TESSERACT_CMD")
    if env_path and os.path.exists(env_path):
        pytesseract.pytesseract.tesseract_cmd = env_path
        return

    if platform.system() == "Windows":
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_path):
            pytesseract.pytesseract.tesseract_cmd = default_path


_configure_tesseract_path()


def convert_text_pdf(pdf_path: str, docx_path: str) -> None:
    """Direct structural extraction for native (text-based) PDFs."""
    cv = Converter(pdf_path)
    try:
        cv.convert(docx_path)
    finally:
        cv.close()


def convert_scanned_pdf(
    pdf_path: str,
    docx_path: str,
    resolution: int = 300,
    lang: str = "tam",
    progress_callback=None,
) -> None:
    """
    OCR extraction for scanned Tamil PDFs.

    progress_callback, if given, is called as progress_callback(page_num, total_pages)
    after each page is processed, so a UI (e.g. Streamlit) can show progress.
    """
    doc = Document()

    # Use a Tamil-friendly font so recognized glyphs render correctly in Word.
    style = doc.styles["Normal"]
    style.font.name = "Nirmala UI"
    style.font.size = Pt(12)

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            img = page.to_image(resolution=resolution).original

            # OEM 3 (default LSTM engine) + PSM 3 (fully automatic page
            # segmentation) is a solid general-purpose default for Tamil.
            custom_config = "--oem 3 --psm 3"
            tamil_text = pytesseract.image_to_string(
                img, lang=lang, config=custom_config
            )

            doc.add_paragraph(tamil_text.strip())
            if i < total_pages:
                doc.add_page_break()

            if progress_callback:
                progress_callback(i, total_pages)

    doc.save(docx_path)


def has_extractable_text(pdf_path: str, sample_pages: int = 3) -> bool:
    """
    Heuristic to auto-detect whether a PDF is text-based or scanned.
    Checks the first few pages for extractable text; if none is found,
    the PDF is very likely a scanned/image PDF.
    """
    with pdfplumber.open(pdf_path) as pdf:
        pages_to_check = pdf.pages[:sample_pages]
        for page in pages_to_check:
            text = page.extract_text()
            if text and text.strip():
                return True
    return False
