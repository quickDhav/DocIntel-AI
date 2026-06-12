"""Upload router — file upload with validation, encryption, and background processing."""

import json
import logging
import os
import tempfile
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Document, DocumentStatus, Page
from app.services.classifier import DocumentClassifier
from app.services.parser import DocumentParser
from app.services.vector_store import VectorStoreService
from app.utils.encryption import FileEncryption
from app.utils.file_validation import validate_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])

settings = get_settings()




def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split text into overlapping chunks for embedding.

    Args:
        text: Input text to split.
        chunk_size: Target character count per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if end < len(text):
            for sep in [". ", ".\n", "\n\n", "\n", " "]:
                last_sep = chunk.rfind(sep)
                if last_sep > chunk_size // 2:
                    chunk = chunk[: last_sep + len(sep)]
                    end = start + len(chunk)
                    break

        chunks.append(chunk.strip())
        start = end - chunk_overlap
        if start < 0:
            start = 0
        if start >= len(text):
            break
        if end >= len(text):
            remaining = text[start:].strip()
            if remaining and remaining != chunks[-1]:
                chunks.append(remaining)
            break

    return [c for c in chunks if c]


def _process_document(doc_id: str) -> None:
    """Run the full processing pipeline for a document.

    Pipeline stages: parse → classify → index.
    Status is updated in the database at each step.
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            logger.error("Document %s not found for processing", doc_id)
            return

        stored_path = os.path.join(settings.UPLOAD_DIR, doc.stored_filename)

        encryption = FileEncryption()
        try:
            file_bytes = encryption.decrypt_file(stored_path)
        except Exception as exc:
            logger.error("Decryption failed for %s: %s", doc_id, exc)
            doc.status = DocumentStatus.ERROR
            doc.error_message = f"Decryption failed: {exc}"
            db.commit()
            return

        ext = os.path.splitext(doc.original_filename)[1]
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
        try:
            with os.fdopen(tmp_fd, "wb") as tmp_file:
                tmp_file.write(file_bytes)

            doc.status = DocumentStatus.PARSING
            db.commit()

            parser = DocumentParser()
            try:
                parsed_pages = parser.parse_document(tmp_path, doc_id)
            except Exception as exc:
                logger.error("Parsing failed for %s: %s", doc_id, exc)
                doc.status = DocumentStatus.ERROR
                doc.error_message = f"Parsing failed: {exc}"
                db.commit()
                return

            for pp in parsed_pages:
                page = Page(
                    document_id=doc_id,
                    page_number=pp.page_number,
                    text_content=pp.text_content,
                    has_tables=pp.has_tables,
                    tables_json=pp.tables_json,
                    image_path=pp.image_path,
                    ocr_used=pp.ocr_used,
                    ocr_confidence=pp.ocr_confidence,
                )
                db.add(page)

            doc.page_count = len(parsed_pages)
            db.commit()

            doc.status = DocumentStatus.CLASSIFYING
            db.commit()

            all_text = "\n".join(p.text_content for p in parsed_pages if p.text_content)
            classifier = DocumentClassifier()
            try:
                classification = classifier.classify(all_text, page_count=len(parsed_pages))
            except Exception as exc:
                logger.warning("Classification failed for %s: %s — using defaults", doc_id, exc)
                classification = DocumentClassifier._default_classification(len(parsed_pages))

            doc.classification_json = json.dumps(classification)
            db.commit()

            doc.status = DocumentStatus.INDEXING
            db.commit()

            chunks: List[dict] = []
            chunk_idx = 0
            for pp in parsed_pages:
                if not pp.text_content:
                    continue
                page_chunks = _chunk_text(
                    pp.text_content,
                    settings.CHUNK_SIZE,
                    settings.CHUNK_OVERLAP,
                )
                for text_chunk in page_chunks:
                    chunks.append(
                        {
                            "text": text_chunk,
                            "page_number": pp.page_number,
                            "chunk_index": chunk_idx,
                        }
                    )
                    chunk_idx += 1

            if chunks:
                vector_store = VectorStoreService()
                try:
                    vector_store.add_chunks(doc_id, doc.original_filename, chunks)
                except Exception as exc:
                    logger.error("Indexing failed for %s: %s", doc_id, exc)
                    doc.status = DocumentStatus.ERROR
                    doc.error_message = f"Indexing failed: {exc}"
                    db.commit()
                    return

            doc.status = DocumentStatus.READY
            db.commit()
            logger.info("Document %s processed successfully", doc_id)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as exc:
        logger.exception("Unexpected error processing document %s: %s", doc_id, exc)
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = DocumentStatus.ERROR
                doc.error_message = f"Unexpected error: {exc}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()




@router.post("")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload one or more documents for processing.

    Each file is validated, encrypted, and stored. A background task
    is launched to parse, classify, and index every document.

    Returns a list of document records with their initial status.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results = []
    encryption = FileEncryption()

    for file in files:
        is_valid, result_or_error = await validate_file(file)
        if not is_valid:
            results.append(
                {
                    "filename": file.filename,
                    "status": "rejected",
                    "error": result_or_error,
                }
            )
            continue

        stored_filename = result_or_error
        content = await file.read()
        file_size = len(content)

        ext = os.path.splitext(file.filename or "")[1].lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tif": "image/tiff",
            ".tiff": "image/tiff",
            ".txt": "text/plain",
        }
        file_type = mime_map.get(ext, "application/octet-stream")

        raw_path = os.path.join(settings.UPLOAD_DIR, stored_filename)
        with open(raw_path, "wb") as fh:
            fh.write(content)

        encrypted_path = encryption.encrypt_file(raw_path)
        encrypted_filename = os.path.basename(encrypted_path)

        doc = Document(
            original_filename=file.filename or "untitled",
            stored_filename=encrypted_filename,
            file_type=file_type,
            file_size=file_size,
            status=DocumentStatus.UPLOADING,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        background_tasks.add_task(_process_document, doc.id)

        results.append(
            {
                "document_id": doc.id,
                "filename": doc.original_filename,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status.value,
            }
        )

    return {"uploaded": results}


@router.get("/status/{job_id}")
async def get_upload_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Return the current processing status for a document.

    Args:
        job_id: Document UUID.
    """
    doc = db.query(Document).filter(Document.id == job_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    response = {
        "document_id": doc.id,
        "filename": doc.original_filename,
        "status": doc.status.value,
        "page_count": doc.page_count,
    }

    if doc.status == DocumentStatus.ERROR:
        response["error"] = doc.error_message

    if doc.classification_json:
        try:
            response["classification"] = json.loads(doc.classification_json)
        except json.JSONDecodeError:
            response["classification"] = None

    return response
