import os
import tempfile
import uuid

import pytesseract
import streamlit as st

from converter import convert_text_pdf, convert_scanned_pdf, has_extractable_text

st.set_page_config(page_title="Tamil PDF to Word Converter", page_icon="📄")
st.title("Tamil PDF to Word Converter")
st.caption("Converts native or scanned Tamil PDFs into editable .docx files.")

uploaded_file = st.file_uploader("Choose a Tamil PDF file", type=["pdf"])

mode = st.radio(
    "PDF Type",
    ("Auto-detect", "Text-Based (Native)", "Scanned/Image"),
    index=0,
    help=(
        "Auto-detect checks the first few pages for extractable text. "
        "Choose manually if you already know the PDF type."
    ),
)

convert_clicked = st.button("Convert", type="primary", disabled=uploaded_file is None)

if uploaded_file and convert_clicked:
    work_id = uuid.uuid4().hex
    tmp_dir = tempfile.gettempdir()
    input_path = os.path.join(tmp_dir, f"tamil_pdf_{work_id}.pdf")
    output_filename = f"{os.path.splitext(uploaded_file.name)[0]}_converted.docx"
    output_path = os.path.join(tmp_dir, f"tamil_docx_{work_id}.docx")

    try:
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        resolved_mode = mode
        if mode == "Auto-detect":
            with st.spinner("Detecting PDF type..."):
                is_text_pdf = has_extractable_text(input_path)
            resolved_mode = "Text-Based (Native)" if is_text_pdf else "Scanned/Image"
            st.info(f"Detected: **{resolved_mode}**")

        if resolved_mode == "Text-Based (Native)":
            with st.spinner("Converting native PDF (preserving layout & tables)..."):
                convert_text_pdf(input_path, output_path)
        else:
            progress_bar = st.progress(0.0, text="Running Tamil OCR...")

            def _update_progress(page_num, total_pages):
                progress_bar.progress(
                    page_num / total_pages,
                    text=f"OCR processing page {page_num}/{total_pages}...",
                )

            convert_scanned_pdf(
                input_path, output_path, progress_callback=_update_progress
            )
            progress_bar.progress(1.0, text="OCR complete.")

        st.success("Conversion complete!")

        with open(output_path, "rb") as f:
            st.download_button(
                "Download Word File",
                f,
                file_name=output_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    except pytesseract.TesseractNotFoundError:
        st.error(
            "Tesseract OCR engine not found. This is a system-level install, "
            "separate from `pip install pytesseract`. See the README's "
            "'System dependency' section for install steps, or set the "
            "TESSERACT_CMD environment variable to the full path of "
            "tesseract.exe / tesseract."
        )
    except Exception as e:
        st.error(f"Conversion failed: {e}")

    finally:
        for path in (input_path, output_path):
            if os.path.exists(path):
                os.remove(path)
