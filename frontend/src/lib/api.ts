/* ============================================================
   DocIntel AI — API Client
   ============================================================ */

import { ChatMessage, DocumentInfo } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';


class ApiClientError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiClientError';
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = 'An unexpected error occurred';
    try {
      const body = await response.json();
      detail = body.detail || body.message || detail;
    } catch {
    }
    throw new ApiClientError(response.status, detail);
  }
  return response.json();
}


export function generateSessionId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getOrCreateSessionId(): string {
  if (typeof window === 'undefined') return generateSessionId();

  const KEY = 'docintel_session_id';
  let sessionId = localStorage.getItem(KEY);
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(KEY, sessionId);
  }
  return sessionId;
}


export async function uploadFiles(
  files: File[]
): Promise<{ job_ids: string[] }> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse<{ job_ids: string[] }>(response);
}

export async function getUploadStatus(jobId: string): Promise<DocumentInfo> {
  const response = await fetch(`${API_BASE}/api/documents/${jobId}/status`);
  return handleResponse<DocumentInfo>(response);
}


export async function sendMessage(
  message: string,
  sessionId: string
): Promise<ChatMessage> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  return handleResponse<ChatMessage>(response);
}

export async function getChatHistory(
  sessionId: string
): Promise<ChatMessage[]> {
  const response = await fetch(
    `${API_BASE}/api/chat/history?session_id=${encodeURIComponent(sessionId)}`
  );
  return handleResponse<ChatMessage[]>(response);
}

export async function clearChatHistory(sessionId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/chat/history?session_id=${encodeURIComponent(sessionId)}`,
    { method: 'DELETE' }
  );
  if (!response.ok) {
    throw new ApiClientError(response.status, 'Failed to clear history');
  }
}


export async function getDocuments(): Promise<DocumentInfo[]> {
  const response = await fetch(`${API_BASE}/api/documents`);
  return handleResponse<DocumentInfo[]>(response);
}

export async function deleteDocument(docId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new ApiClientError(response.status, 'Failed to delete document');
  }
}


export function getPageImageUrl(
  docId: string,
  pageNum: number,
  size: string = 'full'
): string {
  return `${API_BASE}/api/documents/${docId}/pages/${pageNum}/image?size=${size}`;
}

export async function getPageText(
  docId: string,
  pageNum: number
): Promise<string> {
  const response = await fetch(
    `${API_BASE}/api/documents/${docId}/pages/${pageNum}/text`
  );
  const data = await handleResponse<{ text: string }>(response);
  return data.text;
}
