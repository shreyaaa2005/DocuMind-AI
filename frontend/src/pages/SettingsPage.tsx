import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { checkBackendHealth } from '../api/qa';
import { 
  User, 
  Server, 
  Database, 
  ShieldCheck, 
  LogOut, 
  CheckCircle2, 
  XCircle, 
  Loader2,
  Cpu
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { user, signOut, isConfigured } = useAuth();
  const [testingConnection, setTestingConnection] = useState(false);
  const [healthStatus, setHealthStatus] = useState<{
    healthy: boolean;
    latencyMs?: number;
    error?: string;
  } | null>(null);

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setHealthStatus(null);
    const start = performance.now();
    try {
      const res = await checkBackendHealth();
      const latency = Math.round(performance.now() - start);
      setHealthStatus({ healthy: res.status === 'healthy', latencyMs: latency });
    } catch (err: any) {
      setHealthStatus({
        healthy: false,
        error: err.message || 'Failed to reach backend endpoint.',
      });
    } finally {
      setTestingConnection(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-lg font-bold text-slate-900 tracking-tight">System Settings & Profile</h2>
        <p className="text-xs text-slate-500">
          Account details, Supabase identity provider status, and backend connectivity.
        </p>
      </div>

      {/* Account Info Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-sm">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">User Profile</h3>
            <p className="text-xs text-slate-500">Authenticated user identity</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 text-xs">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
              User ID (UUID)
            </span>
            <span className="font-mono text-slate-800 break-all mt-0.5 block">
              {user?.id || 'Unknown'}
            </span>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
              Email Address
            </span>
            <span className="text-slate-800 font-medium mt-0.5 block">
              {user?.email || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={() => signOut()}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-xl transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>

      {/* Backend & Architecture Overview */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Backend Services</h3>
              <p className="text-xs text-slate-500">FastAPI, PostgreSQL pgvector, and LLM orchestration</p>
            </div>
          </div>

          <button
            onClick={handleTestConnection}
            disabled={testingConnection}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-xl transition-colors disabled:opacity-50"
          >
            {testingConnection ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Pinging...</span>
              </>
            ) : (
              <span>Test Connection</span>
            )}
          </button>
        </div>

        {healthStatus && (
          <div
            className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
              healthStatus.healthy
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-rose-50 text-rose-800 border-rose-200'
            }`}
          >
            {healthStatus.healthy ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <div className="flex-1">
              {healthStatus.healthy ? (
                <span>
                  Backend is online and healthy. Response time: {healthStatus.latencyMs}ms.
                </span>
              ) : (
                <span>Backend connection failed: {healthStatus.error}</span>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-1">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 font-semibold mb-1">
              <Cpu className="w-3.5 h-3.5 text-indigo-600" />
              <span>Embedding Model</span>
            </div>
            <p className="font-medium text-slate-800">all-MiniLM-L6-v2</p>
            <p className="text-[11px] text-slate-400">384-dimensional dense vectors</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 font-semibold mb-1">
              <Database className="w-3.5 h-3.5 text-indigo-600" />
              <span>Vector Database</span>
            </div>
            <p className="font-medium text-slate-800">PostgreSQL + pgvector</p>
            <p className="text-[11px] text-slate-400">Cosine distance indexed</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <div className="flex items-center gap-1.5 text-slate-500 font-semibold mb-1">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
              <span>Auth Provider</span>
            </div>
            <p className="font-medium text-slate-800">
              {isConfigured ? 'Supabase Project' : 'Local Development Mode'}
            </p>
            <p className="text-[11px] text-slate-400">HS256 JWT with row isolation</p>
          </div>
        </div>
      </div>
    </div>
  );
};
