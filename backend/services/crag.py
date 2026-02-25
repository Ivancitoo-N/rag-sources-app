"""
Corrective RAG (CRAG) Evaluator.

Before calling the LLM, evaluates retrieved context quality:
- "grounded": All top chunks exceed relevance threshold → proceed with generation
- "partial": Some chunks above threshold → generate with warning
- "insufficient": No chunks meet threshold → return insufficient message directly

Relevance is computed as cosine similarity between query embedding and chunk embedding,
using the same local embedding model. Zero LLM calls for this evaluation step.
"""
from __future__ import annotations
from config import settings
from services.embeddings import embedding_service


INSUFFICIENT_RESPONSE = (
    "No tengo información suficiente en los documentos proporcionados para responder "
    "esta pregunta con certeza. Por favor, sube documentos que contengan información "
    "sobre este tema."
)


class CRAGEvaluator:
    """
    Evaluates context relevance before RAG generation.
    Prevents hallucination by blocking generation when context is weak.
    """

    def evaluate(
        self,
        query: str,
        retrieved_chunks: list[dict],
        threshold: float | None = None,
    ) -> tuple[str, list[dict]]:
        """
        Evaluate retrieved chunks for relevance to query.
        
        Returns:
            (crag_status, filtered_chunks)
            crag_status: "grounded" | "partial" | "insufficient"
            filtered_chunks: chunks that passed the relevance threshold
        """
        if not retrieved_chunks:
            return "insufficient", []
        
        threshold = threshold or settings.crag_relevance_threshold
        query_embedding = embedding_service.embed_single(query)
        
        passing: list[dict] = []
        
        print(f"[CRAG] Evaluating {len(retrieved_chunks)} chunks against threshold {threshold:.2f}")
        for i, chunk in enumerate(retrieved_chunks):
            # Use pre-computed RRF score as primary signal
            rrf_score = chunk.get("rrf_score", 0.0)
            semantic_score = chunk.get("score", 0.0)
            
            # Compute direct cosine similarity as secondary signal
            chunk_embedding = embedding_service.embed_single(chunk["text"])
            direct_similarity = embedding_service.cosine_similarity(
                query_embedding, chunk_embedding
            )
            
            # Combined relevance: use direct_similarity (0-1 scale) as the primary truth
            # We add a small boost from RRF if it ranked very highly
            combined = direct_similarity + (0.05 if rrf_score > 0.01 else 0.0)
            chunk["relevance"] = combined
            
            is_pass = combined >= threshold
            print(f"  - Chunk {i}: combined={combined:.3f} (sim={direct_similarity:.3f}, sem={semantic_score:.3f}, rrf={rrf_score:.3f}) {'✅' if is_pass else '❌'}")
            
            if is_pass:
                passing.append(chunk)
        
        if not passing:
            print("[CRAG] Final status: INSUFFICIENT")
            return "insufficient", []
        
        ratio = len(passing) / len(retrieved_chunks)
        status = "grounded" if ratio >= 0.5 else "partial"
        
        # Sort by relevance descending
        passing.sort(key=lambda x: x["relevance"], reverse=True)
        return status, passing


crag_evaluator = CRAGEvaluator()
