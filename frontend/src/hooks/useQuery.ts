import { useState, useCallback } from "react";
import { queryDocuments, QueryResponse } from "../api/client";

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    citations?: QueryResponse["citations"];
    cragStatus?: QueryResponse["crag_status"];
}

export const useQuery = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);

    const ask = useCallback(async (question: string, collectionName = "default") => {
        const userMsg: ChatMessage = {
            id: `u-${Date.now()}`,
            role: "user",
            content: question,
        };
        setMessages((prev) => [...prev, userMsg]);
        setLoading(true);

        try {
            const res = await queryDocuments(question, collectionName);
            const assistantMsg: ChatMessage = {
                id: `a-${Date.now()}`,
                role: "assistant",
                content: res.answer,
                citations: res.citations,
                cragStatus: res.crag_status,
            };
            setMessages((prev) => [...prev, assistantMsg]);
        } catch (err) {
            const assistantMsg: ChatMessage = {
                id: `a-${Date.now()}`,
                role: "assistant",
                content: "Error al conectar con el servidor. ¿Está el backend corriendo?",
                cragStatus: "insufficient",
            };
            setMessages((prev) => [...prev, assistantMsg]);
        } finally {
            setLoading(false);
        }
    }, []);

    const clearMessages = useCallback(() => setMessages([]), []);

    return { messages, loading, ask, clearMessages };
};
