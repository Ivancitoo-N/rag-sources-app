"""
LLM Generator — calls Ollama (local) or OpenAI API to generate grounded answers.
Extracts citations from the context and maps them to the answer.
"""
from __future__ import annotations
import httpx
import re
from config import settings
from services.crag import INSUFFICIENT_RESPONSE
from models.schemas import Citation

SYSTEM_PROMPT = """Eres un asistente especializado en análisis de documentos. 
Responde ÚNICAMENTE basándote en los fragmentos de documentos proporcionados en el contexto.
Si la información no está disponible en los fragmentos proporcionados, indica claramente que no tienes información suficiente.
No inventes datos, estadísticas, ni afirmaciones que no estén explícitamente en el contexto.
Cuando uses información de un fragmento específico, indica el documento fuente en tu respuesta.
Responde en el idioma de la pregunta del usuario."""


def _build_context(chunks: list[dict]) -> str:
    """Format retrieved chunks into a context block for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        filename = meta.get("filename", "Documento")
        page = meta.get("page_number", "")
        page_str = f", página {page}" if page and page != "unknown" else ""
        parts.append(f"[Fragmento {i} — {filename}{page_str}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)


def _extract_citations(chunks: list[dict]) -> list[Citation]:
    """Convert retrieved chunks to Citation objects."""
    citations = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        page = meta.get("page_number", "")
        try:
            page_num = int(page) if page and page != "unknown" else None
        except (ValueError, TypeError):
            page_num = None
        
        citations.append(Citation(
            document_id=meta.get("document_id", ""),
            filename=meta.get("filename", "Documento desconocido"),
            chunk_text=chunk["text"][:400] + ("..." if len(chunk["text"]) > 400 else ""),
            page_number=page_num,
            relevance_score=round(chunk.get("relevance", chunk.get("rrf_score", 0.0)), 4),
        ))
    return citations


async def _call_ollama(messages: list[dict]) -> str:
    """Call Ollama local API."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for grounded, factual answers
                    "top_p": 0.9,
                    "num_predict": 1024,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


async def _call_openai(messages: list[dict]) -> str:
    """Call OpenAI API."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1024,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


class Generator:
    """
    Generates grounded answers using retrieved context.
    Handles both Ollama and OpenAI providers transparently.
    """

    async def generate(
        self,
        question: str,
        context_chunks: list[dict],
        crag_status: str,
    ) -> tuple[str, list[Citation]]:
        """
        Generate a grounded answer.
        
        Returns:
            (answer_text, citations)
        """
        if crag_status == "insufficient":
            return INSUFFICIENT_RESPONSE, []
        
        context = _build_context(context_chunks)
        user_message = f"""Contexto de los documentos:

{context}

---

Pregunta del usuario: {question}

Responde basándote estrictamente en el contexto anterior."""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
        
        try:
            if settings.llm_provider == "openai":
                answer = await _call_openai(messages)
            else:
                answer = await _call_ollama(messages)
        except Exception as e:
            print(f"[Generator] LLM call failed: {e}")
            answer = (
                f"Error al conectar con el LLM ({settings.llm_provider}). "
                f"Asegúrate de que Ollama esté ejecutándose con `ollama serve`. Error: {str(e)[:100]}"
            )
        
        citations = _extract_citations(context_chunks)
        return answer, citations


generator = Generator()
