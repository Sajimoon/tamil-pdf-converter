# Tamil PDF to Word Converter

Converts native (text-based) or scanned Tamil PDFs into editable `.docx`
files, using `pdf2docx` for structured text and Tesseract OCR (`lang=tam`)
for scanned pages.

## Local Setup

### 1. System dependency: Tesseract + Tamil language pack

**Linux/Ubuntu**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-tam
```

**Windows**
Download the [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)
and select the Tamil language pack during setup. Make sure the install
directory is added to your `PATH`, or set it explicitly in Python:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**macOS**
```bash
brew install tesseract tesseract-lang
```

### 2. Python environment

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## How it works

- **Auto-detect** (default): samples the first few pages with `pdfplumber`
  to check for extractable text. If found, uses the native path; otherwise
  falls back to OCR.
- **Text-Based (Native)**: uses `pdf2docx` to preserve tables, layout, and
  formatting directly.
- **Scanned/Image**: rasterizes each page at 300 DPI with `pdfplumber`,
  runs Tesseract OCR with `lang="tam"`, and writes recognized text into a
  new `.docx` via `python-docx` (with page breaks between source pages).

## Deployment

### Docker (recommended — Render, Railway, Fly.io, etc.)

```bash
docker build -t tamil-pdf-converter .
docker run -p 8501:8501 tamil-pdf-converter
```

On Render/Railway: push this repo with the `Dockerfile` and select
"Docker Runtime" so Tesseract + the Tamil pack build into the image.

### Streamlit Community Cloud (no Docker)

Keep `apt.txt` in the repo root — Streamlit Cloud reads it automatically
and installs `tesseract-ocr` and `tesseract-ocr-tam` before your app starts.

## Troubleshooting

**`TesseractNotFoundError` / "tesseract is not installed or it's not in your PATH"**
This means the Tesseract *binary* is missing or not discoverable — `pip
install pytesseract` only installs the Python wrapper, not the engine
itself. Fixes, in order of preference:
1. Install Tesseract for your OS (see "System dependency" above), make
   sure it's on `PATH`, then **restart your terminal/IDE fully** — a
   PATH update doesn't apply to already-running processes.
2. If you'd rather not touch PATH, set the `TESSERACT_CMD` environment
   variable to the full binary path, e.g. on Windows:
   ```
   set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```
   `converter.py` reads this automatically. On Windows it also falls
   back to that default path if `TESSERACT_CMD` isn't set.
3. Verify from a **new** terminal window with `tesseract --version` and
   `tesseract --list-langs` (confirm `tam` is listed).

**`warning: The 'fitz' API is deprecated...`**
Harmless — this comes from `pdf2docx`'s internal use of PyMuPDF and
doesn't affect conversion. Safe to ignore.

## Notes & tuning

- OCR accuracy depends heavily on scan quality. 300 DPI is a good default;
  raise `resolution` in `convert_scanned_pdf` for low-quality scans.
- The Tesseract config `--oem 3 --psm 3` works well for full pages of
  running text. For single columns or forms, try `--psm 4` or `--psm 6`.
- Very large PDFs may take a while to OCR — the app shows a per-page
  progress bar so users aren't left guessing.
