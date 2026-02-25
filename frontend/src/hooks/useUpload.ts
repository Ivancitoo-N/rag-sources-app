import { useState, useCallback } from "react";
import { uploadDocument, UploadResponse } from "../api/client";

export type UploadStatus = "idle" | "uploading" | "success" | "error";

export const useUpload = (onSuccess?: () => void) => {
    const [status, setStatus] = useState<UploadStatus>("idle");
    const [message, setMessage] = useState("");

    const upload = useCallback(
        async (file: File, collectionName = "default") => {
            setStatus("uploading");
            setMessage(`Procesando "${file.name}"...`);
            try {
                const res: UploadResponse = await uploadDocument(file, collectionName);
                setStatus("success");
                setMessage(res.message);
                onSuccess?.();
                setTimeout(() => setStatus("idle"), 4000);
            } catch (err: unknown) {
                setStatus("error");
                const detail =
                    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
                    "Error al procesar el archivo.";
                setMessage(detail);
                setTimeout(() => setStatus("idle"), 5000);
            }
        },
        [onSuccess]
    );

    return { status, message, upload };
};
