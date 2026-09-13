"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  CalendarClock,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Search,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { ErrorAlert } from "@/components/shared/ErrorAlert";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { useSessionHistory } from "@/hooks/use-session-history";
import { useTripStore } from "@/store/trip-store";
import { getSessionTrips } from "@/lib/api";
import type { ConversationSummary } from "@/types";

function StatusIcon({ status }: { status: ConversationSummary["status"] }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />;
    case "error":
      return <XCircle className="h-4 w-4 text-destructive shrink-0" />;
    default:
      return <Loader2 className="h-4 w-4 text-muted-foreground shrink-0 animate-spin" />;
  }
}

function StatusBadge({ status }: { status: ConversationSummary["status"] }) {
  const map = {
    completed: { label: "Completed", variant: "success" as const },
    error: { label: "Error", variant: "destructive" as const },
    pending: { label: "Pending", variant: "secondary" as const },
  };
  const { label, variant } = map[status] ?? map.pending;
  return <Badge variant={variant as any} className="text-xs">{label}</Badge>;
}

function formatRelativeTime(dateStr: string): string {
  const d = new Date(dateStr);
  const diff = Date.now() - d.getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function HistoryPage() {
  const router = useRouter();
  const { sessionId, setCurrentPlan } = useTripStore();
  const { conversations, isLoading, error, refresh } = useSessionHistory(sessionId ?? "");

  async function openTrip(conv: ConversationSummary) {
    try {
      const plans = await getSessionTrips(conv.session_id, 1);
      if (plans.length > 0) {
        setCurrentPlan(plans[0]);
        router.push(`/trip/${conv.session_id}`);
      }
    } catch {
      // fall through — detail page will fetch itself
      router.push(`/trip/${conv.session_id}`);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="flex-1 bg-background">
        <div className="container mx-auto max-w-3xl px-4 py-8">
          {/* Header */}
          <div className="mb-8 flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold">Trip History</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                {sessionId
                  ? `Session: ${sessionId.slice(0, 8)}…`
                  : "No active session"}
              </p>
            </div>
            <Button onClick={() => router.push("/")} size="sm">
              <Search className="mr-1.5 h-3.5 w-3.5" />
              New Trip
            </Button>
          </div>

          {/* Error */}
          {error && (
            <ErrorAlert
              className="mb-6"
              message={error}
              title="Could not load history"
            />
          )}

          {/* No session */}
          {!sessionId && !isLoading && (
            <div className="flex flex-col items-center gap-4 py-16 text-muted-foreground">
              <CalendarClock className="h-12 w-12 opacity-20" />
              <p className="text-sm">Plan a trip first to see your history here.</p>
              <Button variant="outline" onClick={() => router.push("/")}>
                Plan a trip
              </Button>
            </div>
          )}

          {/* Loading */}
          {isLoading && (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full rounded-xl" />
              ))}
            </div>
          )}

          {/* Empty */}
          {!isLoading && sessionId && conversations.length === 0 && !error && (
            <div className="flex flex-col items-center gap-4 py-16 text-muted-foreground">
              <CalendarClock className="h-12 w-12 opacity-20" />
              <p className="text-sm">No trips found for this session.</p>
              <Button variant="outline" onClick={() => router.push("/")}>
                Plan your first trip
              </Button>
            </div>
          )}

          {/* Conversation list */}
          {!isLoading && conversations.length > 0 && (
            <div className="space-y-3">
              {conversations.map((conv, i) => (
                <div key={conv.id}>
                  <button
                    onClick={() => openTrip(conv)}
                    className="w-full text-left rounded-xl border bg-card p-4 transition-all hover:border-primary/30 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <div className="flex items-start gap-3">
                      <StatusIcon status={conv.status} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-medium truncate">
                            {conv.user_query}
                          </p>
                          <StatusBadge status={conv.status} />
                        </div>
                        <div className="mt-1.5 flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatRelativeTime(conv.created_at)}
                          </span>
                          <span className="truncate">
                            {conv.session_id.slice(0, 8)}…
                          </span>
                        </div>
                      </div>
                      <ArrowLeft className="h-4 w-4 text-muted-foreground rotate-180 shrink-0 mt-0.5" />
                    </div>
                  </button>
                  {i < conversations.length - 1 && (
                    <Separator className="mt-3" />
                  )}
                </div>
              ))}

              <div className="pt-4 text-center">
                <Button variant="ghost" size="sm" onClick={refresh}>
                  Refresh
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
