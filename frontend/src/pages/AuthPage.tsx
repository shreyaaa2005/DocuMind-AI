import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { inspectSupabaseConfig } from '../lib/supabase';
import { loginDemoUser, formatApiError } from '../api/client';
import { 
  BrainCircuit, 
  Lock, 
  Mail, 
  AlertCircle, 
  Loader2, 
  ArrowRight,
  ShieldCheck,
  Zap,
  CheckCircle
} from 'lucide-react';

export const AuthPage: React.FC = () => {
  const { signIn, signUp, signInWithTestToken, error, clearError } = useAuth();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState<string | null>(null);
  const [demoError, setDemoError] = useState<string | null>(null);

  const configStatus = inspectSupabaseConfig();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    setLoading(true);
    try {
      if (mode === 'signin') {
        await signIn(email, password);
      } else {
        await signUp(email, password);
      }
    } catch {
      // Error handled by AuthContext
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (userKey: 'demo-a' | 'demo-b') => {
    setDemoLoading(userKey);
    setDemoError(null);
    try {
      const data = await loginDemoUser(userKey);
      signInWithTestToken(data.access_token, data.user_id, data.email);
    } catch (err: any) {
      setDemoError(
        formatApiError(err) || 'Demo login failed. Is backend running on port 8000?'
      );
    } finally {
      setDemoLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        {/* Brand Icon */}
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center mx-auto shadow-md shadow-indigo-200">
          <BrainCircuit className="w-7 h-7" />
        </div>
        <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">
          DocuMind AI
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Enterprise Document Intelligence & RAG Question Answering
        </p>

        {/* Safe Configuration Status Banner */}
        <div className="mt-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium border bg-white shadow-xs">
          {configStatus.isConfigured ? (
            <span className="flex items-center gap-1 text-emerald-700">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
              <span>Supabase Connected</span>
            </span>
          ) : (
            <span className="flex items-center gap-1 text-amber-700">
              <AlertCircle className="w-3.5 h-3.5 text-amber-500" />
              <span>
                Missing in frontend/.env: {configStatus.missingVariables.join(', ')}
              </span>
            </span>
          )}
        </div>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white py-8 px-6 shadow-sm border border-slate-200/80 rounded-2xl sm:px-10">
          {/* Mode Switch Tabs */}
          <div className="flex rounded-xl bg-slate-100 p-1 mb-6">
            <button
              type="button"
              onClick={() => {
                setMode('signin');
                clearError();
                setDemoError(null);
              }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                mode === 'signin'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('signup');
                clearError();
                setDemoError(null);
              }}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all ${
                mode === 'signup'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Form */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold text-slate-700">
                Email address
              </label>
              <div className="mt-1 relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@enterprise.com"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700">
                Password
              </label>
              <div className="mt-1 relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs shadow-indigo-200 transition-colors disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Please wait...</span>
                </>
              ) : (
                <>
                  <span>{mode === 'signin' ? 'Sign in to Workspace' : 'Create Account'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Access Notice for Reviewers */}
          <div className="mt-6 pt-6 border-t border-slate-100">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 mb-2">
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              <span>Quick Development Access</span>
            </div>
            <p className="text-[11px] text-slate-500 mb-3">
              Testing locally without Supabase credentials? Click below to instantly launch as an isolated test user:
            </p>

            {demoError && (
              <div className="mb-3 p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-[11px] flex items-start gap-2">
                <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-600" />
                <span>{demoError}</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                disabled={Boolean(demoLoading)}
                onClick={() => handleQuickDemoLogin('demo-a')}
                className="py-1.5 px-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-medium text-[11px] rounded-lg transition-colors flex items-center justify-center gap-1 disabled:opacity-50"
              >
                {demoLoading === 'demo-a' ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span>Demo User A</span>
                )}
              </button>
              <button
                type="button"
                disabled={Boolean(demoLoading)}
                onClick={() => handleQuickDemoLogin('demo-b')}
                className="py-1.5 px-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-medium text-[11px] rounded-lg transition-colors flex items-center justify-center gap-1 disabled:opacity-50"
              >
                {demoLoading === 'demo-b' ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span>Demo User B</span>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Security Assurance */}
        <div className="mt-4 text-center flex items-center justify-center gap-1.5 text-xs text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Supabase JWT Bearer Auth with Per-User Row-Level Isolation</span>
        </div>
      </div>
    </div>
  );
};
