'use client';

/* ============================================================
   DocIntel AI — Chat Page
   ============================================================ */

import { useChat } from '@/hooks/useChat';
import { useVoice } from '@/hooks/useVoice';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';

const SUGGESTIONS = [
  'Summarize the uploaded documents',
  'What are the key findings?',
  'Find tables related to revenue',
  'Compare the documents',
  'Extract dates and deadlines',
];

export default function ChatPage() {
  const {
    messages,
    isLoading,
    sendMessage,
    clearHistory,
    bottomRef,
  } = useChat();

  const {
    isListening,
    transcript,
    isSupported,
    toggleListening,
    clearTranscript,
  } = useVoice();

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  return (
    <div className="chat-page" id="chat-page">
      {/* Messages Area */}
      <div className="chat-messages" id="chat-messages">
        <div className="chat-messages-inner">
          {messages.length === 0 && !isLoading ? (
            /* Welcome Screen */
            <div className="chat-welcome" id="chat-welcome">
              <div className="chat-welcome-icon">
                <svg
                  width="36"
                  height="36"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--accent-cyan)"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  <path d="M12 7v2" />
                  <path d="M12 13h.01" />
                </svg>
              </div>
              <h2 className="text-gradient">Welcome to DocIntel AI</h2>
              <p>
                Upload your documents and ask questions. I&apos;ll analyze them
                using advanced AI to give you accurate, cited answers.
              </p>

              {/* Suggestion Pills */}
              <div className="chat-suggestions">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    className="chat-suggestion"
                    onClick={() => handleSuggestionClick(s)}
                    id={`suggestion-${s.slice(0, 20).replace(/\s/g, '-').toLowerCase()}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Message List */
            <>
              {/* Clear history button */}
              {messages.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '8px' }}>
                  <button
                    className="btn-secondary"
                    onClick={clearHistory}
                    id="clear-history-btn"
                    style={{ fontSize: '0.75rem', padding: '6px 16px' }}
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                    Clear History
                  </button>
                </div>
              )}

              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="message message-assistant">
                  <div className="message-avatar">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z" />
                      <path d="M6 10a6 6 0 0 0 12 0" />
                      <path d="M12 16v6" />
                      <path d="M8 22h8" />
                    </svg>
                  </div>
                  <div className="message-content">
                    <div className="message-bubble" style={{ borderTopLeftRadius: 'var(--radius-xs)' }}>
                      <div className="loading-dots" id="loading-dots">
                        <div className="loading-dot" />
                        <div className="loading-dot" />
                        <div className="loading-dot" />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Auto-scroll anchor */}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input Area */}
      <ChatInput
        onSend={sendMessage}
        disabled={isLoading}
        isListening={isListening}
        isVoiceSupported={isSupported}
        voiceTranscript={transcript}
        onVoiceToggle={toggleListening}
        onClearTranscript={clearTranscript}
      />
    </div>
  );
}
