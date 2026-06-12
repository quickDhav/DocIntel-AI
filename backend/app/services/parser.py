"""Document parser — extracts text, tables, and page images from uploaded files.

Supports PDF (pdfplumber + OCR fallback), images (pytesseract), and plain text.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class ParsedPage:
    """Data extracted from a single page of a document."""

    page_number: int
    text_content: str
    has_tables: bool = False
    tables_json: str = "[]"
    image_path: Optional[str] = None
    ocr_used: bool = False
    ocr_confidence: Optional[float] = None


class DocumentParser:
    """Extracts structured content from uploaded documents.

    Strategy
    --------
    * **PDF**: iterate pages with pdfplumber.  If a page yields fewer than
      50 characters of text, fall back to OCR via pytesseract on a
      rendered image of that page (pdf2image at 200 DPI).  Tables are
      extracted with ``pdfplumber.extract_tables()`` and converted to
      Markdown.
    * **Images** (PNG / JPG / TIFF): direct OCR with pytesseract.
    * **Text files**: read with encoding detection via ``chardet``.
    """


    def parse_document(self, file_path: str, doc_id: str) -> List[ParsedPage]:
        """Parse a document and return structured page data.

        Args:
            file_path: Absolute path to the document file.
            doc_id: UUID of the document (used for page image storage).

        Returns:
            Ordered list of ``ParsedPage`` objects.
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return self._parse_pdf(file_path, doc_id)
        elif ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
            return self._parse_image(file_path, doc_id)
        elif ext == ".txt":
            return self._parse_text(file_path, doc_id)
        else:
            logger.warning("Unsupported extension %s — attempting text parse", ext)
            return self._parse_text(file_path, doc_id)


    def _parse_pdf(self, file_path: str, doc_id: str) -> List[ParsedPage]:
        """Parse all pages of a PDF file."""
        import pdfplumber

        pages: List[ParsedPage] = []
        page_images_dir = self._ensure_pages_dir(doc_id)

        rendered_images = self._render_pdf_pages(file_path, page_images_dir)

        with pdfplumber.open(file_path) as pdf:
            for idx, pdf_page in enumerate(pdf.pages):
                page_num = idx + 1
                image_path = rendered_images.get(page_num)

                text = (pdf_page.extract_text() or "").strip()
                ocr_used = False
                ocr_confidence: Optional[float] = None

                if len(text) < 50 and image_path:
                    ocr_text, ocr_conf = self._ocr_image(image_path)
                    if ocr_text:
                        text = ocr_text
                        ocr_used = True
                        ocr_confidence = ocr_conf

                tables_raw = pdf_page.extract_tables() or []
                tables_md = [self._table_to_markdown(t) for t in tables_raw if t]
                has_tables = len(tables_md) > 0

                pages.append(
                    ParsedPage(
                        page_number=page_num,
                        text_content=text,
                        has_tables=has_tables,
                        tables_json=json.dumps(tables_md),
                        image_path=image_path,
                        ocr_used=ocr_used,
                        ocr_confidence=ocr_confidence,
                    )
                )

        logger.info("Parsed PDF %s — %d pages", file_path, len(pages))
        return pages

    def _render_pdf_pages(
        self, file_path: str, output_dir: str
    ) -> dict[int, str]:
        """Render every PDF page as a 200-DPI PNG and return {page_num: path}."""
        from pdf2image import convert_from_path

        mapping: dict[int, str] = {}
        try:
            images = convert_from_path(file_path, dpi=200, fmt="png")
            for idx, img in enumerate(images):
                page_num = idx + 1
                out_path = os.path.join(output_dir, f"page_{page_num:03d}.png")
                img.save(out_path, "PNG")
                mapping[page_num] = out_path
        except Exception as exc:
            logger.error("pdf2image rendering failed: %s", exc)
        return mapping


    def _parse_image(self, file_path: str, doc_id: str) -> List[ParsedPage]:
        """Parse a standalone image file via OCR."""
        from PIL import Image

        page_images_dir = self._ensure_pages_dir(doc_id)
        dest = os.path.join(page_images_dir, "page_001.png")

        img = Image.open(file_path)
        img.save(dest, "PNG")

        text, confidence = self._ocr_image(dest)
        return [
            ParsedPage(
                page_number=1,
                text_content=text or "",
                image_path=dest,
                ocr_used=True,
                ocr_confidence=confidence,
            )
        ]


    def _parse_text(self, file_path: str, doc_id: str) -> List[ParsedPage]:
        """Parse a plain-text file with encoding detection."""
        raw = Path(file_path).read_bytes()

        encoding = "utf-8"
        try:
            import chardet

            detected = chardet.detect(raw)
            if detected and detected.get("encoding"):
                encoding = detected["encoding"]
        except ImportError:
            pass

        try:
            text = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            text = raw.decode("utf-8", errors="replace")

        return [
            ParsedPage(
                page_number=1,
                text_content=text.strip(),
            )
        ]


    def _ocr_image(self, image_path: str) -> tuple[str, Optional[float]]:
        """Run pytesseract OCR on an image and return (text, confidence).

        Returns:
            Tuple of (extracted_text, average_confidence_percent).
        """
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            words: list[str] = []
            confidences: list[float] = []
            for i, word in enumerate(data["text"]):
                word = word.strip()
                if word:
                    words.append(word)
                    conf = float(data["conf"][i])
                    if conf > 0:
                        confidences.append(conf)

            text = " ".join(words)
            avg_conf = sum(confidences) / len(confidences) if confidences else None
            return text, avg_conf

        except Exception as exc:
            logger.error("OCR failed for %s: %s", image_path, exc)
            return "", None


    @staticmethod
    def _table_to_markdown(table: list[list]) -> str:
        """Convert a pdfplumber table (list of rows) to Markdown format."""
        if not table:
            return ""

        def _cell(val) -> str:
            return str(val).replace("|", "\\|").strip() if val else ""

        header = table[0]
        md_lines = [
            "| " + " | ".join(_cell(c) for c in header) + " |",
            "| " + " | ".join("---" for _ in header) + " |",
        ]
        for row in table[1:]:
            padded = list(row) + [""] * (len(header) - len(row))
            md_lines.append("| " + " | ".join(_cell(c) for c in padded[:len(header)]) + " |")

        return "\n".join(md_lines)


    @staticmethod
    def _ensure_pages_dir(doc_id: str) -> str:
        """Create and return the page-images directory for a document."""
        pages_dir = os.path.join(settings.PAGES_DIR, doc_id)
        Path(pages_dir).mkdir(parents=True, exist_ok=True)
        return pages_dir
