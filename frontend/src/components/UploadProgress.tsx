'use client';

/* ============================================================
   DocIntel AI — Upload Progress Card Component
   ============================================================ */

import { UploadJob } from '@/lib/types';

interface Props {
  job: UploadJob;
  index: number;
  onRemove: (index: number) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type StageStatus = 'pending' | 'active' | 'done' | 'error';

function getStageStatus(
  stage: 'parsing' | 'classifying' | 'indexing',
  jobStatus: string
): StageStatus {
  const order = ['uploading', 'parsing', 'classifying', 'indexing', 'ready'];
  const stageIndex = order.indexOf(stage);
  const currentIndex = order.indexOf(jobStatus);

  if (jobStatus === 'error') {
    if (currentIndex >= 0 && stageIndex <= currentIndex) return 'error';
    if (stageIndex < currentIndex) return 'done';
    return 'pending';
  }

  if (jobStatus === 'ready') return 'done';
  if (currentIndex > stageIndex) return 'done';
  if (currentIndex === stageIndex) return 'active';
  return 'pending';
}

function getConnectorStatus(
  fromStage: 'parsing' | 'classifying',
  jobStatus: string
): string {
  const order = ['uploading', 'parsing', 'classifying', 'indexing', 'ready'];
  const fromIndex = order.indexOf(fromStage);
  const currentIndex = order.indexOf(jobStatus);

  if (jobStatus === 'ready' || currentIndex > fromIndex + 1) return 'done';
  if (currentIndex === fromIndex + 1) return 'active';
  return '';
}

function StageIcon({ status }: { status: StageStatus }) {
  if (status === 'done') {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    );
  }
  if (status === 'error') {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    );
  }
  if (status === 'active') {
    return <div className="spinner spinner-sm" />;
  }
  return (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="4" />
    </svg>
  );
}

export default function UploadProgress({ job, index, onRemove }: Props) {
  const stages: Array<{ key: 'parsing' | 'classifying' | 'indexing'; label: string }> = [
    { key: 'parsing', label: 'Parsing' },
    { key: 'classifying', label: 'Classifying' },
    { key: 'indexing', label: 'Indexing' },
  ];

  return (
    <div className="upload-progress-card" id={`upload-job-${index}`}>
      {/* Header */}
      <div className="upload-progress-header">
        <div className="upload-progress-file">
          <div className="upload-progress-file-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <div className="upload-progress-file-info">
            <div className="upload-progress-file-name">{job.file.name}</div>
            <div className="upload-progress-file-size">
              {formatFileSize(job.file.size)}
            </div>
          </div>
        </div>

        {(job.status === 'pending' || job.status === 'ready' || job.status === 'error') && (
          <button
            className="upload-progress-remove"
            onClick={() => onRemove(index)}
            title="Remove"
            id={`upload-remove-${index}`}
            aria-label="Remove file"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>

      {/* Pipeline Stages */}
      {job.status !== 'pending' && (
        <div className="upload-pipeline">
          {stages.map((stage, i) => {
            const stageStatus = getStageStatus(stage.key, job.status);
            return (
              <div key={stage.key} style={{ display: 'contents' }}>
                <div className="upload-stage">
                  <div className={`upload-stage-icon ${stageStatus}`}>
                    <StageIcon status={stageStatus} />
                  </div>
                  <span className={`upload-stage-label ${stageStatus}`}>
                    {stage.label}
                  </span>
                </div>
                {i < stages.length - 1 && (
                  <div
                    className={`upload-stage-connector ${getConnectorStatus(
                      stage.key as 'parsing' | 'classifying',
                      job.status
                    )}`}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Progress Bar */}
      {job.status !== 'pending' && (
        <div className="upload-progress-bar-container">
          <div
            className={`upload-progress-bar${job.status === 'error' ? ' error' : ''}`}
            style={{ width: `${job.progress}%` }}
          />
        </div>
      )}

      {/* Classification Summary */}
      {job.status === 'ready' && job.classification && (
        <div className="upload-classification">
          <div className="upload-classification-row">
            <span className="upload-classification-label">Type</span>
            <span className="upload-classification-value">
              {job.classification.document_type}
            </span>
          </div>
          <div className="upload-classification-row">
            <span className="upload-classification-label">Topic</span>
            <span className="upload-classification-value">
              {job.classification.topic}
            </span>
          </div>
          <div className="upload-classification-row">
            <span className="upload-classification-label">Language</span>
            <span className="upload-classification-value">
              {job.classification.language}
            </span>
          </div>
          {job.classification.key_entities.length > 0 && (
            <div className="upload-classification-tags">
              {job.classification.key_entities.slice(0, 5).map((entity) => (
                <span key={entity} className="upload-classification-tag">
                  {entity}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {job.status === 'error' && job.error && (
        <div className="upload-error">{job.error}</div>
      )}
    </div>
  );
}
