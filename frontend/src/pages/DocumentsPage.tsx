import React from 'react';
import { DocumentItem } from '../types';
import { DocumentTable } from '../components/documents/DocumentTable';
import { FileUp, RefreshCw, AlertCircle } from 'lucide-react';

interface DocumentsPageProps {
  documents: DocumentItem[];
  loading: boolean;
  onRefresh: () => Promise<void>;
  onProcess: (docId: string) => Promise<void>;
  onDelete: (docId: string) => Promise<void>;
  onAskDoc: (docId: string) => void;
  onOpenUpload: () => void;
  processingIds: Set<string>;
  error: string | null;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({
  documents,
  loading,
  onRefresh,
  onProcess,
  onDelete,
  onAskDoc,
  onOpenUpload,
  processingIds,
  error,
}) => {
  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">Document Library</h2>
          <p className="text-xs text-slate-500">
            Upload, extract text, inspect page chunks, and manage your vector index.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onRefresh()}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200/80 hover:bg-slate-50 rounded-xl shadow-xs transition-colors disabled:opacity-50"
            title="Refresh documents list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-xs shadow-indigo-200 transition-colors"
          >
            <FileUp className="w-3.5 h-3.5" />
            <span>Upload PDF</span>
          </button>
        </div>
      </div>

      {/* Error Feedback */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
          <div className="flex-1 font-medium">{error}</div>
        </div>
      )}

      {/* Document Table */}
      <DocumentTable
        documents={documents}
        onProcess={onProcess}
        onDelete={onDelete}
        onAskDoc={onAskDoc}
        onOpenUpload={onOpenUpload}
        processingIds={processingIds}
      />
    </div>
  );
};
