/**
 * useTripPlanner hook
 *
 * Orchestrates the SSE streaming trip planning flow:
 *   1. Generate / reuse session ID
 *   2. Open SSE stream via `streamTripPlan`
 *   3. Drive Zustand store updates as each agent completes
 *   4. Navigate to the result page when done
 */

"use client";

import { useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { streamTripPlan } from "@/lib/api";
import { useTripStore } from "@/store/trip-store";
import { uuid } from "@/lib/utils";
import type { PlanTripRequest } from "@/types";
import { AGENT_ORDER } from "@/types";

export function useTripPlanner() {
  const router = useRouter();
  const abortRef = useRef<(() => void) | null>(null);

  const {
    setSessionId,
    setStatus,
    initAgentSteps,
    markAgentRunning,
    markAgentComplete,
    markAgentError,
    setCurrentPlan,
    setError,
    clearError,
    setLastQuery,
    status,
  } = useTripStore();

  const plan = useCallback(
    (request: PlanTripRequest) => {
      // Abort any in-flight request
      abortRef.current?.();

      const sessionId = request.session_id ?? uuid();
      setSessionId(sessionId);
      setLastQuery(request.user_query);
      initAgentSteps();
      clearError();
      setStatus("connecting");

      const abort = streamTripPlan(
        { ...request, session_id: sessionId },
        {
          onStart(data) {
            setStatus("planning");
            // Mark first agent as running
            if (data.agents?.[0]) {
              markAgentRunning(data.agents[0]);
            }
          },

          onAgentUpdate(data) {
            markAgentComplete(data.agent, data.preview);

            // Mark next agent as running
            const idx = AGENT_ORDER.indexOf(data.agent);
            if (idx >= 0 && idx < AGENT_ORDER.length - 1) {
              markAgentRunning(AGENT_ORDER[idx + 1]);
            }

            if (data.errors?.length) {
              data.errors.forEach((e: string) =>
                markAgentError(data.agent, e)
              );
            }
          },

          onDone(plan) {
            setCurrentPlan(plan);
            setStatus("completed");
            router.push(`/trip/${sessionId}`);
          },

          onError(msg) {
            setError(msg);
            setStatus("error");
          },
        }
      );

      abortRef.current = abort;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const cancel = useCallback(() => {
    abortRef.current?.();
    setStatus("idle");
  }, [setStatus]);

  return { plan, cancel, status };
}
