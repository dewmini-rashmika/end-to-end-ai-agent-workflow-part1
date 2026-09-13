"use client";

import { CheckCircle2, Circle, Loader2, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatElapsed } from "@/lib/utils";
import type { AgentStep } from "@/types";

interface AgentTimelineProps {
  steps: AgentStep[];
  className?: string;
}

function StepIcon({ status }: { status: AgentStep["status"] }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
    case "running":
      return <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />;
    case "error":
      return <XCircle className="h-5 w-5 text-destructive" />;
    default:
      return <Circle className="h-5 w-5 text-muted-foreground/40" />;
  }
}

function StepBadge({ status }: { status: AgentStep["status"] }) {
  const map: Record<AgentStep["status"], { label: string; className: string }> = {
    waiting: { label: "Waiting", className: "text-muted-foreground/50" },
    running: { label: "Running", className: "text-blue-400 animate-pulse" },
    completed: { label: "Done", className: "text-emerald-500" },
    error: { label: "Error", className: "text-destructive" },
  };
  const { label, className } = map[status];
  return <span className={cn("text-xs font-medium", className)}>{label}</span>;
}

export function AgentTimeline({ steps, className }: AgentTimelineProps) {
  return (
    <div className={cn("space-y-1", className)}>
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
        Agent Progress
      </p>
      <ol className="space-y-0">
        {steps.map((step, idx) => {
          const elapsed =
            step.completedAt && step.startedAt
              ? step.completedAt - step.startedAt
              : step.startedAt && step.status === "running"
              ? Date.now() - step.startedAt
              : null;

          const isLast = idx === steps.length - 1;

          return (
            <li key={step.name} className="relative flex gap-3">
              {/* Connector line */}
              {!isLast && (
                <div
                  className={cn(
                    "absolute left-[9px] top-5 h-full w-0.5",
                    step.status === "completed"
                      ? "bg-emerald-500/40"
                      : "bg-border"
                  )}
                />
              )}

              {/* Icon */}
              <div className="relative z-10 flex h-5 w-5 shrink-0 items-center justify-center mt-1.5">
                <StepIcon status={step.status} />
              </div>

              {/* Content */}
              <div
                className={cn(
                  "flex-1 pb-5 min-w-0",
                  step.status === "waiting" && "opacity-40"
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <p
                    className={cn(
                      "text-sm font-medium leading-tight",
                      step.status === "running" && "text-blue-400",
                      step.status === "completed" && "text-foreground",
                      step.status === "error" && "text-destructive"
                    )}
                  >
                    {step.label}
                  </p>
                  <div className="flex items-center gap-2 shrink-0">
                    {elapsed !== null && (
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {formatElapsed(elapsed)}
                      </span>
                    )}
                    <StepBadge status={step.status} />
                  </div>
                </div>
                {step.preview && (
                  <p className="mt-0.5 text-xs text-muted-foreground truncate">
                    {step.preview}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
