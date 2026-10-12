import React, { useEffect, useState } from 'react';
import { NavItem } from './Sidebar';
import { FileUp, Server, CheckCircle2, AlertCircle, Menu } from 'lucide-react';
import { checkBackendHealth } from '../../api/qa';

interface HeaderProps {
  currentTab: NavItem;
  onOpenUpload: () => void;
  onToggleMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentTab,
  onOpenUpload,
  onToggleMobileMenu,
}) => {
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        const res = await checkBackendHealth();
        if (isMounted) setBackendHealthy(res.status === 'healthy');
      } catch {
        if (isMounted) setBackendHealthy(false);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const titles: Record<NavItem, { title: string; subtitle: string }> = {
    dashboard: {
      title: 'Workspace Overview',
      subtitle: 'Monitor document processing statuses, vector counts, and recent uploads.',
    },
    documents: {
      title: 'Document Repository',
      subtitle: 'Manage uploaded PDFs, trigger text extraction, and inspect chunk metadata.',
    },
    ask: {
      title: 'Ask Documents',
      subtitle: 'Perform grounded semantic question answering with precise citations.',
    },
    settings: {
      title: 'System Settings',
      subtitle: 'Account details, Supabase authentication configuration, and API status.',
    },
  };

  const meta = titles[currentTab];

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        {onToggleMobileMenu && (
          <button
            onClick={onToggleMobileMenu}
            className="md:hidden p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div>
          <h1 className="text-base font-bold text-slate-900 tracking-tight">{meta.title}</h1>
          <p className="text-xs text-slate-500 hidden sm:block">{meta.subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend Health Indicator */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            backendHealthy === true
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : backendHealthy === false
              ? 'bg-rose-50 text-rose-700 border-rose-200'
              : 'bg-slate-50 text-slate-600 border-slate-200'
          }`}
          title={
            backendHealthy === true
              ? 'FastAPI Backend is online & healthy'
              : backendHealthy === false
              ? 'FastAPI Backend unreachable on port 8000'
              : 'Checking API health...'
          }
        >
          {backendHealthy === true ? (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          ) : backendHealthy === false ? (
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
          ) : (
            <Server className="w-3.5 h-3.5 text-slate-400" />
          )}
          <span className="hidden sm:inline">
            {backendHealthy === true
              ? 'API Online'
              : backendHealthy === false
              ? 'API Offline'
              : 'Connecting...'}
          </span>
        </div>

        {/* Upload Button */}
        <button
          onClick={onOpenUpload}
          className="flex items-center gap-1.5 py-1.5 px-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs rounded-lg shadow-xs shadow-indigo-200 transition-colors"
        >
          <FileUp className="w-3.5 h-3.5" />
          <span>Upload</span>
        </button>
      </div>
    </header>
  );
};
