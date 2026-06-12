'use client';

/* ============================================================
   DocIntel AI — Chat Message Component
   ============================================================ */

import { ChatMessage as ChatMessageType } from '@/lib/types';
import CitationCard from './CitationCard';
import { useState } from 'react';
import PageModal from './PageModal';

interface Props {
  message: ChatMessageType;
}

/**
 * Simple markdown-like formatting:
 * - **bold** → <strong>
 * - `code` → <code>
 * - Line breaks → <br>
 * - Paragraphs (double newline)
 * - Bullet lists (lines starting with - or *)
 */
function formatContent(content: string): string {
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  html = html.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');

  const paragraphs = html.split(/\n\n+/);

  html = paragraphs
    .map((p) => {
      const trimmed = p.trim();
      if (!trimmed) return '';

      const lines = trimmed.split('\n');
      const isListBlock = lines.every(
        (l) => l.trim().startsWith('- ') || l.trim().startsWith('* ') || l.trim() === ''
      );

      if (isListBlock && lines.some((l) => l.trim().startsWith('- ') || l.trim().startsWith('* '))) {
        const items = lines
          .filter((l) => l.trim().startsWith('- ') || l.trim().startsWith('* '))
          .map((l) => `<li>${l.trim().substring(2)}</li>`)
          .join('');
        return `<ul>${items}</ul>`;
      }

      const isNumberedList = lines.every(
        (l) => /^\d+\.\s/.test(l.trim()) || l.trim() === ''
      );
      if (isNumberedList && lines.some((l) => /^\d+\.\s/.test(l.trim()))) {
        const items = lines
          .filter((l) => /^\d+\.\s/.test(l.trim()))
          .map((l) => `<li>${l.trim().replace(/^\d+\.\s/, '')}</li>`)
          .join('');
        return `<ol>${items}</ol>`;
      }

      if (trimmed.startsWith('<pre>')) return trimmed;

      return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
    })
    .join('');

  return html;
}

function formatTimestamp(iso: string): string {
  try {
    const date = new Date(iso);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

export default function ChatMessage({ message }: Props) {
  const [modalCitation, setModalCitation] = useState<{
    docId: string;
    pageNumber: number;
    docName: string;
  } | null>(null);

  const isUser = message.role === 'user';

  return (
    <>
      <div
        className={`message ${isUser ? 'message-user' : 'message-assistant'}`}
        id={`message-${message.id}`}
      >
        {/* Avatar */}
        <div className="message-avatar">
          {isUser ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z" />
              <path d="M6 10a6 6 0 0 0 12 0" />
              <path d="M12 16v6" />
              <path d="M8 22h8" />
            </svg>
          )}
        </div>

        {/* Content */}
        <div className="message-content">
          <div
            className="message-bubble"
            dangerouslySetInnerHTML={{
              __html: isUser ? message.content : formatContent(message.content),
            }}
          />

          {/* Citations */}
          {message.citations && message.citations.length > 0 && (
            <div className="message-citations">
              {message.citations.map((citation, idx) => (
                <CitationCard
                  key={`${citation.document_id}-${citation.page_number}-${idx}`}
                  citation={citation}
                  onClick={() =>
                    setModalCitation({
                      docId: citation.document_id,
                      pageNumber: citation.page_number,
                      docName: citation.document_name,
                    })
                  }
                />
              ))}
            </div>
          )}

          <div className="message-timestamp">
            {formatTimestamp(message.timestamp)}
          </div>
        </div>
      </div>

      {/* Page Modal */}
      {modalCitation && (
        <PageModal
          isOpen={true}
          onClose={() => setModalCitation(null)}
          docId={modalCitation.docId}
          pageNumber={modalCitation.pageNumber}
          docName={modalCitation.docName}
        />
      )}
    </>
  );
}
