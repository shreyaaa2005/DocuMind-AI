import React, { createContext, useContext, useEffect, useState } from 'react';
import { Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../lib/supabase';

interface AuthUser {
  id: string;
  email: string;
}

interface AuthContextType {
  user: AuthUser | null;
  session: Session | null;
  loading: boolean;
  error: string | null;
  isConfigured: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  signInWithTestToken: (token: string, userId: string, email: string) => void;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const configured = isSupabaseConfigured();

  useEffect(() => {
    // 1. Check for active Supabase session
    async function initAuth() {
      try {
        if (configured) {
          const { data, error: sessionError } = await supabase.auth.getSession();
          if (sessionError) {
            console.warn('Supabase getSession error:', sessionError);
          }
          if (data.session) {
            setSession(data.session);
            setUser({
              id: data.session.user.id,
              email: data.session.user.email || 'user@documind.ai',
            });
            localStorage.setItem('documind_token', data.session.access_token);
          } else {
            // Check if there is a preserved test token in localStorage
            const localToken = localStorage.getItem('documind_token');
            const localUser = localStorage.getItem('documind_user');
            if (localToken && localUser) {
              try {
                const parsedUser = JSON.parse(localUser);
                setUser(parsedUser);
              } catch {
                localStorage.removeItem('documind_token');
                localStorage.removeItem('documind_user');
              }
            }
          }
        } else {
          // If Supabase not yet configured, restore any test token
          const localToken = localStorage.getItem('documind_token');
          const localUser = localStorage.getItem('documind_user');
          if (localToken && localUser) {
            try {
              const parsedUser = JSON.parse(localUser);
              setUser(parsedUser);
            } catch {
              localStorage.removeItem('documind_token');
              localStorage.removeItem('documind_user');
            }
          }
        }
      } catch (err) {
        console.error('Error during auth initialization:', err);
      } finally {
        setLoading(false);
      }
    }

    initAuth();

    // 2. Subscribe to auth state changes
    if (configured) {
      const { data: authListener } = supabase.auth.onAuthStateChange(
        (_event, newSession) => {
          setSession(newSession);
          if (newSession?.user) {
            setUser({
              id: newSession.user.id,
              email: newSession.user.email || 'user@documind.ai',
            });
            localStorage.setItem('documind_token', newSession.access_token);
          } else {
            // Only clear user if no local dev token
            if (!localStorage.getItem('documind_test_mode')) {
              setUser(null);
              localStorage.removeItem('documind_token');
            }
          }
          setLoading(false);
        }
      );

      return () => {
        authListener.subscription.unsubscribe();
      };
    }
  }, [configured]);

  const signIn = async (email: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      if (!configured) {
        throw new Error(
          'Supabase is not configured yet. Please enter your Supabase URL & Key in .env, or use Test/Demo Mode.'
        );
      }
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (signInError) {
        throw signInError;
      }
      if (data.session) {
        setSession(data.session);
        setUser({
          id: data.session.user.id,
          email: data.session.user.email || email,
        });
        localStorage.setItem('documind_token', data.session.access_token);
        localStorage.removeItem('documind_test_mode');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to sign in. Please verify your credentials.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      if (!configured) {
        throw new Error(
          'Supabase is not configured yet. Please configure .env to create real Supabase users.'
        );
      }
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      });
      if (signUpError) {
        throw signUpError;
      }
      if (data.session) {
        setSession(data.session);
        setUser({
          id: data.session.user.id,
          email: data.session.user.email || email,
        });
        localStorage.setItem('documind_token', data.session.access_token);
      } else {
        // Confirmation email may be required
        setError('Confirmation email sent! Please check your inbox.');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to sign up.');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    try {
      if (configured) {
        await supabase.auth.signOut();
      }
    } catch (err) {
      console.warn('Error during Supabase signout:', err);
    } finally {
      setUser(null);
      setSession(null);
      localStorage.removeItem('documind_token');
      localStorage.removeItem('documind_user');
      localStorage.removeItem('documind_test_mode');
    }
  };

  const signInWithTestToken = (token: string, userId: string, email: string) => {
    const testUser: AuthUser = { id: userId, email };
    setUser(testUser);
    localStorage.setItem('documind_token', token);
    localStorage.setItem('documind_user', JSON.stringify(testUser));
    localStorage.setItem('documind_test_mode', 'true');
    setError(null);
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        error,
        isConfigured: configured,
        signIn,
        signUp,
        signOut,
        signInWithTestToken,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
