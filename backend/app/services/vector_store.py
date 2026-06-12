"""ChromaDB vector store wrapper for document chunk storage and retrieval."""

import logging
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.services.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Manages document chunk embeddings in a ChromaDB persistent collection.

    Each chunk is stored with metadata including ``document_id``,
    ``document_name``, ``page_number``, and ``chunk_index``.
    """

    COLLECTION_NAME = "documents"

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = None
        self._collection = None
        self._embedding_service = get_embedding_service()


    def _get_collection(self):
        """Return (and lazily create) the ChromaDB collection."""
        if self._collection is None:
            import chromadb

            self._client = chromadb.PersistentClient(path=self._settings.CHROMA_DIR)
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                "ChromaDB collection '%s' ready (%d items)",
                self.COLLECTION_NAME,
                self._collection.count(),
            )
        return self._collection


    def add_chunks(
        self,
        doc_id: str,
        doc_name: str,
        chunks: List[Dict[str, Any]],
    ) -> int:
        """Add text chunks for a document to the vector store.

        Each element of *chunks* must contain:
        - ``text`` (str): the chunk text
        - ``page_number`` (int): source page number
        - ``chunk_index`` (int): sequential chunk index

        Args:
            doc_id: UUID of the source document.
            doc_name: Human-readable document filename.
            chunks: List of chunk dicts.

        Returns:
            Number of chunks successfully added.
        """
        if not chunks:
            return 0

        collection = self._get_collection()

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            chunk_id = f"{doc_id}_{chunk['chunk_index']}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append(
                {
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                }
            )

        embeddings = self._embedding_service.embed_texts(documents)

        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info("Added %d chunks for document %s (%s)", len(ids), doc_id, doc_name)
        return len(ids)

    def search(
        self,
        query: str,
        n_results: int = 8,
        filter_doc_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for chunks most relevant to a query.

        Args:
            query: Natural-language search query.
            n_results: Maximum number of results to return.
            filter_doc_id: Optional document ID to restrict search scope.

        Returns:
            List of result dicts, each containing ``document_id``,
            ``document_name``, ``page_number``, ``text``, and ``score``.
        """
        collection = self._get_collection()

        if collection.count() == 0:
            return []

        query_embedding = self._embedding_service.embed_text(query)

        where_filter = None
        if filter_doc_id:
            where_filter = {"document_id": filter_doc_id}

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        hits: List[Dict[str, Any]] = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                score = max(0.0, 1.0 - distance)
                hits.append(
                    {
                        "document_id": meta.get("document_id", ""),
                        "document_name": meta.get("document_name", ""),
                        "page_number": meta.get("page_number", 0),
                        "chunk_index": meta.get("chunk_index", 0),
                        "text": results["documents"][0][i] if results["documents"] else "",
                        "score": round(score, 4),
                    }
                )

        hits.sort(key=lambda h: h["score"], reverse=True)
        return hits

    def delete_document(self, doc_id: str) -> int:
        """Remove all chunks belonging to a document.

        Args:
            doc_id: UUID of the document to remove.

        Returns:
            Number of chunks deleted.
        """
        collection = self._get_collection()

        existing = collection.get(
            where={"document_id": doc_id},
            include=[],
        )
        ids_to_delete = existing["ids"] if existing and existing["ids"] else []

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info("Deleted %d chunks for document %s", len(ids_to_delete), doc_id)

        return len(ids_to_delete)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return basic statistics about the collection."""
        collection = self._get_collection()
        return {
            "collection_name": self.COLLECTION_NAME,
            "total_chunks": collection.count(),
        }
