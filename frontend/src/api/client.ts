import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { supabase } from '../lib/supabase';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export function getBackendRootUrl(baseUrl: string = API_BASE_URL): string {
  return baseUrl.replace(/\/api\/v1\/?$/, '');
}

export const BACKEND_ROOT_URL = getBackendRootUrl(API_BASE_URL);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // 45 seconds to accommodate LLM processing
});

// Attach Supabase JWT Bearer token to every request
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    try {
      const { data } = await supabase.auth.getSession();
      const token = data.session?.access_token || localStorage.getItem('documind_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      // If session retrieval fails, fallback to stored token
      const fallbackToken = localStorage.getItem('documind_token');
      if (fallbackToken && config.headers) {
        config.headers.Authorization = `Bearer ${fallbackToken}`;
      }
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Format API error messages consistently
export function formatApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
    }
    if (error.response?.status === 401) {
      return 'Session expired or unauthenticated. Please sign in again.';
    }
    if (error.response?.status === 403) {
      return 'Access forbidden.';
    }
    if (error.response?.status === 404) {
      return 'Resource not found.';
    }
    if (error.response?.status === 413) {
      return 'File size exceeds 50MB limit.';
    }
    if (error.response?.status === 409) {
      return 'Document with identical content already exists.';
    }
    if (error.response?.status === 503) {
      return 'Service temporarily unavailable.';
    }
    if (error.response?.status === 504) {
      return 'Request timed out waiting for AI response.';
    }
    if (error.code === 'ERR_NETWORK') {
      return 'Could not connect to DocuMind backend server. Is it running on port 8000?';
    }
    return error.message || 'An unexpected API error occurred.';
  }
  return (error as Error)?.message || 'An unknown error occurred.';
}

// Backend dev demo login
export async function loginDemoUser(userKey: 'demo-a' | 'demo-b'): Promise<{
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
}> {
  const response = await apiClient.post('/auth/demo-login', { user_key: userKey });
  return response.data;
}

// Backend safe config status check
export async function getAuthConfigStatus(): Promise<{
  supabase_configured: boolean;
  supabase_url_configured: boolean;
  supabase_jwt_secret_configured: boolean;
  supabase_service_role_key_configured: boolean;
  demo_login_enabled: boolean;
}> {
  const response = await apiClient.get('/auth/config-status');
  return response.data;
}
