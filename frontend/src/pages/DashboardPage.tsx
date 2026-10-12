import React from 'react';
import { DocumentItem } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { 
  Files, 
  CheckCircle2, 
  Layers, 
  AlertTriangle, 
  FileUp, 
  MessageSquare, 
  ArrowRight,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { NavItem } from '../components/layout/Sidebar';

interface DashboardPageProps {
  documents: DocumentItem[];
  onNavigate: (tab: NavItem) => void;
  onOpenUpload: () => void;
  onSelectForAsk: (docId: string) => void;
  onProcess: (docId: string) => Promise<void>;
  processingIds: Set<string>;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  documents,
  onNavigate,
  onOpenUpload,
  onSelectForAsk,
  onProcess,
  processingIds,
}) => {
  const totalDocs = documents.length;
  const readyDocs = documents.filter((d) => d.status === 'completed' || d.status === 'completed_with_warnings').length;
  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);
  const pendingDocs = documents.filter((d) => d.status === 'uploaded' || d.status === 'extracting_text' || d.status === 'chunking' || d.status === 'generating_embeddings').length;

  const recentDocs = [...documents]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1 */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Total Documents</span>
            <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
              <Files className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">{totalDocs}</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Uploaded PDF records</p>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Ready for Q&A</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">{readyDocs}</h3>
            <p className="text-[11px] text-emerald-600 mt-0.5">Indexed with vector embeddings</p>
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Vector Chunks</span>
            <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">{totalChunks}</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">384-dim pgvector entries</p>
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Pending Processing</span>
            <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <h3 className="text-2xl font-bold text-slate-900">{pendingDocs}</h3>
            <p className="text-[11px] text-slate-400 mt-0.5">Awaiting extraction</p>
          </div>
        </div>
      </div>

      {/* Action Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900 to-slate-900 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-[11px] font-semibold border border-indigo-400/20">
            <Sparkles className="w-3 h-3" />
            RAG Pipeline Verified
          </div>
          <h3 className="text-lg font-bold">Ask intelligent questions over your uploaded documents</h3>
          <p className="text-xs text-slate-300 max-w-xl">
            DocuMind AI slices your PDFs into semantic passages, computes dense vectors with all-MiniLM-L6-v2, and answers questions with precise page citations.
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => onNavigate('ask')}
            className="px-4 py-2 bg-white hover:bg-slate-100 text-slate-900 text-xs font-semibold rounded-xl shadow-xs transition-colors flex items-center gap-1.5"
          >
            <MessageSquare className="w-3.5 h-3.5 text-indigo-600" />
            <span>Open Q&A Chat</span>
          </button>
          <button
            onClick={onOpenUpload}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors flex items-center gap-1.5"
          >
            <FileUp className="w-3.5 h-3.5" />
            <span>Upload PDF</span>
          </button>
        </div>
      </div>

      {/* Recent Documents Section */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Recent Documents</h3>
            <p className="text-xs text-slate-500">Your most recently uploaded research files</p>
          </div>
          <button
            onClick={() => onNavigate('documents')}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            <span>View all</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {recentDocs.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-xs">
            No documents uploaded yet. Upload your first PDF to see it here!
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recentDocs.map((doc) => {
              const isProcessing = processingIds.has(doc.id);
              const isReady = doc.status === 'completed' || doc.status === 'completed_with_warnings';

              return (
                <div key={doc.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-slate-800 truncate" title={doc.original_filename}>
                      {doc.original_filename}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {doc.page_count ?? 0} pages • {doc.chunk_count} chunks
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge status={doc.status} size="sm" />
                    {isReady ? (
                      <button
                        onClick={() => onSelectForAsk(doc.id)}
                        className="px-2.5 py-1 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors flex items-center gap-1"
                      >
                        <MessageSquare className="w-3 h-3" />
                        <span>Ask</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => onProcess(doc.id)}
                        disabled={isProcessing}
                        className="px-2.5 py-1 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors flex items-center gap-1"
                      >
                        <RefreshCw className={`w-3 h-3 ${isProcessing ? 'animate-spin' : ''}`} />
                        <span>Process</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
