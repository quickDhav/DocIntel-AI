'use client';

/* ============================================================
   DocIntel AI — Page Image Modal Component
   ============================================================ */

import { useEffect, useCallback } from 'react';
import { getPageImageUrl } from '@/lib/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  docId: string;
  pageNumber: number;
  docName: string;
}

export default function PageModal({
  isOpen,
  onClose,
  docId,
  pageNumber,
  docName,
}: Props) {
  const imageUrl = getPageImageUrl(docId, pageNumber, 'full');

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-overlay"
      id="page-modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="modal-content" id="page-modal-content">
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-title">
            <h3>{docName}</h3>
            <span>Page {pageNumber}</span>
          </div>
          <button
            className="modal-close"
            onClick={onClose}
            id="page-modal-close"
            aria-label="Close modal"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imageUrl}
            alt={`${docName} — Page ${pageNumber}`}
            id="page-modal-image"
          />
        </div>
      </div>
    </div>
  );
}
