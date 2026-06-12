'use client';

/* ============================================================
   DocIntel AI — File Uploader (Drag & Drop) Component
   ============================================================ */

import { useRef, useState, DragEvent, ChangeEvent } from 'react';

interface Props {
  onFilesSelected: (files: File[]) => void;
  disabled: boolean;
}

const ACCEPTED_TYPES = '.pdf,.png,.jpg,.jpeg,.tiff,.txt';
const ACCEPTED_MIME = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/tiff',
  'text/plain',
];

export default function FileUploader({ onFilesSelected, disabled }: Props) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files).filter((file) =>
      ACCEPTED_MIME.some((mime) => file.type === mime) ||
      file.name.toLowerCase().endsWith('.tiff')
    );

    if (files.length > 0) {
      onFilesSelected(files);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (files.length > 0) {
      onFilesSelected(files);
    }
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleClick = () => {
    if (!disabled) inputRef.current?.click();
  };

  return (
    <div
      className={`file-uploader${isDragOver ? ' drag-over' : ''}${disabled ? ' disabled' : ''}`}
      id="file-uploader"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label="Upload files"
    >
      <div className="file-uploader-content">
        {/* Icon */}
        <div className="file-uploader-icon">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>

        {/* Text */}
        <div className="file-uploader-text">
          <strong>Drop files here</strong> or click to browse
        </div>

        {/* Format badges */}
        <div className="file-uploader-formats">
          {['PDF', 'PNG', 'JPG', 'TIFF', 'TXT'].map((fmt) => (
            <span key={fmt} className="file-format-badge">
              {fmt}
            </span>
          ))}
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        className="file-uploader-hidden-input"
        id="file-input"
        accept={ACCEPTED_TYPES}
        multiple
        onChange={handleChange}
      />
    </div>
  );
}
