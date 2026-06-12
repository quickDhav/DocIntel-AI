'use client';

/* ============================================================
   DocIntel AI — Upload / Knowledge Base Page
   ============================================================ */

import { useState, useEffect, useCallback } from 'react';
import { useUpload } from '@/hooks/useUpload';
import { DocumentInfo } from '@/lib/types';
import { getDocuments, deleteDocument } from '@/lib/api';
import FileUploader from '@/components/FileUploader';
import UploadProgress from '@/components/UploadProgress';

export default function UploadPage() {
  const {
    jobs,
    isUploading,
    pendingCount,
    addFiles,
    removeJob,
    startUpload,
    clearCompleted,
  } = useUpload();

  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);

  const fetchDocuments = useCallback(async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch {
    } finally {
      setDocsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    const allDone = jobs.length > 0 && jobs.every((j) => j.status === 'ready' || j.status === 'error');
    if (allDone) {
      fetchDocuments();
    }
  }, [jobs, fetchDocuments]);

  const handleDeleteDocument = async (docId: string) => {
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch {
    }
  };

  const readyDocs = documents.filter((d) => d.status === 'ready');

  return (
    <div className="upload-page" id="upload-page">
      {/* Header */}
      <div className="upload-header">
        <h1 className="text-gradient">Knowledge Base</h1>
        <p>Upload and manage your documents for intelligent analysis</p>
        <div className="upload-header-stats">
          <div className="upload-stat">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span className="upload-stat-value">{readyDocs.length}</span>
            documents indexed
          </div>
          {jobs.length > 0 && (
            <div className="upload-stat">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-teal)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 16 12 12 8 16" />
                <line x1="12" y1="12" x2="12" y2="21" />
                <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
              </svg>
              <span className="upload-stat-value">{jobs.length}</span>
              in queue
            </div>
          )}
        </div>
      </div>

      {/* File Uploader */}
      <FileUploader onFilesSelected={addFiles} disabled={isUploading} />

      {/* Upload Actions */}
      {jobs.length > 0 && (
        <div className="upload-actions">
          <button
            className="btn-primary"
            id="start-upload-btn"
            onClick={startUpload}
            disabled={pendingCount === 0 || isUploading}
          >
            {isUploading ? (
              <>
                <div className="spinner spinner-sm" style={{ borderTopColor: 'var(--text-inverse)' }} />
                Processing...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="16 16 12 12 8 16" />
                  <line x1="12" y1="12" x2="12" y2="21" />
                  <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
                </svg>
                Upload {pendingCount} file{pendingCount !== 1 ? 's' : ''}
              </>
            )}
          </button>

          {jobs.some((j) => j.status === 'ready' || j.status === 'error') && (
            <button
              className="btn-secondary"
              id="clear-completed-btn"
              onClick={clearCompleted}
            >
              Clear completed
            </button>
          )}
        </div>
      )}

      {/* Upload Jobs */}
      {jobs.length > 0 && (
        <div className="upload-jobs">
          <div className="upload-jobs-title">Upload Queue</div>
          <div className="upload-jobs-grid">
            {jobs.map((job, idx) => (
              <UploadProgress
                key={`${job.file.name}-${idx}`}
                job={job}
                index={idx}
                onRemove={removeJob}
              />
            ))}
          </div>
        </div>
      )}

      {/* Existing Documents */}
      <div className="documents-section" id="documents-section">
        <h2>
          <span className="text-gradient">Indexed Documents</span>
        </h2>

        {docsLoading ? (
          <div className="empty-state">
            <div className="spinner" />
          </div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <p>No documents uploaded yet</p>
            <span className="text-xs text-muted" style={{ marginTop: '4px' }}>
              Upload documents above to get started
            </span>
          </div>
        ) : (
          <div className="documents-grid">
            {documents.map((doc) => (
              <div
                className="document-card"
                key={doc.id}
                id={`doc-${doc.id}`}
              >
                <div className="document-card-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                </div>

                <div className="document-card-info">
                  <div className="document-card-name">
                    {doc.original_filename}
                  </div>
                  <div className="document-card-meta">
                    {doc.page_count && <span>{doc.page_count} pages</span>}
                    <span>
                      {new Date(doc.upload_time).toLocaleDateString()}
                    </span>
                  </div>
                  <span
                    className={`document-card-status ${
                      doc.status === 'ready'
                        ? 'ready'
                        : doc.status === 'error'
                        ? 'error'
                        : 'processing'
                    }`}
                  >
                    {doc.status === 'ready' && (
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                    {doc.status}
                  </span>
                </div>

                <button
                  className="document-card-delete"
                  onClick={() => handleDeleteDocument(doc.id)}
                  title="Delete document"
                  id={`delete-doc-${doc.id}`}
                  aria-label={`Delete ${doc.original_filename}`}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
