from __future__ import annotations

from pathlib import Path

import pymupdf
from docx import Document

from app.config import MAX_FILE_SIZE
from app.services.text_cleaner import clean_resume_text


def extract_pdf_text(file_path: str | Path) -> str:
    doc = pymupdf.open(str(file_path))
    chunks = []
    for page in doc:
        chunks.append(page.get_text())
    doc.close()
    return "\n".join(chunks)


def extract_docx_text(file_path: str | Path) -> str:
    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def parse_resume_file(file_obj) -> str:
    filename = getattr(file_obj, "filename", "") or "resume"
    return parse_resume_content(filename, file_obj.read())


def parse_resume_content(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix not in {".pdf", ".doc", ".docx"}:
        raise ValueError("Please upload a PDF or DOCX resume.")

    if not content:
        raise ValueError("The uploaded file is empty.")
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File exceeds the maximum allowed size.")

    temp_dir = Path("tmp")
    temp_dir.mkdir(exist_ok=True)
    target_path = temp_dir / Path(filename).name
    with open(target_path, "wb") as handle:
        handle.write(content)

    try:
        if suffix == ".pdf":
            text = extract_pdf_text(target_path)
        elif suffix == ".docx":
            text = extract_docx_text(target_path)
        else:
            raise ValueError("DOC parsing is not enabled in this environment.")

        cleaned = clean_resume_text(text)
        if not cleaned:
            raise ValueError("We could not extract readable text from this file. Please upload a text-based PDF or DOCX.")
        return cleaned
    finally:
        if target_path.exists():
            target_path.unlink(missing_ok=True)
