/**
 * Zustand store for global trip planning state.
 *
 * Manages:
 *  - Current session ID (persisted to sessionStorage)
 *  - Planning status and agent progress
 *  - The current TripPlan result
 *  - History list
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  TripPlan,
  AgentStep,
  PlanningStatus,
  AgentName,
  ConversationSummary,
} from "@/types";
import { AGENT_ORDER, AGENT_LABELS } from "@/types";

interface TripStore {
  // Session
  sessionId: string | null;
  setSessionId: (id: string) => void;
  clearSession: () => void;

  // Planning lifecycle
  status: PlanningStatus;
  setStatus: (s: PlanningStatus) => void;

  // Agent progress steps
  agentSteps: AgentStep[];
  initAgentSteps: () => void;
  markAgentRunning: (name: AgentName) => void;
  markAgentComplete: (name: AgentName, preview?: string) => void;
  markAgentError: (name: AgentName, preview?: string) => void;

  // Current result
  currentPlan: TripPlan | null;
  setCurrentPlan: (plan: TripPlan) => void;
  clearCurrentPlan: () => void;

  // Error
  error: string | null;
  setError: (msg: string) => void;
  clearError: () => void;

  // History
  history: ConversationSummary[];
  setHistory: (h: ConversationSummary[]) => void;

  // User query (carry across views)
  lastQuery: string;
  setLastQuery: (q: string) => void;
}

const buildInitialSteps = (): AgentStep[] =>
  AGENT_ORDER.map((name) => ({
    name,
    label: AGENT_LABELS[name],
    status: "waiting",
  }));

export const useTripStore = create<TripStore>()(
  persist(
    (set, get) => ({
      // Session
      sessionId: null,
      setSessionId: (id) => set({ sessionId: id }),
      clearSession: () =>
        set({
          sessionId: null,
          currentPlan: null,
          agentSteps: buildInitialSteps(),
          status: "idle",
          error: null,
          lastQuery: "",
        }),

      // Status
      status: "idle",
      setStatus: (s) => set({ status: s }),

      // Agent steps
      agentSteps: buildInitialSteps(),
      initAgentSteps: () => set({ agentSteps: buildInitialSteps() }),
      markAgentRunning: (name) =>
        set((state) => ({
          agentSteps: state.agentSteps.map((s) =>
            s.name === name
              ? { ...s, status: "running", startedAt: Date.now() }
              : s
          ),
        })),
      markAgentComplete: (name, preview) =>
        set((state) => ({
          agentSteps: state.agentSteps.map((s) =>
            s.name === name
              ? {
                  ...s,
                  status: "completed",
                  completedAt: Date.now(),
                  preview: preview ?? s.preview,
                }
              : s
          ),
        })),
      markAgentError: (name, preview) =>
        set((state) => ({
          agentSteps: state.agentSteps.map((s) =>
            s.name === name
              ? { ...s, status: "error", preview: preview ?? s.preview }
              : s
          ),
        })),

      // Plan
      currentPlan: null,
      setCurrentPlan: (plan) => set({ currentPlan: plan }),
      clearCurrentPlan: () => set({ currentPlan: null }),

      // Error
      error: null,
      setError: (msg) => set({ error: msg }),
      clearError: () => set({ error: null }),

      // History
      history: [],
      setHistory: (h) => set({ history: h }),

      // Query
      lastQuery: "",
      setLastQuery: (q) => set({ lastQuery: q }),
    }),
    {
      name: "tripmate-store",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? sessionStorage : (null as never)
      ),
      // Only persist session identity and history — not transient UI state
      partialize: (state) => ({
        sessionId: state.sessionId,
        lastQuery: state.lastQuery,
        history: state.history,
      }),
    }
  )
);
