import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export interface UploadResponse {
    document_id: string;
    filename: string;
    chunks_created: number;
    message: string;
}

export interface Citation {
    document_id: string;
    filename: string;
    chunk_text: string;
    page_number: number | null;
    relevance_score: number;
}

export interface QueryResponse {
    answer: string;
    citations: Citation[];
    crag_status: "grounded" | "partial" | "insufficient";
}

export interface DocumentInfo {
    document_id: string;
    filename: string;
    collection_name: string;
    chunk_count: number;
    file_type: string;
}

export interface CollectionInfo {
    name: string;
    document_count: number;
    chunk_count: number;
}

export const uploadDocument = (file: File, collection_name = "default"): Promise<UploadResponse> => {
    const form = new FormData();
    form.append("file", file);
    return api.post<UploadResponse>(`/upload?collection_name=${encodeURIComponent(collection_name)}`, form).then((r) => r.data);
};

export const queryDocuments = (question: string, collection_name = "default", top_k = 5): Promise<QueryResponse> =>
    api.post<QueryResponse>("/query", { question, collection_name, top_k }).then((r) => r.data);

export const listDocuments = (collection_name?: string): Promise<DocumentInfo[]> =>
    api.get<DocumentInfo[]>("/documents", { params: { collection_name } }).then((r) => r.data);

export const deleteDocument = (document_id: string): Promise<void> =>
    api.delete(`/documents/${document_id}`).then(() => undefined);

export const listCollections = (): Promise<CollectionInfo[]> =>
    api.get<CollectionInfo[]>("/collections").then((r) => r.data);

export const createCollection = (name: string): Promise<void> =>
    api.post("/collections", { name }).then(() => undefined);

export const deleteCollection = (name: string): Promise<void> =>
    api.delete(`/collections/${encodeURIComponent(name)}`).then(() => undefined);
