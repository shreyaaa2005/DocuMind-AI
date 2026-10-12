import React, { useState, useEffect, useCallback } from 'react';
import { useAuth, AuthProvider } from './context/AuthContext';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { AskPage } from './pages/AskPage';
import { SettingsPage } from './pages/SettingsPage';
import { Sidebar, NavItem } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { UploadModal } from './components/documents/UploadModal';
import { listDocuments, processDocument, deleteDocument } from './api/documents';
import { formatApiError } from './api/client';
import { DocumentItem } from './types';
import { Loader2 } from 'lucide-react';

const MainLayout: React.FC = () => {
  const { user, loading: authLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<NavItem>('dashboard');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const fetchDocuments = useCallback(async () => {
    if (!user) return;
    setLoadingDocs(true);
    setError(null);
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoadingDocs(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchDocuments();
    }
  }, [user, fetchDocuments]);

  const handleProcess = async (docId: string) => {
    setProcessingIds((prev) => new Set(prev).add(docId));
    setError(null);
    try {
      const updated = await processDocument(docId);
      setDocuments((prev) =>
        prev.map((d) => (d.id === docId ? { ...d, ...updated } : d))
      );
    } catch (err) {
      setError(formatApiError(err));
      // Refresh to ensure database state is synchronized
      await fetchDocuments();
    } finally {
      setProcessingIds((prev) => {
        const next = new Set(prev);
        next.delete(docId);
        return next;
      });
    }
  };

  const handleDelete = async (docId: string) => {
    setError(null);
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (selectedDocId === docId) {
        setSelectedDocId(null);
      }
    } catch (err) {
      setError(formatApiError(err));
    }
  };

  const handleUploadSuccess = (newDoc: DocumentItem) => {
    setDocuments((prev) => {
      const exists = prev.some((d) => d.id === newDoc.id);
      if (exists) {
        return prev.map((d) => (d.id === newDoc.id ? newDoc : d));
      }
      return [newDoc, ...prev];
    });
  };

  const handleSelectForAsk = (docId: string) => {
    setSelectedDocId(docId);
    setCurrentTab('ask');
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-500 text-xs font-medium">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
          <span>Initializing DocuMind AI...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage />;
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex shrink-0">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          onOpenUpload={() => setIsUploadOpen(true)}
          documentCount={documents.length}
        />
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white z-10">
            <Sidebar
              currentTab={currentTab}
              onSelectTab={(tab) => {
                setCurrentTab(tab);
                setMobileMenuOpen(false);
              }}
              onOpenUpload={() => {
                setIsUploadOpen(true);
                setMobileMenuOpen(false);
              }}
              documentCount={documents.length}
            />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          currentTab={currentTab}
          onOpenUpload={() => setIsUploadOpen(true)}
          onToggleMobileMenu={() => setMobileMenuOpen(true)}
        />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {currentTab === 'dashboard' && (
              <DashboardPage
                documents={documents}
                onNavigate={setCurrentTab}
                onOpenUpload={() => setIsUploadOpen(true)}
                onSelectForAsk={handleSelectForAsk}
                onProcess={handleProcess}
                processingIds={processingIds}
              />
            )}

            {currentTab === 'documents' && (
              <DocumentsPage
                documents={documents}
                loading={loadingDocs}
                onRefresh={fetchDocuments}
                onProcess={handleProcess}
                onDelete={handleDelete}
                onAskDoc={handleSelectForAsk}
                onOpenUpload={() => setIsUploadOpen(true)}
                processingIds={processingIds}
                error={error}
              />
            )}

            {currentTab === 'ask' && (
              <AskPage
                documents={documents}
                selectedDocId={selectedDocId}
                onSelectDocId={setSelectedDocId}
              />
            )}

            {currentTab === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
};

export default App;
