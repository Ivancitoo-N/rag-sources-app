"""
Settings loaded from .env via pydantic-settings.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_db_path: str = "./data/chromadb"
    bm25_index_path: str = "./data/bm25_index.pkl"
    frontend_origin: str = "http://127.0.0.1:5173"
    crag_relevance_threshold: float = 0.20
    rrf_k: int = 60
    chunk_size: int = 512
    chunk_overlap: int = 64
    collections_registry_path: str = "./data/collections.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure data directories exist
Path(settings.chroma_db_path).mkdir(parents=True, exist_ok=True)
Path(settings.bm25_index_path).parent.mkdir(parents=True, exist_ok=True)
Path(settings.collections_registry_path).parent.mkdir(parents=True, exist_ok=True)
