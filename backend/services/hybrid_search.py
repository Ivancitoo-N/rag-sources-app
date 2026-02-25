"""
Hybrid Search Engine — combines semantic (ChromaDB) + lexical (BM25) results
using Reciprocal Rank Fusion (RRF) with configurable k parameter.

RRF formula: score(d) = Σ 1 / (k + rank_i(d))
where rank_i is the 1-based rank of document d in result list i.
"""
from __future__ import annotations
from config import settings
from services.vector_store import vector_store
from services.bm25_store import bm25_store


def reciprocal_rank_fusion(
    result_lists: list[list[dict]],
    k: int | None = None,
) -> list[dict]:
    """
    Fuse multiple ranked result lists using RRF.
    
    Args:
        result_lists: Each inner list is a ranked list of {id, text, metadata, score}
        k: RRF constant (default from settings, k=60 proven optimal)
    
    Returns:
        Merged, re-ranked list of results sorted by descending RRF score.
    """
    if k is None:
        k = settings.rrf_k
    
    rrf_scores: dict[str, float] = {}
    docs: dict[str, dict] = {}
    
    for result_list in result_lists:
        for rank, doc in enumerate(result_list, start=1):
            doc_id = doc["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            if doc_id not in docs:
                docs[doc_id] = doc
    
    # Sort by RRF score descending
    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
    
    results = []
    for doc_id in sorted_ids:
        entry = docs[doc_id].copy()
        entry["rrf_score"] = rrf_scores[doc_id]
        results.append(entry)
    
    return results


class HybridSearch:
    """
    Orchestrates hybrid search: semantic + BM25 + RRF fusion.
    """

    def search(self, query: str, collection_name: str | None = None, top_k: int = 5) -> list[dict]:
        """
        1. Run semantic search (ChromaDB cosine similarity)
        2. Run lexical search (BM25Okapi)
        3. Fuse results with RRF (k=60)
        4. Return top_k fused results
        """
        fetch_k = max(top_k * 3, 15)  # Fetch more candidates before fusion
        
        semantic_results = vector_store.search(query, collection_name=collection_name, top_k=fetch_k)
        bm25_results = bm25_store.search(query, collection_name=collection_name, top_k=fetch_k)
        
        print(f"[HybridSearch] Query: '{query}' (Collection: {collection_name or 'global'})")
        print(f"  - Semantic hits: {len(semantic_results)}")
        print(f"  - Lexical hits:  {len(bm25_results)}")

        if not semantic_results and not bm25_results:
            return []
        
        fused = reciprocal_rank_fusion(
            [l for l in [semantic_results, bm25_results] if l],
        )
        
        print(f"  - Fused top result RRF: {fused[0]['rrf_score']:.4f}" if fused else "  - No results after fusion")
        return fused[:top_k]


hybrid_search = HybridSearch()
