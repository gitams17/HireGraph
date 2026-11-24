"""
File upload validation and security checks for resumes.

Enforces:
1. Allowed extensions (.pdf, .docx).
2. Maximum file size (configurable, default 10MB).
3. Magic byte signature verification:
   - PDF: must begin with `%PDF-` (0x25 0x50 0x44 0x46 0x2D).
   - DOCX: must be a valid ZIP archive starting with `PK\x03\x04` and containing
     OpenXML document structures (`[Content_Types].xml` or `word/document.xml`).
"""

import io
from pathlib import Path
import zipfile

from django.conf import settings
from django.core.exceptions import ValidationError

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}
MAX_RESUME_SIZE = getattr(settings, "MAX_RESUME_SIZE_BYTES", 10 * 1024 * 1024)

# Magic bytes
PDF_MAGIC_BYTES = b"%PDF-"
ZIP_MAGIC_BYTES = b"PK\x03\x04"


def validate_resume_file(uploaded_file):
    """
    Validates uploaded file size, extension, and binary signature.
    Raises ValidationError with a human-readable message if invalid.
    """
    if not uploaded_file:
        raise ValidationError("No file provided.")

    # 1. Size check
    if uploaded_file.size > MAX_RESUME_SIZE:
        max_mb = MAX_RESUME_SIZE // (1024 * 1024)
        raise ValidationError(f"File size exceeds the {max_mb} MB limit.")

    # 2. Extension check
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Only PDF and DOCX documents are accepted."
        )

    # 3. Read initial bytes for signature inspection
    try:
        initial_chunk = uploaded_file.read(4096)
        uploaded_file.seek(0)
    except Exception as e:
        raise ValidationError("Unable to read uploaded file.") from e

    if ext == ".pdf":
        if not initial_chunk.startswith(PDF_MAGIC_BYTES):
            raise ValidationError(
                "Invalid PDF document: file header signature does not match PDF specification."
            )

    elif ext == ".docx":
        if not initial_chunk.startswith(ZIP_MAGIC_BYTES):
            raise ValidationError(
                "Invalid DOCX document: file header is not a valid OpenXML archive."
            )

        # Further verify it is a valid zip package containing word document xml
        try:
            file_bytes = io.BytesIO(uploaded_file.read())
            uploaded_file.seek(0)
            with zipfile.ZipFile(file_bytes, "r") as zf:
                namelist = set(zf.namelist())
                if not ("[Content_Types].xml" in namelist or "word/document.xml" in namelist):
                    raise ValidationError(
                        "Invalid DOCX document: missing required OpenXML components."
                    )
        except zipfile.BadZipFile:
            raise ValidationError("Invalid DOCX document: corrupt ZIP structure.")
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Error inspecting DOCX document: {e}")
