import React, { useState } from 'react';
import { Citation } from '../../types';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface CitationCardProps {
  citation: Citation;
  index: number;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const pageLabel =
    citation.page_start === citation.page_end
      ? `Page ${citation.page_start}`
      : `Pages ${citation.page_start}–${citation.page_end}`;

  const similarityPercent = Math.round(citation.similarity_score * 100);

  return (
    <div className="bg-slate-50/80 hover:bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs transition-colors">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-5 h-5 rounded-md bg-indigo-100/70 text-indigo-700 flex items-center justify-center text-[10px] font-bold shrink-0">
            {index + 1}
          </div>
          <span className="font-semibold text-slate-800 truncate" title={citation.document_name}>
            {citation.document_name}
          </span>
          <span className="text-slate-400">•</span>
          <span className="text-slate-500 font-medium shrink-0">{pageLabel}</span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span
            className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200/60"
            title="Cosine similarity score"
          >
            {similarityPercent}% match
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-slate-400 hover:text-slate-600 rounded"
            aria-label={isExpanded ? 'Collapse excerpt' : 'Expand excerpt'}
          >
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
        </div>
      </div>

      <div className="mt-2 text-slate-600 font-mono text-[11px] leading-relaxed bg-white p-2 rounded-lg border border-slate-100">
        <p className={isExpanded ? '' : 'line-clamp-2'}>"{citation.text}"</p>
      </div>
    </div>
  );
};
