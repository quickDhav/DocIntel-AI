"""Document classifier using Google Gemini 2.0 Flash.

Produces structured JSON metadata describing a document's type, topic,
language, sensitivity, and key entities.
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """\
You are a document classification expert. Analyze the provided document text \
and return a JSON object that conforms EXACTLY to the schema below. Do NOT \
include any text outside the JSON block.

Required JSON schema:
{
  "document_type": "<one of: invoice, report, letter, form, academic_paper, legal, manual, presentation, spreadsheet, other>",
  "topic": "<one of: finance, healthcare, technology, legal, education, government, science, business, other>",
  "language": "<ISO 639-1 code, e.g. en, es, fr>",
  "content_characteristics": {
    "has_tables": <bool>,
    "has_images": <bool>,
    "has_handwriting": <bool>,
    "is_scanned": <bool>,
    "page_count": <int>
  },
  "sensitivity_level": "<one of: public, internal, confidential, restricted>",
  "summary": "<Brief 2-3 sentence summary of the document>",
  "key_entities": ["<entity1>", "<entity2>"],
  "date_references": ["<YYYY-MM-DD>"]
}

If a field cannot be determined, use reasonable defaults (e.g. "other", empty list, false).

--- DOCUMENT TEXT ---
"""


class DocumentClassifier:
    """Classifies documents via Google Gemini, returning structured metadata."""

    _MAX_RETRIES = 3
    _RETRY_DELAY_SECONDS = 2
    _TEXT_LIMIT = 12_000  # chars sent to Gemini (keeps token cost low)

    def __init__(self) -> None:
        self._settings = get_settings()
        self._model = None

    def _get_model(self):
        """Lazy-init the Gemini GenerativeModel."""
        if self._model is None:
            import google.generativeai as genai

            genai.configure(api_key=self._settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(self._settings.GEMINI_MODEL)
        return self._model

    def classify(
        self, doc_text_summary: str, page_count: int = 1
    ) -> Dict[str, Any]:
        """Classify a document based on its textual content.

        Args:
            doc_text_summary: Combined text content from the document (may be
                truncated to ``_TEXT_LIMIT`` characters).
            page_count: Total number of pages in the document.

        Returns:
            Classification dictionary matching the schema above.
        """
        if not self._settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set — returning default classification")
            return self._default_classification(page_count)

        truncated = doc_text_summary[: self._TEXT_LIMIT]
        prompt = CLASSIFICATION_PROMPT + truncated

        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                return self._call_gemini(prompt, page_count)
            except Exception as exc:
                logger.warning(
                    "Classification attempt %d/%d failed: %s",
                    attempt,
                    self._MAX_RETRIES,
                    exc,
                )
                if attempt < self._MAX_RETRIES:
                    time.sleep(self._RETRY_DELAY_SECONDS * attempt)

        logger.error("All classification attempts failed — returning defaults")
        return self._default_classification(page_count)


    def _call_gemini(
        self, prompt: str, page_count: int
    ) -> Dict[str, Any]:
        """Make a single Gemini API call and parse the JSON response."""
        import google.generativeai as genai

        model = self._get_model()
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1,
        )

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )

        raw_text = response.text.strip()
        result = json.loads(raw_text)

        if "content_characteristics" in result:
            result["content_characteristics"]["page_count"] = page_count
        else:
            result["content_characteristics"] = {
                "has_tables": False,
                "has_images": False,
                "has_handwriting": False,
                "is_scanned": False,
                "page_count": page_count,
            }

        return result


    @staticmethod
    def _default_classification(page_count: int = 1) -> Dict[str, Any]:
        """Return a safe default classification when the API is unavailable."""
        return {
            "document_type": "other",
            "topic": "other",
            "language": "en",
            "content_characteristics": {
                "has_tables": False,
                "has_images": False,
                "has_handwriting": False,
                "is_scanned": False,
                "page_count": page_count,
            },
            "sensitivity_level": "internal",
            "summary": "Classification unavailable — document uploaded successfully.",
            "key_entities": [],
            "date_references": [],
        }
