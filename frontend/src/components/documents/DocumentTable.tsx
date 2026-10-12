import React, { useState } from 'react';
import { DocumentItem } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { 
  FileText, 
  Trash2, 
  RefreshCw, 
  MessageSquare, 
  AlertTriangle, 
  Search, 
  FileUp,
  Layers,
  BookOpen
} from 'lucide-react';
import { Modal } from '../common/Modal';

interface DocumentTableProps {
  documents: DocumentItem[];
  onProcess: (docId: string) => Promise<void>;
  onDelete: (docId: string) => Promise<void>;
  onAskDoc: (docId: string) => void;
  onOpenUpload: () => void;
  processingIds: Set<string>;
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents,
  onProcess,
  onDelete,
  onAskDoc,
  onOpenUpload,
  processingIds,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<DocumentItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const filtered = documents.filter((doc) =>
    doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await onDelete(deleteTarget.id);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-4">
      {/* Search & Actions Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search documents by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs rounded-xl border border-slate-200/80 bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
          />
        </div>
        <div className="flex items-center gap-2 self-end sm:self-auto">
          <span className="text-xs text-slate-500 font-medium">
            {filtered.length} {filtered.length === 1 ? 'document' : 'documents'}
          </span>
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3 shadow-xs">
              <FileText className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-slate-800">No documents found</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {searchTerm
                ? 'No documents match your current filter. Try searching for a different keyword.'
                : 'Upload your first PDF document to begin extracting text and answering questions with pgvector RAG.'}
            </p>
            {!searchTerm && (
              <button
                onClick={onOpenUpload}
                className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs rounded-xl shadow-xs transition-colors"
              >
                <FileUp className="w-3.5 h-3.5" />
                <span>Upload PDF</span>
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/70 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Document</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Pages & Chunks</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filtered.map((doc) => {
                  const isProcessing = processingIds.has(doc.id);
                  const canProcess =
                    doc.status === 'uploaded' ||
                    doc.status === 'failed' ||
                    doc.status === 'completed_with_warnings';

                  return (
                    <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                      {/* Document Name */}
                      <td className="py-3 px-4 font-medium">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div className="min-w-0 max-w-xs md:max-w-sm">
                            <p className="font-semibold text-slate-900 truncate" title={doc.original_filename}>
                              {doc.original_filename}
                            </p>
                            <p className="text-[11px] text-slate-400">
                              {formatFileSize(doc.file_size)}
                            </p>
                          </div>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <StatusBadge status={doc.status} size="sm" />
                          {doc.warnings && doc.warnings.ocr_needed && (
                            <span
                              className="text-amber-500 cursor-help"
                              title={doc.warnings.ocr_needed}
                            >
                              <AlertTriangle className="w-3.5 h-3.5" />
                            </span>
                          )}
                        </div>
                        {doc.error_message && (
                          <p className="text-[10px] text-rose-600 mt-0.5 truncate max-w-xs" title={doc.error_message}>
                            {doc.error_message}
                          </p>
                        )}
                      </td>

                      {/* Pages & Chunks */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3 text-slate-600 font-medium">
                          <span className="flex items-center gap-1" title="Page count">
                            <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                            {doc.page_count ?? '—'}
                          </span>
                          <span className="flex items-center gap-1" title="Chunks count">
                            <Layers className="w-3.5 h-3.5 text-slate-400" />
                            {doc.chunk_count}
                          </span>
                        </div>
                      </td>

                      {/* Upload Date */}
                      <td className="py-3 px-4 text-slate-500">
                        {formatDate(doc.created_at)}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {canProcess && (
                            <button
                              onClick={() => onProcess(doc.id)}
                              disabled={isProcessing}
                              title={doc.status === 'uploaded' ? 'Process document' : 'Retry processing'}
                              className="p-1.5 text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors disabled:opacity-50"
                            >
                              <RefreshCw
                                className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin text-indigo-600' : ''}`}
                              />
                            </button>
                          )}

                          <button
                            onClick={() => onAskDoc(doc.id)}
                            title="Ask questions about this document"
                            className="p-1.5 text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                          >
                            <MessageSquare className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => setDeleteTarget(doc)}
                            title="Delete document"
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={Boolean(deleteTarget)}
        onClose={() => !isDeleting && setDeleteTarget(null)}
        title="Confirm Deletion"
        maxWidth="sm"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-600">
            Are you sure you want to delete{' '}
            <strong className="text-slate-900">{deleteTarget?.original_filename}</strong>?
            This will permanently remove the document, its extracted pages, vector embeddings, and storage files.
          </p>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              onClick={() => setDeleteTarget(null)}
              disabled={isDeleting}
              className="px-3.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="px-3.5 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition-colors disabled:opacity-50 shadow-xs"
            >
              {isDeleting ? 'Deleting...' : 'Delete Permanently'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
