import { apiClient } from './client';
import { DocumentItem, UploadResponse, ProcessResponse } from '../types';

export async function uploadDocument(
  file: File,
  onProgress?: (percent: number) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<UploadResponse>('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  return response.data;
}

export async function processDocument(documentId: string): Promise<ProcessResponse> {
  const response = await apiClient.post<ProcessResponse>(`/documents/${documentId}/process`);
  return response.data;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  const response = await apiClient.get<DocumentItem[]>('/documents/');
  return response.data;
}

export async function getDocument(documentId: string): Promise<DocumentItem> {
  const response = await apiClient.get<DocumentItem>(`/documents/${documentId}`);
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<{ message: string }> {
  const response = await apiClient.delete<{ message: string }>(`/documents/${documentId}`);
  return response.data;
}
