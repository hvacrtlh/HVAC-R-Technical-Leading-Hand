from __future__ import annotations

from io import BytesIO


def extract_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    filename = (uploaded_file.name or "").lower()
    raw = uploaded_file.getvalue()

    if filename.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(raw))
        return "\n".join(
            (page.extract_text() or "") for page in reader.pages
        ).strip()

    if filename.endswith(".docx"):
        from docx import Document

        document = Document(BytesIO(raw))
        return "\n".join(
            paragraph.text for paragraph in document.paragraphs
        ).strip()

    if filename.endswith((".txt", ".md", ".csv")):
        return raw.decode("utf-8", errors="replace").strip()

    raise ValueError("Unsupported file type. Upload PDF, DOCX, TXT, MD or CSV.")
