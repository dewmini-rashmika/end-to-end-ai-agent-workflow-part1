/**
 * TripMate AI — typed API client
 *
 * All HTTP calls to the FastAPI backend go through here.
 * SSE streaming is handled by `streamTripPlan`.
 */

import type {
  TripPlan,
  PlanTripRequest,
  FollowUpRequest,
  ConversationSummary,
  AgentUpdateEvent,
  SSEStartEvent,
  SSEEventType,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API = `${BASE}/api/v1`;

// ---------------------------------------------------------------------------
// Generic fetch wrapper
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...init.headers,
    },
    ...init,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body.detail ?? body.error ?? message;
    } catch {
      /* ignore parse error */
    }
    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Trip endpoints
// ---------------------------------------------------------------------------

/** POST /api/v1/trips/plan — standard JSON response */
export async function planTrip(body: PlanTripRequest): Promise<TripPlan> {
  return apiFetch<TripPlan>("/trips/plan", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** POST /api/v1/trips/{sessionId}/followup */
export async function followUp(
  sessionId: string,
  body: FollowUpRequest
): Promise<TripPlan> {
  return apiFetch<TripPlan>(`/trips/${sessionId}/followup`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** GET /api/v1/trips/{sessionId} */
export async function getSessionTrips(
  sessionId: string,
  limit = 10
): Promise<TripPlan[]> {
  return apiFetch<TripPlan[]>(`/trips/${sessionId}?limit=${limit}`);
}

// ---------------------------------------------------------------------------
// Session endpoints
// ---------------------------------------------------------------------------

/** GET /api/v1/sessions/{sessionId}/history */
export async function getSessionHistory(
  sessionId: string,
  limit = 20
): Promise<ConversationSummary[]> {
  return apiFetch<ConversationSummary[]>(
    `/sessions/${sessionId}/history?limit=${limit}`
  );
}

/** GET /api/v1/sessions/{sessionId}/preferences */
export async function getPreferences(sessionId: string): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/sessions/${sessionId}/preferences`
  );
}

/** PUT /api/v1/sessions/{sessionId}/preferences */
export async function savePreferences(
  sessionId: string,
  preferences: Record<string, unknown>
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(
    `/sessions/${sessionId}/preferences`,
    {
      method: "PUT",
      body: JSON.stringify({ preferences }),
    }
  );
}

// ---------------------------------------------------------------------------
// SSE Streaming
// ---------------------------------------------------------------------------

export interface StreamCallbacks {
  onStart?: (data: SSEStartEvent) => void;
  onAgentUpdate?: (data: AgentUpdateEvent) => void;
  onDone?: (data: TripPlan) => void;
  onError?: (message: string) => void;
}

/**
 * POST /api/v1/trips/plan/stream
 *
 * Opens a Server-Sent Events connection and calls the appropriate callback
 * for each event type. Returns a cleanup function to abort the request.
 */
export function streamTripPlan(
  body: PlanTripRequest,
  callbacks: StreamCallbacks
): () => void {
  const controller = new AbortController();

  (async () => {
    let res: Response;
    try {
      res = await fetch(`${API}/trips/plan/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
    } catch (err) {
      if (controller.signal.aborted) return;
      callbacks.onError?.((err as Error).message);
      return;
    }

    if (!res.ok || !res.body) {
      callbacks.onError?.(`HTTP ${res.status}`);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE messages are separated by double newlines
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        if (!part.trim()) continue;

        let eventType: SSEEventType = "agent_update";
        let dataLine = "";

        for (const line of part.split("\n")) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim() as SSEEventType;
          } else if (line.startsWith("data: ")) {
            dataLine = line.slice(6).trim();
          }
        }

        if (!dataLine) continue;

        try {
          const parsed = JSON.parse(dataLine);
          if (eventType === "start") callbacks.onStart?.(parsed as SSEStartEvent);
          else if (eventType === "agent_update") callbacks.onAgentUpdate?.(parsed as AgentUpdateEvent);
          else if (eventType === "done") callbacks.onDone?.(parsed as TripPlan);
          else if (eventType === "error") callbacks.onError?.(parsed.message ?? "Unknown error");
        } catch {
          // Malformed JSON — skip
        }
      }
    }
  })();

  return () => controller.abort();
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}
