"""
Documents API — list and delete ingested documents.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from models.schemas import DocumentInfo
from services.vector_store import vector_store
from services.bm25_store import bm25_store

router = APIRouter()


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents(collection_name: str | None = None) -> list[DocumentInfo]:
    """Return documents currently indexed, optionally filtered by collection."""
    raw = vector_store.get_documents(collection_name=collection_name)
    return [DocumentInfo(**doc) for doc in raw]


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> dict:
    """Remove a document and all its chunks from the vector store."""
    try:
        vector_store.delete_document(document_id)
        bm25_store.delete_document(document_id)
        return {"message": f"Documento {document_id[:8]} eliminado correctamente."}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
