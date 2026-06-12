"""Documents router — list and delete uploaded documents."""

import json
import logging
import os
import shutil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Document, Page
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

settings = get_settings()


@router.get("")
async def list_documents(db: Session = Depends(get_db)):
    """Return all documents with their processing status and classification.

    Documents are ordered by upload time (most recent first).
    """
    docs = (
        db.query(Document)
        .order_by(Document.upload_time.desc())
        .all()
    )

    results = []
    for doc in docs:
        item = {
            "id": doc.id,
            "original_filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "upload_time": doc.upload_time.isoformat() if doc.upload_time else None,
            "status": doc.status.value,
            "page_count": doc.page_count,
        }

        if doc.classification_json:
            try:
                item["classification"] = json.loads(doc.classification_json)
            except json.JSONDecodeError:
                item["classification"] = None
        else:
            item["classification"] = None

        if doc.error_message:
            item["error_message"] = doc.error_message

        results.append(item)

    return {"documents": results, "total": len(results)}


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
):
    """Delete a document and all associated data.

    Removes:
    - Database records (Document + Pages via cascade)
    - Encrypted file from uploads directory
    - Page images from pages directory
    - Vector store chunks

    Args:
        doc_id: UUID of the document to delete.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    original_filename = doc.original_filename

    try:
        vector_store = VectorStoreService()
        deleted_chunks = vector_store.delete_document(doc_id)
        logger.info("Deleted %d vector chunks for %s", deleted_chunks, doc_id)
    except Exception as exc:
        logger.warning("Failed to delete vector chunks for %s: %s", doc_id, exc)

    stored_path = os.path.join(settings.UPLOAD_DIR, doc.stored_filename)
    if os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except OSError as exc:
            logger.warning("Failed to remove file %s: %s", stored_path, exc)

    pages_dir = os.path.join(settings.PAGES_DIR, doc_id)
    if os.path.isdir(pages_dir):
        try:
            shutil.rmtree(pages_dir)
        except OSError as exc:
            logger.warning("Failed to remove pages dir %s: %s", pages_dir, exc)

    db.delete(doc)
    db.commit()

    logger.info("Deleted document %s (%s)", doc_id, original_filename)
    return {
        "message": f"Document '{original_filename}' deleted successfully",
        "document_id": doc_id,
    }
