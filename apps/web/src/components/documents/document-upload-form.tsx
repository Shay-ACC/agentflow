"use client";

import { useEffect, useState, type FormEvent } from "react";

import { apiClient } from "@/lib/api";
import type { DocumentRecord } from "@/lib/api";


function formatByteSize(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }

  return `${(value / 1024).toFixed(1)} KB`;
}


function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}


export function DocumentUploadForm() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadDocuments() {
      setIsLoading(true);

      try {
        const nextDocuments = await apiClient.listDocuments();
        if (!isActive) {
          return;
        }

        setDocuments(nextDocuments);
        setErrorMessage(null);
      } catch (error) {
        if (!isActive) {
          return;
        }

        setErrorMessage(
          error instanceof Error ? error.message : "Failed to load documents.",
        );
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    void loadDocuments();

    return () => {
      isActive = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;

    if (selectedFile === null) {
      setErrorMessage("Select a .txt or .md file first.");
      return;
    }

    setIsUploading(true);

    try {
      const result = await apiClient.uploadDocument(selectedFile);
      setDocuments((currentDocuments) => {
        const existingIndex = currentDocuments.findIndex(
          (document) => document.id === result.document.id,
        );

        if (existingIndex === -1) {
          return [result.document, ...currentDocuments];
        }

        return currentDocuments.map((document) =>
          document.id === result.document.id ? result.document : document,
        );
      });
      setSelectedFile(null);
      setSuccessMessage(
        result.deduplicated
          ? `${result.document.filename} already exists. Reused existing index.`
          : `Stored ${result.document.filename} successfully.`,
      );
      setErrorMessage(null);
      form?.reset();
    } catch (error) {
      setSuccessMessage(null);
      setErrorMessage(
        error instanceof Error ? error.message : "Document upload failed.",
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-app-border bg-app-panel p-6">
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-semibold text-app-text">
              Upload a text document
            </label>
            <p className="mt-2 text-sm leading-7 text-app-subtle">
              v1 supports `.txt` and `.md` only. Each upload creates a document
              record in PostgreSQL and attempts to keep its vector index
              available in Qdrant.
            </p>
          </div>

          <input
            type="file"
            accept=".txt,.md,text/plain,text/markdown"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            className="block w-full rounded-2xl border border-app-border bg-[#0b1422] px-4 py-3 text-sm text-app-text file:mr-4 file:rounded-full file:border-0 file:bg-app-accent file:px-4 file:py-2 file:text-sm file:font-semibold file:text-app-accent-foreground"
          />

          <div className="flex items-center justify-between gap-4">
            <p className="text-xs text-app-muted">
              The list below shows both the document record and current index
              availability.
            </p>
            <button
              type="submit"
              disabled={isUploading || selectedFile === null}
              className="rounded-full bg-app-accent px-5 py-3 text-sm font-semibold text-app-accent-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isUploading ? "Uploading..." : "Upload Document"}
            </button>
          </div>
        </form>
      </div>

      {successMessage ? (
        <div className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
          {successMessage}
        </div>
      ) : null}

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
          {errorMessage}
        </div>
      ) : null}

      <div className="rounded-3xl border border-app-border bg-app-panel p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-app-text">
              Document Records
            </h2>
            <p className="mt-2 text-sm leading-7 text-app-subtle">
              Simple v1 view of uploaded documents and whether their vector
              index is currently available.
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          {isLoading ? (
            <div className="rounded-2xl border border-dashed border-app-border px-4 py-4 text-sm text-app-subtle">
              Loading documents...
            </div>
          ) : null}

          {!isLoading && documents.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-app-border px-4 py-4 text-sm text-app-subtle">
              No documents uploaded yet.
            </div>
          ) : null}

          {!isLoading
            ? documents.map((document) => (
                <article
                  key={document.id}
                  className="rounded-2xl border border-app-border bg-[#0d1727] px-4 py-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-app-text">
                        {document.filename}
                      </p>
                      <p className="mt-1 text-xs text-app-muted">
                        Uploaded {formatDateTime(document.created_at)}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={[
                          "rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]",
                          document.index_status === "indexed"
                            ? "bg-emerald-500/15 text-emerald-300"
                            : "bg-amber-500/15 text-amber-200",
                        ].join(" ")}
                      >
                        {document.index_status === "indexed" ? "Indexed" : "Index Missing"}
                      </span>
                      <span className="rounded-full bg-app-panel-soft px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-app-muted">
                        {document.chunk_count} chunks
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-4 text-xs text-app-subtle">
                    <span>Size: {formatByteSize(document.byte_size)}</span>
                    <span>Text length: {document.text_length}</span>
                    <span>Type: {document.content_type ?? "text/plain"}</span>
                  </div>
                </article>
              ))
            : null}
        </div>
      </div>
    </div>
  );
}
