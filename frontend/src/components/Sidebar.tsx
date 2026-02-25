import { useEffect, useState } from "react";
import { listDocuments, deleteDocument, DocumentInfo, listCollections, CollectionInfo, deleteCollection, createCollection } from "../api/client";

interface SidebarProps {
    refreshTrigger: number;
    activeCollection: string;
    onCollectionChange: (name: string) => void;
}

const FILE_ICON: Record<string, string> = { pdf: "📄", docx: "📝", doc: "📝", md: "📋" };

export const Sidebar: React.FC<SidebarProps> = ({ refreshTrigger, activeCollection, onCollectionChange }) => {
    const [docs, setDocs] = useState<DocumentInfo[]>([]);
    const [collections, setCollections] = useState<CollectionInfo[]>([]);
    const [newCollectionName, setNewCollectionName] = useState("");

    const loadData = async () => {
        try {
            const [docsData, collectionsData] = await Promise.all([
                listDocuments(activeCollection),
                listCollections()
            ]);
            setDocs(docsData);
            setCollections(collectionsData);

            // Auto-select logic
            if (activeCollection === "" && collectionsData.length > 0) {
                onCollectionChange(collectionsData[0].name);
            } else if (collectionsData.length > 0) {
                const names = collectionsData.map(c => c.name);
                if (!names.includes(activeCollection)) {
                    onCollectionChange(collectionsData[0].name);
                }
            } else if (activeCollection !== "" && collectionsData.length === 0) {
                onCollectionChange("");
            }
        } catch {
            // backend may not be ready yet
        }
    };

    useEffect(() => {
        loadData();
    }, [refreshTrigger, activeCollection]);

    const handleDeleteDoc = async (doc: DocumentInfo) => {
        if (!confirm(`¿Eliminar "${doc.filename}"?`)) return;
        await deleteDocument(doc.document_id);
        setDocs((prev) => prev.filter((d) => d.document_id !== doc.document_id));
    };

    const handleCreateCollection = async () => {
        const name = newCollectionName.trim().toLowerCase();
        if (!name) return;
        if (collections.some(c => c.name === name)) {
            alert("Esta colección ya existe");
            return;
        }

        try {
            await createCollection(name);
            onCollectionChange(name);
            setNewCollectionName("");
            loadData();
        } catch (err) {
            alert("Error al crear la colección");
        }
    };

    const handleDeleteColl = async (name: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (name === "default") {
            alert("No se puede eliminar la colección por defecto, pero puedes vaciarla borrando sus archivos.");
            return;
        }
        if (!confirm(`¿Eliminar la colección "${name}" y todos sus documentos?`)) return;
        await deleteCollection(name);
        if (activeCollection === name) {
            onCollectionChange("default");
        } else {
            loadData();
        }
    };

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <div className="logo-icon">🧠</div>
                    <span className="logo-text">RAG Sources</span>
                </div>
                <span className="logo-badge">LOCAL · HYBRID</span>
            </div>

            <div className="sidebar-section">
                <div className="sidebar-section-title">Colecciones</div>
                <div className="collections-list">
                    {collections.map(c => (
                        <div
                            key={c.name}
                            className={`collection-item ${activeCollection === c.name ? 'active' : ''}`}
                            onClick={() => onCollectionChange(c.name)}
                        >
                            <span className="coll-icon">📁</span>
                            <span className="coll-name">{c.name}</span>
                            <span className="coll-count">{c.document_count}</span>
                            {c.name !== "default" && (
                                <button className="coll-delete" onClick={(e) => handleDeleteColl(c.name, e)}>✕</button>
                            )}
                        </div>
                    ))}
                    {!collections.some(c => c.name === "default") && (
                        <div
                            className={`collection-item ${activeCollection === "default" ? 'active' : ''}`}
                            onClick={() => onCollectionChange("default")}
                        >
                            <span className="coll-icon">📁</span>
                            <span className="coll-name">default</span>
                            <span className="coll-count">0</span>
                        </div>
                    )}
                </div>
                <div className="add-collection">
                    <input
                        type="text"
                        placeholder="Nueva colección..."
                        value={newCollectionName}
                        onChange={(e) => setNewCollectionName(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleCreateCollection()}
                    />
                    <button onClick={handleCreateCollection}>+</button>
                </div>
            </div>

            <div className="sidebar-section">
                <div className="sidebar-section-title">Documentos ({docs.length})</div>
                <div className="sidebar-docs">
                    {docs.length === 0 ? (
                        <div className="sidebar-empty">
                            Sin documentos en "{activeCollection}".
                            <br />
                            Arrastra un PDF, DOCX o MD.
                        </div>
                    ) : (
                        docs.map((doc) => {
                            const ext = doc.file_type.toLowerCase();
                            const icon = FILE_ICON[ext] ?? "📎";
                            return (
                                <div key={doc.document_id} className="doc-item">
                                    <span className="doc-icon">{icon}</span>
                                    <div className="doc-info">
                                        <div className="doc-name" title={doc.filename}>{doc.filename}</div>
                                        <div className="doc-meta">{doc.chunk_count} fragmentos</div>
                                    </div>
                                    <button className="doc-delete" onClick={() => handleDeleteDoc(doc)}>✕</button>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </aside>
    );
};
