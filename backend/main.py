"""
FastAPI application entry point.
Configures CORS, mounts routers, initializes services at startup.
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from services.embeddings import embedding_service
from services.vector_store import vector_store
from services.bm25_store import bm25_store
from api.upload import router as upload_router
from api.query import router as query_router
from api.documents import router as documents_router
from api.collections import router as collections_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load services in background to avoid blocking the port."""
    print("\n" + "="*50)
    print("🚀 RAG Sources App starting...")
    print("="*50)
    
    # 1. Background Loading of Embedding Model
    import threading
    def load_models_bg():
        print("[Startup] Loading models in background...")
        try:
            embedding_service.load()
            print("[Startup] Models ready in background ✓")
        except Exception as e:
            print(f"[ERROR] Model loading failed: {e}")

    threading.Thread(target=load_models_bg, daemon=True).start()

    # 2. Sync Lexical index (BM25)
    if not bm25_store._chunk_texts:
        try:
            all_chunks = vector_store.get_all_chunks()
            if all_chunks:
                print(f"[Startup] Syncing BM25 from {len(all_chunks)} chunks...")
                bm25_store.rebuild_from_store(all_chunks)
                print("[Startup] BM25 synced ✓")
        except Exception as e:
            print(f"[ERROR] BM25 sync failed: {e}")
    
    print("="*50)
    print("✅ SERVER READY - http://127.0.0.1:8000")
    print(" (App is alive! The first query/upload will wait for models)")
    print("="*50 + "\n")
    yield
    print("RAG Sources App shutting down.")


app = FastAPI(
    title="RAG Sources App",
    description="Local RAG system with hybrid search (BM25 + semantic + RRF) and Corrective RAG",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api", tags=["Ingestion"])
app.include_router(query_router, prefix="/api", tags=["Query"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])
app.include_router(collections_router, prefix="/api", tags=["Collections"])


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "model": settings.ollama_model if settings.llm_provider == "ollama" else settings.openai_model,
        "embedding_model": settings.embedding_model,
    }
