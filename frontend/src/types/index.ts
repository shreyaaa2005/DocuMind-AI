export type DocumentStatus =
  | 'uploaded'
  | 'validating'
  | 'extracting_text'
  | 'ocr_processing'
  | 'chunking'
  | 'generating_embeddings'
  | 'indexing'
  | 'completed'
  | 'completed_with_warnings'
  | 'failed';

export type ExtractionMethod = 'text' | 'ocr' | 'mixed';

export interface DocumentItem {
  id: string;
  owner_id: string;
  original_filename: string;
  stored_path?: string;
  file_size: number;
  content_hash: string;
  page_count: number | null;
  status: DocumentStatus;
  extraction_method: ExtractionMethod | null;
  ocr_status?: string | null;
  chunk_count: number;
  error_code: string | null;
  error_message: string | null;
  warnings: Record<string, any> | null;
  retry_count: number;
  created_at: string;
  updated_at?: string | null;
}

export interface UploadResponse {
  id: string;
  original_filename: string;
  status: DocumentStatus;
  file_size: number;
}

export interface ProcessResponse {
  id: string;
  original_filename?: string;
  status: DocumentStatus;
  page_count: number | null;
  chunk_count: number;
  extraction_method: ExtractionMethod | null;
  warnings: Record<string, any> | null;
  error_code: string | null;
  error_message: string | null;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  min_similarity?: number;
}

export interface SearchResult {
  document_id: string;
  document_name: string;
  page_start: number;
  page_end: number;
  text: string;
  similarity_score: number;
}

export interface AskRequest {
  question: string;
  document_id?: string;
  top_k?: number;
  min_similarity?: number;
}

export interface Citation {
  document_id: string;
  document_name: string;
  page_start: number;
  page_end: number;
  text: string;
  similarity_score: number;
}

export interface AskResponse {
  answer: string;
  citations: Citation[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: Citation[];
  loading?: boolean;
  error?: string;
}
