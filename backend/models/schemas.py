"""
Pydantic schemas for RAG Sources App API.
"""
from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    message: str


class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_text: str
    page_number: Optional[int] = None
    relevance_score: float


class QueryRequest(BaseModel):
    question: str
    collection_name: str = "default"
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    crag_status: str  # "grounded" | "insufficient" | "partial"


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    collection_name: str = "default"
    chunk_count: int
    file_type: str


class CollectionInfo(BaseModel):
    name: str
    document_count: int
    chunk_count: int


class CreateCollectionRequest(BaseModel):
    name: str
