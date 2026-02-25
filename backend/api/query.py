"""
Query API — hybrid search + CRAG evaluation + LLM generation.
"""
from __future__ import annotations
from fastapi import APIRouter
from models.schemas import QueryRequest, QueryResponse
from services.hybrid_search import hybrid_search
from services.crag import crag_evaluator, INSUFFICIENT_RESPONSE
from services.generator import generator

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    RAG query endpoint:
    1. Hybrid search (semantic + BM25 + RRF)
    2. CRAG evaluation (relevance check)
    3. LLM generation with strict grounding
    """
    # Step 1: Hybrid retrieval
    results = hybrid_search.search(
        request.question, 
        collection_name=request.collection_name, 
        top_k=request.top_k
    )
    
    # Step 2: CRAG evaluation
    crag_status, filtered_chunks = crag_evaluator.evaluate(request.question, results)
    
    # Step 3: Generate answer
    if crag_status == "insufficient":
        return QueryResponse(
            answer=INSUFFICIENT_RESPONSE,
            citations=[],
            crag_status="insufficient",
        )
    
    answer, citations = await generator.generate(
        request.question,
        filtered_chunks,
        crag_status,
    )
    
    return QueryResponse(
        answer=answer,
        citations=citations,
        crag_status=crag_status,
    )
