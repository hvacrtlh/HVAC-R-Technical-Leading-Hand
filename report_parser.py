from __future__ import annotations
from io import BytesIO

def extract_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""

    name = (uploaded_file.name or "").lower()
    data = uploaded_file.getvalue()

    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

    if name.endswith(".docx"):
        from docx import Document
        document = Document(BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs).strip()

    if name.endswith((".txt", ".md", ".csv")):
        return data.decode("utf-8", errors="replace").strip()

    raise ValueError("Unsupported file type. Upload PDF, DOCX, TXT, MD or CSV.")
