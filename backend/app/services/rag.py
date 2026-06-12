"""Agentic RAG engine — orchestrates retrieval and Gemini-powered generation.

Retrieves relevant document chunks from the vector store, builds a
context window with source attribution, and calls Gemini to produce a
cited answer.
"""

import json
import logging
import re
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an intelligent document assistant. Your job is to answer user \
questions based ONLY on the provided document context. Follow these rules \
strictly:

1. **Citations are mandatory.** Every factual claim must include a citation \
in the format [DocName, Page X]. Use the exact document name and page number \
from the context.
2. **Never hallucinate.** If the provided context does not contain enough \
information to answer the question, respond with: \
"I don't have information about that in the uploaded documents."
3. **Be thorough.** Use all relevant context chunks to build a comprehensive \
answer. Combine information across documents when appropriate.
4. **Preserve structure.** If the answer benefits from bullet points, tables, \
or numbered lists, use them.
5. **Stay on-topic.** Only answer what is asked. Do not volunteer unrelated \
information.
6. **Multi-turn awareness.** Use the conversation history to understand \
follow-up questions and pronoun references.
"""


class RAGEngine:
    """Retrieval-Augmented Generation engine backed by ChromaDB + Gemini."""

    _MAX_CONTEXT_CHARS = 14_000
    _MAX_HISTORY_MESSAGES = 10
    _MAX_RETRIES = 2

    def __init__(self) -> None:
        self._settings = get_settings()
        self._vector_store = VectorStoreService()
        self._model = None

    def _get_model(self):
        """Lazy-init the Gemini model."""
        if self._model is None:
            import google.generativeai as genai

            genai.configure(api_key=self._settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                self._settings.GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT,
            )
        return self._model


    def answer(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Answer a user query using retrieved document context.

        Args:
            query: The user's question.
            chat_history: Previous messages as ``[{"role": "user"|"assistant", "content": "..."}]``.

        Returns:
            Dictionary with ``answer`` (str) and ``citations``
            (list of ``{document_id, document_name, page_number}``).
        """
        search_results = self._vector_store.search(query, n_results=8)

        if not search_results:
            return {
                "answer": "I don't have information about that in the uploaded documents. Please upload relevant documents first.",
                "citations": [],
            }

        grouped = self._group_by_document(search_results)

        context, all_sources = self._build_context(grouped)

        prompt = self._build_prompt(query, context, chat_history)

        answer_text = self._call_gemini(prompt)

        citations = self._extract_citations(answer_text, all_sources)

        return {
            "answer": answer_text,
            "citations": citations,
        }


    @staticmethod
    def _group_by_document(
        results: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group search results by document_id."""
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in results:
            grouped[r["document_id"]].append(r)
        return dict(grouped)

    def _build_context(
        self,
        grouped: Dict[str, List[Dict[str, Any]]],
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Build a context string from grouped chunks, respecting char limits.

        Returns:
            Tuple of (context_string, list_of_source_dicts).
        """
        context_parts: List[str] = []
        all_sources: List[Dict[str, Any]] = []
        total_chars = 0

        for doc_id, chunks in grouped.items():
            chunks.sort(key=lambda c: (c["page_number"], c["chunk_index"]))
            doc_name = chunks[0]["document_name"]

            for chunk in chunks:
                snippet = (
                    f"[Source: {doc_name}, Page {chunk['page_number']}]\n"
                    f"{chunk['text']}\n"
                )
                if total_chars + len(snippet) > self._MAX_CONTEXT_CHARS:
                    break
                context_parts.append(snippet)
                total_chars += len(snippet)
                all_sources.append(
                    {
                        "document_id": chunk["document_id"],
                        "document_name": doc_name,
                        "page_number": chunk["page_number"],
                    }
                )

        return "\n".join(context_parts), all_sources

    def _build_prompt(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict[str, str]]],
    ) -> str:
        """Assemble the full prompt for Gemini."""
        parts: List[str] = []

        if chat_history:
            recent = chat_history[-self._MAX_HISTORY_MESSAGES :]
            parts.append("=== CONVERSATION HISTORY ===")
            for msg in recent:
                role = msg.get("role", "user").upper()
                parts.append(f"{role}: {msg['content']}")
            parts.append("")

        parts.append("=== DOCUMENT CONTEXT ===")
        parts.append(context)
        parts.append("")
        parts.append("=== USER QUESTION ===")
        parts.append(query)

        return "\n".join(parts)

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini with retries and return the generated text."""
        if not self._settings.GEMINI_API_KEY:
            return "I cannot process your question because the AI service is not configured. Please set the GEMINI_API_KEY."

        model = self._get_model()

        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as exc:
                logger.warning(
                    "Gemini call attempt %d/%d failed: %s",
                    attempt,
                    self._MAX_RETRIES,
                    exc,
                )
                if attempt < self._MAX_RETRIES:
                    time.sleep(1.5 * attempt)

        return "I'm sorry, I encountered an error processing your question. Please try again."

    @staticmethod
    def _extract_citations(
        answer_text: str,
        all_sources: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Extract cited sources from the answer text.

        Looks for patterns like ``[DocName, Page X]`` and matches them
        against the known source list.  Also includes any sources that
        were part of the context (to ensure completeness).

        Returns:
            Deduplicated list of citation dicts.
        """
        pattern = r"\[([^,\]]+),\s*[Pp]age\s*(\d+)\]"
        cited_refs = re.findall(pattern, answer_text)

        seen: set = set()
        citations: List[Dict[str, Any]] = []

        for doc_name_fragment, page_str in cited_refs:
            doc_name_fragment = doc_name_fragment.strip()
            page_num = int(page_str)

            for source in all_sources:
                key = (source["document_id"], source["page_number"])
                if key in seen:
                    continue
                if (
                    doc_name_fragment.lower() in source["document_name"].lower()
                    and source["page_number"] == page_num
                ):
                    citations.append(
                        {
                            "document_id": source["document_id"],
                            "document_name": source["document_name"],
                            "page_number": source["page_number"],
                        }
                    )
                    seen.add(key)

        if not citations and all_sources:
            for source in all_sources:
                key = (source["document_id"], source["page_number"])
                if key not in seen:
                    citations.append(source)
                    seen.add(key)

        return citations
