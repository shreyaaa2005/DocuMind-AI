import { apiClient, BACKEND_ROOT_URL } from './client';
import { AskRequest, AskResponse } from '../types';

export async function askQuestion(params: AskRequest): Promise<AskResponse> {
  const payload: Record<string, any> = {
    question: params.question.trim(),
    top_k: params.top_k ?? 5,
  };

  if (params.min_similarity !== undefined && params.min_similarity !== null) {
    payload.min_similarity = params.min_similarity;
  }

  if (params.document_id) {
    payload.document_id = params.document_id;
  }

  const response = await apiClient.post<AskResponse>('/qa/ask', payload);
  return response.data;
}

export async function checkBackendHealth(): Promise<{ status: string }> {
  const response = await apiClient.get<{ status: string }>('/health', {
    baseURL: BACKEND_ROOT_URL,
  });
  return response.data;
}
