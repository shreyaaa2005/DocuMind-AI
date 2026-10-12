import React from 'react';
import { ChatMessage as ChatMessageType } from '../../types';
import { CitationCard } from './CitationCard';
import { BrainCircuit, User, Loader2, AlertCircle, Quote } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex items-start justify-end gap-3 max-w-3xl ml-auto">
        <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-xs px-4 py-3 text-xs leading-relaxed shadow-xs">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className="w-8 h-8 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 text-xs font-bold">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 max-w-3xl mr-auto">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center shrink-0 shadow-xs shadow-indigo-200">
        <BrainCircuit className="w-4 h-4" />
      </div>

      <div className="flex-1 space-y-3">
        {/* Message Content */}
        <div className="bg-white border border-slate-200/80 rounded-2xl rounded-tl-xs px-5 py-4 shadow-xs text-xs text-slate-800 leading-relaxed">
          {message.loading ? (
            <div className="flex items-center gap-2 text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
              <span>Analyzing document context and synthesizing grounded answer...</span>
            </div>
          ) : message.error ? (
            <div className="flex items-start gap-2 text-rose-600">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Unable to generate answer</p>
                <p className="text-[11px] mt-0.5 text-rose-500">{message.error}</p>
              </div>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none text-slate-800">
              <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
            </div>
          )}
        </div>

        {/* Citations Section */}
        {message.citations && message.citations.length > 0 && (
          <div className="space-y-2 pt-1 pl-1">
            <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-semibold uppercase tracking-wider">
              <Quote className="w-3 h-3 text-indigo-600" />
              <span>Grounded Citations ({message.citations.length})</span>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {message.citations.map((c, idx) => (
                <CitationCard key={idx} citation={c} index={idx} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
