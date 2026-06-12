"""File validation utilities — MIME type checking, size limits, filename sanitisation."""

import os
import re
import uuid
import logging
from typing import Tuple

from fastapi import UploadFile

from app.config import get_settings

logger = logging.getLogger(__name__)


def _sanitize_filename(filename: str) -> str:
    """Strip path-traversal characters and replace unsafe chars.

    Returns a safe base name (no directory components).
    """
    name = os.path.basename(filename)
    name = re.sub(r"[^\w\-.]", "_", name)
    name = re.sub(r"__+", "_", name)
    name = re.sub(r"\.\.+", ".", name)
    return name.strip("_. ")


def _detect_mime_type(file_header: bytes, filename: str) -> str:
    """Detect MIME type using python-magic, with fallback heuristics.

    Args:
        file_header: First few KB of the file content.
        filename: Original filename for extension-based fallback.

    Returns:
        Detected MIME type string.
    """
    try:
        import magic

        mime = magic.from_buffer(file_header, mime=True)
        return mime
    except ImportError:
        logger.warning(
            "python-magic not available; falling back to extension-based detection"
        )
    except Exception as exc:
        logger.warning("magic detection failed: %s; falling back", exc)

    ext = os.path.splitext(filename)[1].lower()
    extension_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".txt": "text/plain",
    }
    return extension_map.get(ext, "application/octet-stream")


async def validate_file(file: UploadFile) -> Tuple[bool, str]:
    """Validate an uploaded file against whitelist rules.

    Checks:
    1. MIME type is in the allowed list.
    2. File size does not exceed ``MAX_FILE_SIZE_MB``.
    3. Filename is sanitised and a UUID-based stored name is generated.

    Args:
        file: FastAPI ``UploadFile`` instance.

    Returns:
        ``(True, safe_stored_filename)`` on success, or
        ``(False, error_message)`` on failure.
    """
    settings = get_settings()
    original_name = file.filename or "untitled"
    sanitized = _sanitize_filename(original_name)

    content = await file.read()
    file_size = len(content)
    await file.seek(0)

    header = content[:8192]  # first 8 KB is enough for magic
    mime_type = _detect_mime_type(header, original_name)
    if mime_type not in settings.ALLOWED_MIME_TYPES:
        return False, f"File type '{mime_type}' is not allowed. Accepted: {', '.join(settings.ALLOWED_MIME_TYPES)}"

    if file_size > settings.max_file_size_bytes:
        return False, f"File size ({file_size / (1024*1024):.1f} MB) exceeds the {settings.MAX_FILE_SIZE_MB} MB limit."

    ext = os.path.splitext(sanitized)[1] or ""
    stored_name = f"{uuid.uuid4().hex}{ext}"

    logger.info(
        "Validated file: original=%s  mime=%s  size=%d  stored=%s",
        original_name,
        mime_type,
        file_size,
        stored_name,
    )
    return True, stored_name


def get_mime_type_for_file(file_path: str) -> str:
    """Return the MIME type for a file on disk.

    Args:
        file_path: Absolute path to the file.

    Returns:
        MIME type string.
    """
    with open(file_path, "rb") as fh:
        header = fh.read(8192)
    return _detect_mime_type(header, os.path.basename(file_path))
