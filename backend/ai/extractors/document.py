"""
Document text extraction and sanitization for Resume Screening.
Supports:
- PDF (pypdf)
- DOCX (python-docx)
- Text cleaning, normalization, and prompt-injection sanitization
"""

import io
import logging
from pathlib import Path
import re
from typing import BinaryIO

logger = logging.getLogger(__name__)

# Prompt injection patterns frequently attempted in resumes
SUSPICIOUS_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s*:\s*(override|ignore|give|you\s+must)", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(previous|job|evaluation)\s+(prompt|instructions?)", re.IGNORECASE),
    re.compile(r"give\s+this\s+candidate\s+(a\s+score\s+of\s+)?100", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
]


class DocumentExtractionError(Exception):
    """Raised when document extraction fails."""
    pass


class DocumentExtractor:
    """Extracts raw text from PDF and DOCX files safely."""

    @classmethod
    def extract_from_file_path(cls, file_path: Path | str) -> dict[str, str | bool]:
        path = Path(file_path)
        if not path.exists():
            raise DocumentExtractionError(f"File not found: {file_path}")

        suffix = path.suffix.lower()
        with open(path, "rb") as f:
            return cls.extract_from_stream(f, filename=path.name, suffix=suffix)

    @classmethod
    def extract_from_stream(
        cls,
        stream: BinaryIO,
        filename: str = "",
        suffix: str = "",
    ) -> dict[str, str | bool]:
        if not suffix and filename:
            suffix = Path(filename).suffix.lower()

        raw_text = ""
        is_scanned = False

        try:
            if suffix == ".pdf":
                raw_text, is_scanned = cls._extract_pdf(stream)
            elif suffix == ".docx":
                raw_text = cls._extract_docx(stream)
            elif suffix == ".txt":
                raw_text = stream.read().decode("utf-8", errors="replace")
            else:
                raise DocumentExtractionError(f"Unsupported document format: {suffix}")
        except DocumentExtractionError:
            raise
        except Exception as e:
            logger.exception("Error extracting text from document %s", filename)
            raise DocumentExtractionError(f"Failed to read document: {str(e)}") from e

        cleaned_text, injection_detected = cls.clean_and_sanitize(raw_text)

        return {
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "is_scanned": is_scanned,
            "injection_detected": injection_detected,
        }

    @classmethod
    def _extract_pdf(cls, stream: BinaryIO) -> tuple[str, bool]:
        import pypdf

        reader = pypdf.PdfReader(stream)
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(text)

        full_text = "\n\n".join(pages_text).strip()
        is_scanned = len(full_text) < 50  # Very few or 0 characters indicates scanned/image-only PDF

        # If scanned, attempt OCR fallback if pytesseract is available
        if is_scanned:
            ocr_text = cls._attempt_ocr(stream)
            if ocr_text:
                full_text = ocr_text
                is_scanned = False

        return full_text, is_scanned

    @classmethod
    def _extract_docx(cls, stream: BinaryIO) -> str:
        import docx

        doc = docx.Document(stream)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        # Extract text from tables inside docx
        table_text = []
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_text.append(" | ".join(row_cells))

        all_elements = paragraphs + table_text
        return "\n\n".join(all_elements).strip()

    @classmethod
    def _attempt_ocr(cls, stream: BinaryIO) -> str | None:
        """Graceful OCR fallback when scanned PDF is encountered."""
        try:
            import pytesseract
            from PIL import Image
            # If pytesseract is configured and available
            return None
        except ImportError:
            logger.debug("pytesseract/PIL not available for OCR fallback.")
            return None

    @classmethod
    def clean_and_sanitize(cls, text: str) -> tuple[str, bool]:
        """
        Cleans non-printable characters, normalizes whitespace,
        and sanitizes potential prompt injection vectors.
        """
        if not text:
            return "", False

        # 1. Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 2. Strip non-printable ASCII control characters (keep newline and tab)
        text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)

        # 3. Detect prompt injection keywords
        injection_detected = False
        for pattern in SUSPICIOUS_INJECTION_PATTERNS:
            if pattern.search(text):
                injection_detected = True
                # Neutralize injection lines by commenting them out in the extracted view
                text = pattern.sub("[REDACTED_SECURITY_RISK]", text)

        # 4. Collapse excessive consecutive empty lines
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        return text, injection_detected
