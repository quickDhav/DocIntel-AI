'use client';

/* ============================================================
   DocIntel AI — Chat State Management Hook
   ============================================================ */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ChatMessage } from '@/lib/types';
import {
  sendMessage as apiSendMessage,
  getChatHistory,
  clearChatHistory as apiClearHistory,
  getOrCreateSessionId,
} from '@/lib/api';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const id = getOrCreateSessionId();
    setSessionId(id);
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    const loadHistory = async () => {
      try {
        const history = await getChatHistory(sessionId);
        setMessages(history);
      } catch {
      }
    };

    loadHistory();
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || !sessionId || isLoading) return;

      setError(null);

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: text.trim(),
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const response = await apiSendMessage(text.trim(), sessionId);
        setMessages((prev) => [...prev, response]);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);

        const errorResponse: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `I'm sorry, I encountered an error: ${errorMessage}. Please try again.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorResponse]);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading]
  );

  const clearHistory = useCallback(async () => {
    if (!sessionId) return;

    try {
      await apiClearHistory(sessionId);
      setMessages([]);
      setError(null);
    } catch {
      setError('Failed to clear history');
    }
  }, [sessionId]);

  return {
    messages,
    isLoading,
    sessionId,
    error,
    sendMessage,
    clearHistory,
    bottomRef,
  };
}
