'use client';

/* ============================================================
   DocIntel AI — Voice Button Component
   ============================================================ */

interface Props {
  isListening: boolean;
  isSupported: boolean;
  onToggle: () => void;
  transcript: string;
}

export default function VoiceButton({
  isListening,
  isSupported,
  onToggle,
  transcript,
}: Props) {
  if (!isSupported) {
    return (
      <button
        className="voice-btn"
        id="voice-btn"
        disabled
        title="Voice input not supported in this browser"
        style={{ opacity: 0.3, cursor: 'not-allowed' }}
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
          <line x1="1" y1="1" x2="23" y2="23" />
          <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
          <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .76-.13 1.49-.35 2.17" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
      </button>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      {/* Live transcript popup */}
      {isListening && transcript && (
        <div className="voice-transcript-popup" id="voice-transcript">
          {transcript}
        </div>
      )}

      <button
        className={`voice-btn${isListening ? ' listening' : ''}`}
        id="voice-btn"
        onClick={onToggle}
        title={isListening ? 'Stop recording' : 'Start voice input'}
        aria-label={isListening ? 'Stop recording' : 'Start voice input'}
      >
        {isListening && <span className="voice-btn-dot" />}
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
          <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="23" />
          <line x1="8" y1="23" x2="16" y2="23" />
        </svg>
      </button>
    </div>
  );
}
