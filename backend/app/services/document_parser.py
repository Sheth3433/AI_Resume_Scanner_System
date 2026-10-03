from __future__ import annotations

from io import BytesIO
from pathlib import Path
import tempfile
import zipfile

import pymupdf
from docx import Document

from app.config import MAX_FILE_SIZE, OCR_LANGUAGE, OCR_MAX_PAGES, TESSERACT_CMD
from app.services.text_cleaner import clean_resume_text


def extract_pdf_text(file_path: str | Path) -> str:
    with pymupdf.open(str(file_path)) as doc:
        if doc.needs_pass:
            raise ValueError("This PDF is password-protected and cannot be analyzed.")
        return "\n".join(page.get_text() for page in doc)


def extract_docx_text(file_path: str | Path) -> str:
    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_scanned_pdf_text(file_path: str | Path) -> str:
    import pytesseract
    from PIL import Image

    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError as exc:
        raise ValueError(
            "This PDF appears to be scanned/image-only, but the Tesseract OCR executable was not found. "
            "Install Tesseract OCR or set TESSERACT_CMD to its executable path."
        ) from exc

    pages_text = []
    with pymupdf.open(str(file_path)) as document:
        if document.needs_pass:
            raise ValueError("This PDF is password-protected and cannot be analyzed.")
        for page in document[:OCR_MAX_PAGES]:
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
            with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
                pages_text.append(pytesseract.image_to_string(image, lang=OCR_LANGUAGE, timeout=30))
    return "\n".join(pages_text)


def parse_resume_file(file_obj) -> str:
    filename = getattr(file_obj, "filename", "") or "resume"
    return parse_resume_content(filename, file_obj.read())


def validate_resume_content(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise ValueError("Please upload a PDF or DOCX resume.")
    if not content:
        raise ValueError("The uploaded file is empty.")
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds the maximum allowed size.")

    if suffix == ".pdf" and b"%PDF-" not in content[:1024]:
        raise ValueError("The file does not contain a valid PDF document.")
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ValueError("The file does not contain a valid DOCX document.")
        except (OSError, zipfile.BadZipFile) as exc:
            raise ValueError("The file does not contain a valid DOCX document.") from exc
    return suffix


def parse_resume_content(filename: str, content: bytes) -> str:
    suffix = validate_resume_content(filename, content)

    temp_dir = Path("tmp")
    temp_dir.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=suffix, delete=False) as handle:
        target_path = Path(handle.name)
        handle.write(content)

    try:
        if suffix == ".pdf":
            text = extract_pdf_text(target_path)
        else:
            text = extract_docx_text(target_path)

        cleaned = clean_resume_text(text)
        if not cleaned and suffix == ".pdf":
            cleaned = clean_resume_text(extract_scanned_pdf_text(target_path))
        if not cleaned:
            raise ValueError("Text could not be extracted from this document. OCR did not recover readable text from the PDF.")
        return cleaned
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("The document is damaged or could not be read. Please upload a valid PDF or DOCX.") from exc
    finally:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
