"""
BM25 lexical search index using rank_bm25.
Index is rebuilt whenever new documents are ingested.
Persisted to disk as a pickle file.
"""
from __future__ import annotations
import pickle
import re
from pathlib import Path
from config import settings
from services.ingestion import Chunk


def _tokenize(text: str) -> list[str]:
    """Unicode-aware tokenizer preserving accents."""
    text = text.lower()
    # Match words including accents/unicode
    tokens = re.findall(r"\b\w+\b", text, re.UNICODE)
    # Filter common Spanish stop words to focus on meaningful terms
    stop_words = {"de", "la", "el", "en", "y", "a", "los", "las", "un", "una", "que", "es", "del"}
    return [t for t in tokens if t not in stop_words and len(t) > 1]


class BM25Store:
    """Maintains a BM25Okapi index over all ingested chunks."""

    def __init__(self) -> None:
        self._index_path = Path(settings.bm25_index_path)
        self._chunk_ids: list[str] = []
        self._chunk_texts: list[str] = []
        self._chunk_metadatas: list[dict] = []
        self._bm25 = None
        self._load()

    def _load(self) -> None:
        """Load persisted index from disk if it exists."""
        if self._index_path.exists():
            try:
                with open(self._index_path, "rb") as f:
                    state = pickle.load(f)
                self._chunk_ids = state["ids"]
                self._chunk_texts = state["texts"]
                self._chunk_metadatas = state["metadatas"]
                self._rebuild_bm25()
                print(f"[BM25] Loaded index ({len(self._chunk_ids)} chunks)")
            except Exception as e:
                print(f"[BM25] Could not load index: {e}. Starting fresh.")

    def _save(self) -> None:
        """Persist index to disk."""
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._index_path, "wb") as f:
            pickle.dump({
                "ids": self._chunk_ids,
                "texts": self._chunk_texts,
                "metadatas": self._chunk_metadatas,
            }, f)

    def _rebuild_bm25(self) -> None:
        """Rebuild the BM25Okapi model from current corpus."""
        if not self._chunk_texts:
            self._bm25 = None
            return
        from rank_bm25 import BM25Okapi
        tokenized = [_tokenize(t) for t in self._chunk_texts]
        self._bm25 = BM25Okapi(tokenized)

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Add new chunks to the index and rebuild BM25."""
        for chunk in chunks:
            self._chunk_ids.append(chunk.chunk_id)
            self._chunk_texts.append(chunk.text)
            self._chunk_metadatas.append(chunk.metadata)
        self._rebuild_bm25()
        self._save()
        print(f"[BM25] Index updated ({len(self._chunk_ids)} total chunks)")

    def search(self, query: str, collection_name: str | None = None, top_k: int = 10) -> list[dict]:
        """
        BM25 search. Optionally filtered by collection_name.
        Returns list of dicts with id, text, metadata, score.
        Scores normalized to [0, 1] range.
        """
        if self._bm25 is None or not self._chunk_texts:
            return []
        
        query_tokens = _tokenize(query)
        print(f"[BM25] Query tokens: {query_tokens}")
        scores = self._bm25.get_scores(query_tokens)
        
        # Normalize scores
        max_score = max(scores) if max(scores) > 0 else 1.0
        normalized = scores / max_score
        
        # Get all candidates and filter by collection
        hits = []
        for i, score in enumerate(normalized):
            if score <= 0.001:
                continue
            
            meta = self._chunk_metadatas[i]
            # Filter by collection if requested
            if collection_name and meta.get("collection_name", "default") != collection_name:
                continue
                
            hits.append({
                "id": self._chunk_ids[i],
                "text": self._chunk_texts[i],
                "metadata": meta,
                "score": float(score),
            })
            
        # Sort by score and take top_k
        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:top_k]

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks belonging to a document from BM25 index."""
        indices_to_keep = [
            i for i, meta in enumerate(self._chunk_metadatas)
            if meta.get("document_id") != document_id
        ]
        
        if len(indices_to_keep) == len(self._chunk_ids):
            return  # Nothing to delete
            
        self._chunk_ids = [self._chunk_ids[i] for i in indices_to_keep]
        self._chunk_texts = [self._chunk_texts[i] for i in indices_to_keep]
        self._chunk_metadatas = [self._chunk_metadatas[i] for i in indices_to_keep]
        
        self._rebuild_bm25()
        self._save()
        print(f"[BM25] Deleted document {document_id[:8]} and rebuilt index")

    def rebuild_from_store(self, all_chunks: list[dict]) -> None:
        """Rebuild entire index from vector store dump (used for recovery)."""
        self._chunk_ids = [c["id"] for c in all_chunks]
        self._chunk_texts = [c["text"] for c in all_chunks]
        self._chunk_metadatas = [c["metadata"] for c in all_chunks]
        self._rebuild_bm25()
        self._save()
        print(f"[BM25] Rebuilt from store ({len(self._chunk_ids)} chunks)")


bm25_store = BM25Store()
