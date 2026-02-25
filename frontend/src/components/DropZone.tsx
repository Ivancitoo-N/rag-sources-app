import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useUpload } from "../hooks/useUpload";

interface DropZoneProps {
    onUploadSuccess: () => void;
    activeCollection: string;
    disabled?: boolean;
}

const FILE_ICON: Record<string, string> = {
    pdf: "📄",
    docx: "📝",
    doc: "📝",
    md: "📋",
};

const getIcon = (name: string) => {
    const ext = name.split(".").pop()?.toLowerCase() ?? "";
    return FILE_ICON[ext] ?? "📎";
};

export const DropZone: React.FC<DropZoneProps> = ({ onUploadSuccess, activeCollection, disabled }) => {
    const { status, message, upload } = useUpload(onUploadSuccess);

    const onDrop = useCallback(
        (accepted: File[]) => {
            if (accepted[0]) upload(accepted[0], activeCollection);
        },
        [upload, activeCollection]
    );

    const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
        onDrop,
        accept: {
            "application/pdf": [".pdf"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
            "application/msword": [".doc"],
            "text/markdown": [".md"],
        },
        multiple: false,
        disabled: disabled || status === "uploading",
    });

    return (
        <div style={{ opacity: disabled ? 0.5 : 1, pointerEvents: disabled ? "none" : "auto" }}>
            <div {...getRootProps()} className={`dropzone ${isDragActive ? "active" : ""}`}>
                <input {...getInputProps()} />
                <div className="dropzone-content">
                    <span className="dropzone-icon">
                        {isDragActive ? "📥" : acceptedFiles[0] ? getIcon(acceptedFiles[0].name) : "📂"}
                    </span>
                    <div>
                        <div className="dropzone-text">
                            {isDragActive ? (
                                <strong>Suelta aquí para subir</strong>
                            ) : (
                                <>
                                    <strong>Arrastra un documento</strong> o haz clic para explorar
                                </>
                            )}
                        </div>
                        <div className="dropzone-types">PDF · DOCX · MD — máx. 50 MB</div>
                    </div>
                </div>
            </div>

            {status === "uploading" && (
                <div className="upload-progress">
                    <div className="progress-spinner" />
                    {message}
                </div>
            )}
            {status === "success" && <div className="upload-success">✅ {message}</div>}
            {status === "error" && <div className="upload-error">⚠️ {message}</div>}
        </div>
    );
};
