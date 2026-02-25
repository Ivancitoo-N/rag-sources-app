"""
API routes for document upload and ingestion.
"""
from __future__ import annotations
import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import UploadResponse
from services.ingestion import ingestion_service
from services.vector_store import vector_store
from services.bm25_store import bm25_store

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".md"}
MAX_FILE_SIZE_MB = 50


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = "default"
) -> UploadResponse:
    """
    Upload a PDF, DOCX, or MD file for ingestion into a specific collection.
    Steps: extract → chunk → embed → store in ChromaDB + BM25.
    """
    filename = file.filename or "document"
    suffix = Path(filename).suffix.lower()
    
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: '{suffix}'. "
                   f"Formatos aceptados: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        # Check file size
        size_mb = Path(tmp_path).stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo demasiado grande ({size_mb:.1f} MB). Máximo: {MAX_FILE_SIZE_MB} MB",
            )
        
        # Ingest: extract + chunk
        document_id, chunks = ingestion_service.ingest(tmp_path, filename, collection_name=collection_name)
        
        if not chunks:
            raise HTTPException(
                status_code=422,
                detail="No se pudo extraer contenido del archivo. Comprueba que no esté vacío o protegido.",
            )
        
        # Store in vector store (embeddings)
        vector_store.add_chunks(chunks)
        
        # Store in BM25 index (lexical)
        bm25_store.add_chunks(chunks)
        
        return UploadResponse(
            document_id=document_id,
            filename=filename,
            chunks_created=len(chunks),
            message=f"✅ '{filename}' procesado correctamente. {len(chunks)} fragmentos indexados.",
        )
    
    finally:
        Path(tmp_path).unlink(missing_ok=True)
