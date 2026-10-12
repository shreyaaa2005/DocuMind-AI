import { apiClient } from './client';
import { SearchRequest, SearchResult } from '../types';

export async function searchDocuments(params: SearchRequest): Promise<SearchResult[]> {
  const response = await apiClient.post<SearchResult[]>('/search/', {
    query: params.query.trim(),
    top_k: params.top_k ?? 5,
    min_similarity: params.min_similarity ?? 0.5,
  });
  return response.data;
}
