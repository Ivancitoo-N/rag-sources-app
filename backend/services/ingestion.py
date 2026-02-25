"""
Document ingestion service.
Uses Docling for high-precision extraction (PDFs, DOCX, MD).
Falls back to PyMuPDF/python-docx for error recovery.
Applies recursive chunking with configurable overlap.
"""
from __future__ import annotations
import re
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from config import settings


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    filename: str
    text: str
    page_number: int | None = None
    chunk_index: int = 0
    metadata: dict = field(default_factory=dict)


def _recursive_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Splits text into chunks of maximum size, attempting to break at logical boundaries.
    """
    if not text or not text.strip():
        return []
    
    if len(text) <= chunk_size:
        return [text.strip()]

    # Simple boundaries to try
    boundaries = ["\n\n", "\n", ". ", " ", ""]
    
    chunks = []
    text_to_process = text
    
    while len(text_to_process) > chunk_size:
        # Find the best split point
        split_idx = -1
        for b in boundaries:
            if not b:
                # Last resort: hard cut
                split_idx = chunk_size
                break
            
            # Look for boundary within chunk_size
            last_b_idx = text_to_process.rfind(b, 0, chunk_size)
            if last_b_idx != -1:
                split_idx = last_b_idx + len(b)
                break
        
        # Extract chunk
        chunk = text_to_process[:split_idx].strip()
        if chunk:
            chunks.append(chunk)
            
        # Move forward, account for overlap
        # We start the next chunk 'overlap' chars before the split point
        text_to_process = text_to_process[max(0, split_idx - overlap):]
        
    if text_to_process.strip():
        chunks.append(text_to_process.strip())
        
    return chunks


class IngestionService:
    """Extracts and chunks documents using Docling."""

    _converter: "DocumentConverter | None" = None

    @classmethod
    def _get_converter(cls):
        if cls._converter is None:
            print("[Ingestion] Initializing Docling (this may take 2-3 minutes on first run)...")
            from docling.document_converter import DocumentConverter
            cls._converter = DocumentConverter()
            print("[Ingestion] Docling ready ✓")
        return cls._converter

    def ingest(self, file_path: str, filename: str, collection_name: str = "default") -> tuple[str, list[Chunk]]:
        """
        Main entry point. Returns (document_id, list_of_chunks).
        """
        document_id = str(uuid.uuid4())
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        print(f"[Ingestion] Processing: {filename} (Collection: {collection_name})")
        raw_pages = self._extract(path, suffix)
        chunks = self._chunk_pages(raw_pages, document_id, filename, collection_name)
        
        print(f"[Ingestion] {filename} → {len(chunks)} chunks (doc_id={document_id[:8]})")
        return document_id, chunks

    def _extract(self, path: Path, suffix: str) -> list[dict]:
        """
        Extract text from document. Returns list of {text, page_number} dicts.
        """
        # Ensure HF doesn't use symlinks on Windows to avoid WinError 1314
        import os
        if os.name == 'nt':
            os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
            os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

        if suffix == ".md":
            return self._extract_markdown(path)
        
        # Use Docling for PDF and DOCX (high-precision table extraction)
        try:
            return self._extract_docling(path)
        except (Exception, OSError) as e:
            # Catch OSError specifically for WinError 1314
            print(f"[Ingestion] Docling failed or lacks permissions ({type(e).__name__}: {e})")
            print(f"[Ingestion] Switching to fallback for '{suffix}'...")
            
            if suffix == ".pdf":
                return self._extract_pdf_fallback(path)
            elif suffix in (".docx", ".doc"):
                return self._extract_docx_fallback(path)
            
            return [{"text": path.read_text(encoding="utf-8", errors="ignore"), "page_number": None}]

    def _extract_docling(self, path: Path) -> list[dict]:
        converter = self._get_converter()
        print(f"[Ingestion] Converting {path.name} with Docling...")
        result = converter.convert(str(path))
        doc = result.document
        
        # In Docling v2, we iterate over items to get content per page
        # This prevents getting just the page number via str(page)
        pages_dict: dict[int, list[str]] = {}
        
        for item, _ in doc.iterate_items():
            # Get text: either via export_to_markdown (preferred for tables) or text attribute
            # We use markdown because it preserves table structure better for AI
            text = ""
            if hasattr(item, "export_to_markdown"):
                text = item.export_to_markdown().strip()
            elif hasattr(item, "text"):
                text = item.text.strip()
            
            if not text:
                continue

            # Find page number
            page_num = None
            if hasattr(item, "prov") and item.prov:
                # prov[0].page_no is 1-based page number in Docling
                page_num = item.prov[0].page_no
            
            if page_num is None:
                # Fallback to a special 'unknown' bucket if no prov
                page_num = 0
            
            if page_num not in pages_dict:
                pages_dict[page_num] = []
            pages_dict[page_num].append(text)
        
        if not pages_dict:
            # Fallback to whole document export if item iteration failed
            full_text = doc.export_to_markdown()
            print("[Ingestion] Warning: Item iteration failed, using full document export.")
            return [{"text": full_text, "page_number": None}]

        # Sort pages and return
        results = []
        for p_num in sorted(pages_dict.keys()):
            results.append({
                "text": "\n\n".join(pages_dict[p_num]),
                "page_number": p_num if p_num > 0 else None
            })
        
        return results

    def _extract_markdown(self, path: Path) -> list[dict]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Split by H2/H3 headers to create logical pages
        sections = re.split(r"\n(?=#{1,3} )", text)
        return [{"text": s.strip(), "page_number": i + 1} for i, s in enumerate(sections) if s.strip()]

    def _extract_pdf_fallback(self, path: Path) -> list[dict]:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("[Ingestion] PyMuPDF not found. Attempting auto-install...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf", "--quiet"])
            import fitz
            
        pages = []
        with fitz.open(str(path)) as doc:
            for i, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    pages.append({"text": text.strip(), "page_number": i})
        return pages

    def _extract_docx_fallback(self, path: Path) -> list[dict]:
        try:
            from docx import Document
        except ImportError:
            print("[Ingestion] python-docx not found. Attempting auto-install...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-docx", "--quiet"])
            from docx import Document

        doc = Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [{"text": text, "page_number": None}]

    def _chunk_pages(self, pages: list[dict], document_id: str, filename: str, collection_name: str) -> list[Chunk]:
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap
        chunks: list[Chunk] = []
        global_idx = 0
        
        for page in pages:
            page_text = page["text"]
            page_num = page.get("page_number")
            
            raw_chunks = _recursive_split(page_text, chunk_size, overlap)
            print(f"  - Page {page_num}: {len(page_text)} chars → {len(raw_chunks)} chunks")
            if raw_chunks:
                preview = raw_chunks[0][:50].replace("\n", " ")
                print(f"    Preview: [{preview}...]")
            
            for text in raw_chunks:
                if not text.strip():
                    continue
                chunks.append(Chunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    filename=filename,
                    text=text.strip(),
                    page_number=page_num,
                    chunk_index=global_idx,
                    metadata={
                        "document_id": document_id,
                        "filename": filename,
                        "collection_name": collection_name,
                        "page_number": str(page_num) if page_num else "unknown",
                    }
                ))
                global_idx += 1
        
        return chunks


ingestion_service = IngestionService()
