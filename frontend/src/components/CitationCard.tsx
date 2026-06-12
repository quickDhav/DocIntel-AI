'use client';

/* ============================================================
   DocIntel AI — Citation Card Component
   ============================================================ */

import { Citation } from '@/lib/types';
import { getPageImageUrl } from '@/lib/api';

interface Props {
  citation: Citation;
  onClick: () => void;
}

export default function CitationCard({ citation, onClick }: Props) {
  const thumbUrl = getPageImageUrl(
    citation.document_id,
    citation.page_number,
    'thumbnail'
  );

  return (
    <button
      className="citation-card"
      onClick={onClick}
      id={`citation-${citation.document_id}-p${citation.page_number}`}
      title={`${citation.document_name} — Page ${citation.page_number}`}
    >
      <div className="citation-card-thumb">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={thumbUrl}
          alt={`Page ${citation.page_number} of ${citation.document_name}`}
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.style.display = 'none';
          }}
        />
        {/* Fallback icon if image fails */}
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ color: 'var(--text-muted)', position: 'absolute' }}
        >
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
      </div>
      <div className="citation-card-info">
        <div className="citation-card-name">{citation.document_name}</div>
        <div className="citation-card-page">Page {citation.page_number}</div>
      </div>
    </button>
  );
}
