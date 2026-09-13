"use client";

import { useEffect, useState, useCallback } from "react";
import { getSessionHistory } from "@/lib/api";
import { useTripStore } from "@/store/trip-store";
import type { ConversationSummary } from "@/types";

/**
 * Fetches the conversation history for the given sessionId.
 * Also syncs results into the Zustand store.
 *
 * @param sessionId - Pass the session ID directly, or omit to read from store.
 */
export function useSessionHistory(sessionId?: string) {
  const { sessionId: storeSessionId, history, setHistory } = useTripStore();
  const effectiveSessionId = sessionId ?? storeSessionId ?? "";

  const [conversations, setConversations] = useState<ConversationSummary[]>(history);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!effectiveSessionId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await getSessionHistory(effectiveSessionId);
      setConversations(data);
      setHistory(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setIsLoading(false);
    }
  }, [effectiveSessionId, setHistory]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return {
    conversations,
    /** @deprecated use conversations */
    history: conversations,
    isLoading,
    /** @deprecated use isLoading */
    loading: isLoading,
    error,
    refresh: fetch,
  };
}
