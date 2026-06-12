"""Sentence-transformers embedding service (singleton, lazy-loaded)."""

import logging
from typing import List

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates dense vector embeddings using sentence-transformers.

    The model is loaded lazily on first use and shared across all
    callers via the module-level :func:`get_embedding_service` helper.
    """

    _instance: "EmbeddingService | None" = None
    _model = None

    def __new__(cls) -> "EmbeddingService":
        """Singleton — only one instance is ever created."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        """Load the sentence-transformers model on first call."""
        if self._model is None:
            settings = get_settings()
            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")


    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string.

        Args:
            text: Input text to embed.

        Returns:
            Dense vector as a list of floats.
        """
        self._load_model()
        embedding = self._model.encode(text, show_progress_bar=False)
        return embedding.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings.

        Args:
            texts: List of input texts.

        Returns:
            List of dense vectors (one per input text).
        """
        self._load_model()
        embeddings = self._model.encode(texts, show_progress_bar=False, batch_size=64)
        return [e.tolist() for e in embeddings]


def get_embedding_service() -> EmbeddingService:
    """Return the singleton EmbeddingService instance."""
    return EmbeddingService()
