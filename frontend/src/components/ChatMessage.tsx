import ReactMarkdown from "react-markdown";
import type { Citation, QueryResponse } from "../api/client";

interface CitationCardProps {
    citation: Citation;
    index: number;
}

const CitationCard: React.FC<CitationCardProps> = ({ citation, index }) => {
    const ext = citation.filename.split(".").pop()?.toLowerCase() ?? "";
    const icon = ext === "pdf" ? "📄" : ext === "docx" || ext === "doc" ? "📝" : "📋";

    return (
        <div className="citation-card">
            <div className="citation-header">
                <span className="citation-icon">{icon}</span>
                <span className="citation-filename" title={citation.filename}>
                    {citation.filename.length > 30
                        ? `...${citation.filename.slice(-28)}`
                        : citation.filename}
                </span>
                {citation.page_number && (
                    <span className="citation-page">p.{citation.page_number}</span>
                )}
                <span className="citation-score">
                    {(citation.relevance_score * 100).toFixed(0)}% relevancia
                </span>
            </div>
            <div className="citation-text">
                [{index + 1}] "{citation.chunk_text}"
            </div>
        </div>
    );
};

const CRAG_LABELS: Record<NonNullable<QueryResponse["crag_status"]>, string> = {
    grounded: "✓ Respuesta fundamentada",
    partial: "△ Respuesta parcialmente fundamentada",
    insufficient: "✗ Información insuficiente",
};

interface ChatMessageProps {
    role: "user" | "assistant";
    content: string;
    citations?: Citation[];
    cragStatus?: QueryResponse["crag_status"];
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
    role,
    content,
    citations,
    cragStatus,
}) => {
    return (
        <div className={`message ${role}`}>
            <div className="message-avatar">
                {role === "user" ? "👤" : "🤖"}
            </div>
            <div className="message-body">
                {role === "assistant" && cragStatus && (
                    <div className={`crag-badge ${cragStatus}`}>
                        {CRAG_LABELS[cragStatus]}
                    </div>
                )}
                <div className="message-bubble">
                    <ReactMarkdown>{content}</ReactMarkdown>
                </div>
                {role === "assistant" && citations && citations.length > 0 && (
                    <div className="citations">
                        <div className="citations-label">📎 Fuentes ({citations.length})</div>
                        {citations.map((c, i) => (
                            <CitationCard key={`${c.document_id}-${i}`} citation={c} index={i} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
