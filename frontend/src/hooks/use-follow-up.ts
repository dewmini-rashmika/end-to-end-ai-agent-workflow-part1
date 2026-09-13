"use client";

import { useState, useCallback } from "react";
import { followUp } from "@/lib/api";
import { useTripStore } from "@/store/trip-store";

export function useFollowUp() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { sessionId, setCurrentPlan } = useTripStore();

  const send = useCallback(
    async (message: string) => {
      if (!sessionId) {
        setError("No active session. Please start a new trip plan.");
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const plan = await followUp(sessionId, { message });
        setCurrentPlan(plan);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, setCurrentPlan]
  );

  return { send, loading, error };
}
