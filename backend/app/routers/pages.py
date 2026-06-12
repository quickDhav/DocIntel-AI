"""Pages router — serve page images and extracted text."""

import io
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Document, Page

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pages", tags=["pages"])

settings = get_settings()

THUMBNAIL_MAX_WIDTH = 300


@router.get("/{doc_id}/{page_num}")
async def get_page_image(
    doc_id: str,
    page_num: int,
    size: str = Query("full", regex="^(thumbnail|full)$"),
    db: Session = Depends(get_db),
):
    """Serve the rendered image of a document page.

    Args:
        doc_id: Document UUID.
        page_num: 1-based page number.
        size: ``thumbnail`` (max 300px wide) or ``full``.

    Returns:
        PNG image as a streaming response.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    page = (
        db.query(Page)
        .filter(Page.document_id == doc_id, Page.page_number == page_num)
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail=f"Page {page_num} not found")

    if not page.image_path or not os.path.exists(page.image_path):
        raise HTTPException(
            status_code=404,
            detail=f"Page image not available for page {page_num}",
        )

    from PIL import Image

    img = Image.open(page.image_path)

    if size == "thumbnail":
        w, h = img.size
        if w > THUMBNAIL_MAX_WIDTH:
            ratio = THUMBNAIL_MAX_WIDTH / w
            new_size = (THUMBNAIL_MAX_WIDTH, int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f'inline; filename="page_{page_num:03d}.png"',
        },
    )


@router.get("/{doc_id}/{page_num}/text")
async def get_page_text(
    doc_id: str,
    page_num: int,
    db: Session = Depends(get_db),
):
    """Return the extracted text content for a specific page.

    Args:
        doc_id: Document UUID.
        page_num: 1-based page number.

    Returns:
        JSON with ``text``, ``has_tables``, ``tables``, ``ocr_used``,
        and ``ocr_confidence``.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    page = (
        db.query(Page)
        .filter(Page.document_id == doc_id, Page.page_number == page_num)
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail=f"Page {page_num} not found")

    import json

    tables = []
    if page.tables_json:
        try:
            tables = json.loads(page.tables_json)
        except json.JSONDecodeError:
            tables = []

    return {
        "document_id": doc_id,
        "page_number": page.page_number,
        "text": page.text_content or "",
        "has_tables": page.has_tables,
        "tables": tables,
        "ocr_used": page.ocr_used,
        "ocr_confidence": page.ocr_confidence,
    }
