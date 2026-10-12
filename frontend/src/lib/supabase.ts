import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder-anon-key';

export interface SupabaseConfigInspection {
  isConfigured: boolean;
  hasUrl: boolean;
  hasAnonKey: boolean;
  missingVariables: string[];
}

export const inspectSupabaseConfig = (): SupabaseConfigInspection => {
  const url = import.meta.env.VITE_SUPABASE_URL;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
  
  const hasValidUrl = Boolean(url) && 
    !url.includes('your-supabase-project') && 
    !url.includes('placeholder') &&
    url.startsWith('http');

  const hasValidKey = Boolean(anonKey) && 
    !anonKey.includes('placeholder') && 
    !anonKey.includes('dummy') &&
    anonKey.length > 20;

  const missingVariables: string[] = [];
  if (!hasValidUrl) missingVariables.push('VITE_SUPABASE_URL');
  if (!hasValidKey) missingVariables.push('VITE_SUPABASE_ANON_KEY');

  return {
    isConfigured: hasValidUrl && hasValidKey,
    hasUrl: hasValidUrl,
    hasAnonKey: hasValidKey,
    missingVariables,
  };
};

export const isSupabaseConfigured = (): boolean => {
  return inspectSupabaseConfig().isConfigured;
};

export const supabase: SupabaseClient = createClient(
  supabaseUrl.startsWith('http') ? supabaseUrl : 'https://placeholder.supabase.co',
  supabaseAnonKey,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  }
);
