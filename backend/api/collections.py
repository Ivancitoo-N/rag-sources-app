"""
Collections API — list and manage document groups.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from models.schemas import CollectionInfo, CreateCollectionRequest
from services.vector_store import vector_store
from services.bm25_store import bm25_store
from services.collection_registry import collection_registry

router = APIRouter()


@router.get("/collections", response_model=list[CollectionInfo])
async def list_collections() -> list[CollectionInfo]:
    """Return all unique collections and their statistics."""
    try:
        # Vector store now merges with registry
        raw = vector_store.get_collections()
        return [CollectionInfo(**c) for c in raw]
    except Exception as e:
        print(f"[API] Error listing collections: {e}")
        return []


@router.post("/collections", response_model=dict)
async def create_collection(request: CreateCollectionRequest) -> dict:
    """Register a new collection name."""
    try:
        collection_registry.add(request.name)
        return {"message": f"Colección '{request.name}' creada."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{name}")
async def delete_collection(name: str) -> dict:
    """Delete an entire collection and all its associated documents."""
    try:
        # Remove from registry
        collection_registry.remove(name)
        
        # Remove from vector store
        vector_store.delete_collection(name)
        
        # We need to rebuild BM25 because it's in-memory
        bm25_store.rebuild_from_store(vector_store.get_all_chunks())
        
        return {"message": f"Colección '{name}' eliminada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
