# C4 Container Diagram

The **RAG Sources App** consists of a React frontend and a FastAPI backend, using local persistence for both vector and lexical data.

```mermaid
C4Container
    title Container diagram for RAG Sources App

    Person(user, "User", "Interacts via the web browser.")

    System_Boundary(c1, "RAG Sources App") {
        Container(spa, "Single Page App", "React, Vite, TS", "Provides UI for uploading documents and chatting within collections.")
        Container(api, "Backend API", "FastAPI, Python", "Orchestrates ingestion, hybrid search, and RAG logic.")
        ContainerDb(vector_db, "Vector Store", "ChromaDB (Local)", "Stores document embeddings and collection metadata.")
        ContainerDb(bm25_db, "BM25 Store", "JSON/Pickle (Local)", "Stores lexical frequency index for keyword search.")
    }

    System_Ext(llm, "LLM Engine", "Ollama or OpenAI", "Generates answers based on provided context.")

    Rel(user, spa, "Uses", "HTTPS")
    Rel(spa, api, "API calls (upload, query, collections)", "JSON/HTTPS")
    Rel(api, vector_db, "Stores/Queries embeddings", "Vector Search")
    Rel(api, bm25_db, "Stores/Queries tokens", "Lexical Search")
    Rel(api, llm, "Sends context & prompts", "HTTP/HTTPS")
```

## Containers Description

- **SPA (React)**: Handles the "Multi-Chat" experience. Maintains the state of the `activeCollection` and scopes all API requests to it.
- **Backend API (FastAPI)**: The brain of the application. It applies the "Multi-Context" isolation by partitioning the database queries using the `collection_name` metadata.
- **ChromaDB**: An embedded vector database that runs in-process. It stores the document chunks and provides semantic similarity search.
- **BM25 Store**: A custom lexical index implemented with `rank-bm25`. Optimized for keyword relevance.
- **LLM Engine**: The final generation stage. It is "blind" to the original files, receiving only the specifically selected and evaluated (via CRAG) text fragments.
