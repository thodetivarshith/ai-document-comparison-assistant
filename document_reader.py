"""PDF validation and text extraction (pypdf)."""
from __future__ import annotations

import io
from dataclasses import dataclass, field

from pypdf import PdfReader

MAX_FILE_MB = 20
MIN_TEXT_CHARS = 20  # fewer characters than this = treated as "no readable text"


class DocumentError(Exception):
    """Raised with a user-friendly message when a file cannot be used."""


@dataclass
class DocumentData:
    name: str
    pages: list[str]                      # text per page (index 0 = page 1)
    unreadable_pages: list[int] = field(default_factory=list)  # 1-based

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def text(self) -> str:
        """Full text with [Page N] markers so the LLM can cite page numbers."""
        return "\n\n".join(
            f"[Page {i}]\n{t.strip()}" for i, t in enumerate(self.pages, 1) if t.strip()
        )

    @property
    def char_count(self) -> int:
        return sum(len(t.strip()) for t in self.pages)

    def preview(self, n: int = 600) -> str:
        flat = " ".join(" ".join(self.pages).split())
        return flat[:n] + ("…" if len(flat) > n else "")


def validate_upload(name: str, data: bytes) -> None:
    """Cheap checks before parsing."""
    if not name.lower().endswith(".pdf"):
        raise DocumentError(f"'{name}' is not a PDF. Only .pdf files are supported.")
    if not data:
        raise DocumentError(f"'{name}' is empty (0 bytes).")
    if len(data) > MAX_FILE_MB * 1024 * 1024:
        raise DocumentError(f"'{name}' is larger than {MAX_FILE_MB} MB.")
    if b"%PDF" not in data[:1024]:
        raise DocumentError(f"'{name}' does not look like a valid PDF file.")


def extract_document(name: str, data: bytes) -> DocumentData:
    """Validate a PDF and extract text page by page."""
    validate_upload(name, data)
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            try:
                ok = reader.decrypt("")
            except Exception:
                ok = 0
            if not ok:
                raise DocumentError(f"'{name}' is password-protected and cannot be read.")
        total = len(reader.pages)
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f"'{name}' could not be opened as a PDF ({type(exc).__name__}). It may be corrupted.") from exc

    if total == 0:
        raise DocumentError(f"'{name}' has no pages.")

    pages: list[str] = []
    unreadable: list[int] = []
    for i, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if len(text.strip()) < 1:
            unreadable.append(i)
        pages.append(text)

    doc = DocumentData(name=name, pages=pages, unreadable_pages=unreadable)
    if doc.char_count < MIN_TEXT_CHARS:
        raise DocumentError(
            f"No readable text was found in '{name}'. It may be a scanned or image-only PDF "
            "(OCR is not supported in this version)."
        )
    return doc
