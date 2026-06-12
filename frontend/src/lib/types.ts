/* ============================================================
   DocIntel AI — TypeScript Interfaces
   ============================================================ */

export interface Citation {
  document_id: string;
  document_name: string;
  page_number: number;
  image_url: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: string;
}

export interface DocumentClassification {
  document_type: string;
  topic: string;
  language: string;
  content_characteristics: {
    has_tables: boolean;
    has_images: boolean;
    has_handwriting: boolean;
    is_scanned: boolean;
    page_count: number;
  };
  sensitivity_level: string;
  summary: string;
  key_entities: string[];
  date_references: string[];
}

export interface DocumentInfo {
  id: string;
  original_filename: string;
  status: 'uploading' | 'parsing' | 'classifying' | 'indexing' | 'ready' | 'error';
  classification?: DocumentClassification;
  page_count?: number;
  upload_time: string;
  error_message?: string;
}

export interface UploadJob {
  file: File;
  id?: string;
  status: 'pending' | 'uploading' | 'parsing' | 'classifying' | 'indexing' | 'ready' | 'error';
  progress: number;
  error?: string;
  classification?: DocumentClassification;
}

export interface ApiError {
  detail: string;
  status: number;
}
