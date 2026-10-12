import React, { useState, useRef, useEffect } from 'react';
import { DocumentItem, ChatMessage as ChatMessageType } from '../types';
import { ChatMessage } from '../components/qa/ChatMessage';
import { askQuestion } from '../api/qa';
import { formatApiError } from '../api/client';
import { 
  Send, 
  SlidersHorizontal, 
  Trash2, 
  FileText, 
  Sparkles, 
  ChevronDown,
  ChevronUp,
  AlertCircle
} from 'lucide-react';

interface AskPageProps {
  documents: DocumentItem[];
  selectedDocId?: string | null;
  onSelectDocId: (id: string | null) => void;
}

export const AskPage: React.FC<AskPageProps> = ({
  documents,
  selectedDocId,
  onSelectDocId,
}) => {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [minSimilarity, setMinSimilarity] = useState(0.2);
  const [showSettings, setShowSettings] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const readyDocuments = documents.filter(
    (d) => d.status === 'completed' || d.status === 'completed_with_warnings'
  );

  const selectedDocument = documents.find((d) => d.id === selectedDocId);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (questionText?: string) => {
    const textToSend = (questionText || question).trim();
    if (!textToSend || isSubmitting) return;

    const userMessage: ChatMessageType = {
      id: String(Date.now()),
      role: 'user',
      content: textToSend,
      timestamp: new Date().toISOString(),
    };

    const tempAssistantId = String(Date.now() + 1);
    const pendingAssistantMessage: ChatMessageType = {
      id: tempAssistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      loading: true,
    };

    setMessages((prev) => [...prev, userMessage, pendingAssistantMessage]);
    setQuestion('');
    setIsSubmitting(true);

    try {
      const response = await askQuestion({
        question: textToSend,
        document_id: selectedDocId || undefined,
        top_k: topK,
        min_similarity: minSimilarity,
      });

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempAssistantId
            ? {
                ...msg,
                content: response.answer,
                citations: response.citations,
                loading: false,
              }
            : msg
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === tempAssistantId
            ? {
                ...msg,
                loading: false,
                error: formatApiError(err),
              }
            : msg
        )
      );
    } finally {
      setIsSubmitting(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearHistory = () => {
    setMessages([]);
  };

  const starterQuestions = [
    'What are the core conclusions and findings in these documents?',
    'Summarize the key architectural decisions and requirements.',
    'List any identified risk factors, constraints, or next steps.',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
      {/* Top Controls Bar */}
      <div className="px-6 py-3.5 border-b border-slate-100 bg-slate-50/50 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3">
          {/* Document Scope Selector */}
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-400" />
            <select
              value={selectedDocId || ''}
              onChange={(e) => onSelectDocId(e.target.value || null)}
              className="text-xs font-semibold bg-white border border-slate-200 rounded-xl px-3 py-1.5 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800"
            >
              <option value="">All Documents ({readyDocuments.length} ready)</option>
              {readyDocuments.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.original_filename} ({doc.chunk_count} chunks)
                </option>
              ))}
            </select>
          </div>

          {selectedDocument && (
            <span className="text-[11px] text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full font-medium border border-indigo-100 hidden md:inline">
              Restricted to: {selectedDocument.original_filename}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Settings Toggle */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
              showSettings
                ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>Retrieval Settings</span>
            {showSettings ? (
              <ChevronUp className="w-3 h-3 ml-0.5" />
            ) : (
              <ChevronDown className="w-3 h-3 ml-0.5" />
            )}
          </button>

          {/* Clear Chat */}
          {messages.length > 0 && (
            <button
              onClick={handleClearHistory}
              title="Clear session history"
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Expandable Retrieval Settings Panel */}
      {showSettings && (
        <div className="px-6 py-3 bg-slate-50 border-b border-slate-200/80 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs animate-in slide-in-from-top-2 duration-150">
          <div>
            <div className="flex items-center justify-between text-slate-700 font-semibold mb-1">
              <span>Top-K Passages: {topK}</span>
              <span className="text-slate-400 text-[11px]">Range: 1–20</span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <p className="text-[10px] text-slate-400 mt-0.5">
              Number of closest semantic chunks retrieved via pgvector.
            </p>
          </div>

          <div>
            <div className="flex items-center justify-between text-slate-700 font-semibold mb-1">
              <span>Min Similarity: {minSimilarity.toFixed(2)}</span>
              <span className="text-slate-400 text-[11px]">0.0 – 1.0</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={minSimilarity}
              onChange={(e) => setMinSimilarity(Number(e.target.value))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <p className="text-[10px] text-slate-400 mt-0.5">
              Cosine similarity threshold (1 - distance) required for citations.
            </p>
          </div>
        </div>
      )}

      {/* Chat Messages Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {readyDocuments.length === 0 && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <p className="font-semibold">No ready documents in your workspace</p>
              <p className="text-[11px] text-amber-700 mt-0.5">
                Upload and process at least one PDF in "My Documents" before asking questions.
              </p>
            </div>
          </div>
        )}

        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center shadow-xs">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-800">Grounded Document Q&A</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Ask questions about your uploaded PDFs. Answers are strictly synthesized from retrieved passages with verified citations.
              </p>
            </div>

            {/* Starter Suggestion Chips */}
            <div className="w-full space-y-2 pt-2">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Suggested Questions
              </p>
              {starterQuestions.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(sq)}
                  disabled={readyDocuments.length === 0 || isSubmitting}
                  className="w-full text-left p-2.5 rounded-xl border border-slate-200/80 hover:border-indigo-300 hover:bg-indigo-50/50 text-xs text-slate-700 transition-all font-medium disabled:opacity-50 disabled:pointer-events-none"
                >
                  "{sq}"
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-slate-100 bg-white shrink-0">
        <div className="relative flex items-center">
          <input
            ref={inputRef}
            type="text"
            placeholder={
              readyDocuments.length === 0
                ? 'Upload and process a document to start asking questions...'
                : selectedDocument
                ? `Ask a question about ${selectedDocument.original_filename}...`
                : 'Ask a question across all your uploaded documents...'
            }
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSubmitting || readyDocuments.length === 0}
            className="w-full pl-4 pr-12 py-3 text-xs rounded-xl border border-slate-200/80 bg-slate-50/50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:opacity-50 transition-all"
          />
          <button
            onClick={() => handleSend()}
            disabled={!question.trim() || isSubmitting || readyDocuments.length === 0}
            className="absolute right-2 p-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-xs"
            aria-label="Send question"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 px-1">
          <span>Press Enter to send</span>
          <span>Citations are verified against retrieved pgvector chunks</span>
        </div>
      </div>
    </div>
  );
};
