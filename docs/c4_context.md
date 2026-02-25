# C4 Context Diagram

## System Overview
The **RAG Sources App** allows users to upload exclusive documents and query them using a local AI pipeline. It ensures maximum privacy by processing everything on the user's machine.

```mermaid
C4Context
    title System Context diagram for RAG Sources App

    Person(user, "User/Researcher", "Processes exclusive documents and asks grounded questions.")
    System(rag_app, "RAG Sources App", "Provides private document ingestion, hybrid search, and citation-based answering.")

    System_Ext(ollama, "Ollama (Local LLM)", "Optional: Runs LLM models like Llama3.2 locally for inference.")
    System_Ext(openai, "OpenAI API", "Optional: Provides cloud-based inference if configured.")

    Rel(user, rag_app, "Uploads files, switches collections, and asks queries", "HTTPS")
    Rel(rag_app, ollama, "Sends ground context and prompt for generation", "Local HTTP")
    Rel(rag_app, openai, "Sends grounded context and prompt", "HTTPS")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

## Key Personas
- **User/Researcher**: Needs to extract reliable information from specific document sets (PDF, DOCX, MD) without data leakage.

## System Boundaries
- **Internal**: Document extraction (Docling), local vector storage (ChromaDB), ranking (BM25 + RRF).
- **External**: LLM Inference (Ollama or OpenAI).
