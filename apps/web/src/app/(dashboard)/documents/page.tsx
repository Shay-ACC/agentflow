import { DocumentUploadForm } from "@/components/documents/document-upload-form";


export default function DocumentsPage() {
  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.3em] text-app-muted">
          Documents
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">
          Document Library
        </h1>
        <p className="max-w-2xl text-sm leading-7 text-app-subtle">
          Minimal retrieval slice: upload plain text documents, index them, and
          make them available to the grounded chat flow.
        </p>
      </header>

      <DocumentUploadForm />
    </section>
  );
}
