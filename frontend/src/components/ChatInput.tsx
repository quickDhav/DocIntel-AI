'use client';

/* ============================================================
   DocIntel AI — Chat Input Component
   ============================================================ */

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import VoiceButton from './VoiceButton';

interface Props {
  onSend: (message: string) => void;
  disabled: boolean;
  isListening: boolean;
  isVoiceSupported: boolean;
  voiceTranscript: string;
  onVoiceToggle: () => void;
  onClearTranscript: () => void;
}

export default function ChatInput({
  onSend,
  disabled,
  isListening,
  isVoiceSupported,
  voiceTranscript,
  onVoiceToggle,
  onClearTranscript,
}: Props) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (voiceTranscript && !isListening) {
      setText((prev) => {
        const newText = prev ? `${prev} ${voiceTranscript}` : voiceTranscript;
        return newText;
      });
      onClearTranscript();
      textareaRef.current?.focus();
    }
  }, [voiceTranscript, isListening, onClearTranscript]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-area">
      <div className="chat-input-container" id="chat-input-container">
        {/* Voice Button */}
        <VoiceButton
          isListening={isListening}
          isSupported={isVoiceSupported}
          onToggle={onVoiceToggle}
          transcript={voiceTranscript}
        />

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          id="chat-textarea"
          placeholder="Ask about your documents..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
        />

        {/* Send Button */}
        <button
          className="chat-send-btn"
          id="chat-send-btn"
          onClick={handleSend}
          disabled={!text.trim() || disabled}
          title="Send message"
          aria-label="Send message"
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
