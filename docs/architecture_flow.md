# Architecture & Data Flow

The RAG Sources App implements a sophisticated pipeline to ensure high accuracy and context isolation.

## 1. Document Ingestion (Isolation Layer)
When a file is uploaded, the user specifies a `collection_name`.
1. **Extraction**: `Docling` parses the document with layout awareness.
2. **Partitioning**: Each extracted chunk is tagged with its `collection_name` in metadata.
3. **Storage**: Chunks are stored in ChromaDB (semantic) and BM25 (lexical).

## 2. Hybrid Search (RRF)
When a query is asked:
1. **Scoped Search**: The query is only sent to the `collection_name` specified in the request.
2. **Semantic Search**: Retrieval of top-k chunks based on cosine similarity.
3. **Lexical Search**: Retrieval of top-k chunks based on keyword frequency.
4. **Fusion**: Reciprocal Rank Fusion (RRF) combines both lists into a single ranked set.

## 3. CRAG Evaluation (The Safety Gate)
RETRIEVED CHUNKS → CRAG Evaluator → LLM
1. **Relevance Scoring**: Retreived chunks are scored against the query.
2. **Safety Cut-off**: If the best chunk score is below the `CRAG_RELEVANCE_THRESHOLD` (0.20), the process stops.
3. **Outcome**: The user receives "No tengo información suficiente" instead of an LLM hallucination.

## 4. Generation & Citations
1. **Grounded Prompting**: The system prompt forces the LLM to only use the provided context.
2. **Citation Mapping**: The LLM output is parsed to link sentences back to original `document_id` and `page_number`.
3. **UI Rendering**: Citations appear as interactive cards for transparency.
