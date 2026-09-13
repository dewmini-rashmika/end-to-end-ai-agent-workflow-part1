"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, RefreshCw, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TripResult } from "@/components/trip/TripResult";
import { AgentTimeline } from "@/components/trip/AgentTimeline";
import { ErrorAlert } from "@/components/shared/ErrorAlert";
import { Skeleton } from "@/components/ui/skeleton";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { useTripStore } from "@/store/trip-store";
import { getSessionTrips } from "@/lib/api";

export default function TripDetailPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const sessionId = params.sessionId;

  const { currentPlan, setCurrentPlan, status, agentSteps, error, clearError } =
    useTripStore();

  const isPlanning = status === "connecting" || status === "planning";

  // If the store has no plan (e.g., hard navigation / refresh), fetch from API
  useEffect(() => {
    if (!currentPlan && sessionId && !isPlanning) {
      getSessionTrips(sessionId, 1)
        .then((plans) => {
          if (plans.length > 0) setCurrentPlan(plans[0]);
        })
        .catch(() => {
          // silently fail — user will see the empty state
        });
    }
  }, [currentPlan, sessionId, isPlanning, setCurrentPlan]);

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />

      <main className="flex-1 bg-background">
        <div className="container mx-auto max-w-5xl px-4 py-8">
          {/* Back + actions */}
          <div className="mb-6 flex items-center justify-between gap-4">
            <Link
              href="/"
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              New trip
            </Link>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push("/")}
            >
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
              Plan another
            </Button>
          </div>

          {/* Active planning state */}
          {isPlanning && (
            <div className="mb-6 rounded-xl border bg-card p-6">
              <AgentTimeline steps={agentSteps} />
            </div>
          )}

          {/* Error */}
          {error && (
            <ErrorAlert
              className="mb-6"
              message={error}
              onDismiss={clearError}
            />
          )}

          {/* Loading skeleton while fetching from API */}
          {!currentPlan && !isPlanning && !error && (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full rounded-xl" />
              <div className="grid grid-cols-3 gap-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-48 w-full rounded-xl" />
                <Skeleton className="h-48 w-full rounded-xl" />
              </div>
            </div>
          )}

          {/* Trip result */}
          {currentPlan && <TripResult plan={currentPlan} />}
        </div>
      </main>

      <Footer />
    </div>
  );
}
