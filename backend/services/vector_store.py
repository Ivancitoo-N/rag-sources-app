"""
ChromaDB vector store — persistent, local, no server needed.
Stores chunk embeddings with metadata for semantic search.
"""
from __future__ import annotations
import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings
from services.embeddings import embedding_service
from services.ingestion import Chunk


class VectorStore:
    _client: chromadb.PersistentClient | None = None
    _collection: chromadb.Collection | None = None
    COLLECTION_NAME = "rag_chunks"

    def _get_collection(self) -> chromadb.Collection:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=settings.chroma_db_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        if self._collection is None:
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """Embed and store chunks in ChromaDB."""
        if not chunks:
            return
        
        collection = self._get_collection()
        texts = [c.text for c in chunks]
        embeddings = embedding_service.embed(texts)
        
        collection.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[c.metadata for c in chunks],
        )
        print(f"[VectorStore] Added {len(chunks)} chunks")

    def search(self, query: str, collection_name: str | None = None, top_k: int = 10) -> list[dict]:
        """
        Semantic search. Optionally filtered by collection_name.
        Scores are cosine distances (lower = more similar); we convert to similarity.
        """
        collection = self._get_collection()
        query_embedding = embedding_service.embed_single(query)
        
        # Prepare filter if collection_name is provided
        where_filter = {"collection_name": collection_name} if collection_name else None
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, max(1, collection.count())),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        
        hits = []
        if not results["ids"]:
            return []
            
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            similarity = 1.0 - (distance / 2.0)
            hits.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": similarity,
            })
        
        return hits

    def get_all_chunks(self) -> list[dict]:
        """Retrieve all chunks (for BM25 re-indexing)."""
        collection = self._get_collection()
        if collection.count() == 0:
            return []
        results = collection.get(include=["documents", "metadatas"])
        return [
            {"id": results["ids"][i], "text": results["documents"][i], "metadata": results["metadatas"][i]}
            for i in range(len(results["ids"]))
        ]

    def get_documents(self, collection_name: str | None = None) -> list[dict]:
        """Return unique documents stored in the vector store, optionally filtered by collection."""
        all_chunks = self.get_all_chunks()
        seen: dict[str, dict] = {}
        for chunk in all_chunks:
            meta = chunk["metadata"]
            
            # Filter by collection if requested
            chunk_collection = meta.get("collection_name", "default")
            if collection_name and chunk_collection != collection_name:
                continue
                
            doc_id = meta.get("document_id", "")
            if doc_id not in seen:
                seen[doc_id] = {
                    "document_id": doc_id,
                    "filename": meta.get("filename", "unknown"),
                    "collection_name": chunk_collection,
                    "chunk_count": 0,
                    "file_type": meta.get("filename", "").rsplit(".", 1)[-1] if "." in meta.get("filename", "") else "unknown",
                }
            seen[doc_id]["chunk_count"] += 1
        return list(seen.values())

    def get_collections(self) -> list[dict]:
        """Return unique collections and their stats, merged with registered empty ones."""
        from services.collection_registry import collection_registry
        
        all_chunks = self.get_all_chunks()
        stats: dict[str, dict] = {}
        
        # Get stats from actual data
        for chunk in all_chunks:
            meta = chunk["metadata"]
            name = meta.get("collection_name", "default")
            doc_id = meta.get("document_id", "")
            
            if name not in stats:
                stats[name] = {
                    "name": name,
                    "document_ids": set(),
                    "chunk_count": 0
                }
            
            stats[name]["document_ids"].add(doc_id)
            stats[name]["chunk_count"] += 1
            
        # Merge with all registered names (even those without data)
        registered_names = collection_registry.get_all()
        result = []
        for name in registered_names:
            if name in stats:
                result.append({
                    "name": name,
                    "document_count": len(stats[name]["document_ids"]),
                    "chunk_count": stats[name]["chunk_count"]
                })
            else:
                result.append({
                    "name": name,
                    "document_count": 0,
                    "chunk_count": 0
                })
                
        return result

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks belonging to a document."""
        collection = self._get_collection()
        collection.delete(where={"document_id": document_id})
        print(f"[VectorStore] Deleted document {document_id[:8]}")

    def delete_collection(self, collection_name: str) -> None:
        """Delete all documents in a collection."""
        collection = self._get_collection()
        collection.delete(where={"collection_name": collection_name})
        print(f"[VectorStore] Deleted collection: {collection_name}")


vector_store = VectorStore()
