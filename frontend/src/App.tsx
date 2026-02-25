import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Sidebar } from "./components/Sidebar";
import { DropZone } from "./components/DropZone";
import { ChatMessage } from "./components/ChatMessage";
import { useQuery } from "./hooks/useQuery";

export default function App() {
    const [activeCollection, setActiveCollection] = useState("default");
    const { messages, loading, ask, clearMessages } = useQuery();
    const [input, setInput] = useState("");
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const chatEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    // Clear messages when switching collection
    useEffect(() => {
        clearMessages();
    }, [activeCollection, clearMessages]);

    // Auto-resize textarea
    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value);
        const el = e.target;
        el.style.height = "auto";
        el.style.height = Math.min(el.scrollHeight, 140) + "px";
    };

    const handleSend = () => {
        const q = input.trim();
        if (!q || loading) return;
        setInput("");
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
        ask(q, activeCollection);
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleUploadSuccess = () => {
        setRefreshTrigger((n) => n + 1);
    };

    return (
        <div className="app-layout">
            <Sidebar
                refreshTrigger={refreshTrigger}
                activeCollection={activeCollection}
                onCollectionChange={setActiveCollection}
            />

            <div className="main">
                {/* Chat area */}
                <div className="chat-area">
                    {activeCollection === "" ? (
                        <div className="welcome">
                            <div className="welcome-icon">📁</div>
                            <h1>Primeros Pasos</h1>
                            <p className="onboarding-text">
                                Crea una carpeta para empezar a organizar tu conocimiento y potenciar tu IA local.
                            </p>
                            <div className="onboarding-arrow">← Empieza por aquí</div>
                        </div>
                    ) : messages.length === 0 && !loading ? (
                        <div className="welcome">
                            <div className="welcome-icon">🧠</div>
                            <h1>RAG Sources App</h1>
                            <p>
                                Consulta inteligente de documentos exclusivos con búsqueda híbrida,
                                CRAG y citaciones directas en <b>{activeCollection}</b>.
                            </p>
                            <div className="welcome-chips">
                                <span className="welcome-chip">📄 PDF</span>
                                <span className="welcome-chip">📝 DOCX</span>
                                <span className="welcome-chip">📋 Markdown</span>
                                <span className="welcome-chip">🔍 Hybrid Search</span>
                                <span className="welcome-chip">🛡 CRAG</span>
                                <span className="welcome-chip">🏠 100% Local</span>
                            </div>
                        </div>
                    ) : (
                        <div className="messages">
                            {messages.map((msg) => (
                                <ChatMessage
                                    key={msg.id}
                                    role={msg.role}
                                    content={msg.content}
                                    citations={msg.citations}
                                    cragStatus={msg.cragStatus}
                                />
                            ))}
                            {loading && (
                                <div className="message assistant">
                                    <div className="message-avatar">🤖</div>
                                    <div className="message-body">
                                        <div className="message-bubble">
                                            <div className="thinking">
                                                <span /><span /><span />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>
                    )}
                </div>

                {/* Input bar */}
                <div className="bottom-bar">
                    <DropZone
                        onUploadSuccess={handleUploadSuccess}
                        activeCollection={activeCollection}
                        disabled={!activeCollection}
                    />
                    <div className="chat-input-row">
                        <textarea
                            ref={textareaRef}
                            className="chat-input"
                            placeholder={activeCollection ? "Pregunta sobre tus documentos..." : "Crea una carpeta para empezar..."}
                            value={input}
                            onChange={handleInput}
                            onKeyDown={handleKeyDown}
                            rows={1}
                            disabled={loading || !activeCollection}
                        />
                        <button
                            className="send-btn"
                            onClick={handleSend}
                            disabled={!input.trim() || loading || !activeCollection}
                            title="Enviar"
                        >
                            ↑
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
