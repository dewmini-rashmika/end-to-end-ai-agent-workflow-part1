"use client";

import { Plane, Zap, Shield, Globe } from "lucide-react";
import { TripForm } from "@/components/trip/TripForm";
import { AgentTimeline } from "@/components/trip/AgentTimeline";
import { ErrorAlert } from "@/components/shared/ErrorAlert";
import { useTripStore } from "@/store/trip-store";

const FEATURES = [
  {
    icon: Plane,
    title: "Real Flight Data",
    description: "Live flight search via AviationStack with Tavily fallback for global coverage.",
  },
  {
    icon: Globe,
    title: "Hotel Recommendations",
    description: "Google Places + curated web search finds hotels matching your budget tier.",
  },
  {
    icon: Zap,
    title: "Day-by-Day Itinerary",
    description: "A dedicated agent crafts your complete daily schedule with local insights.",
  },
  {
    icon: Shield,
    title: "Persistent Memory",
    description: "PostgreSQL checkpointing remembers your trips. Ask follow-up questions anytime.",
  },
];

export default function HomePage() {
  const { status, agentSteps, error, clearError } = useTripStore();

  const isPlanning = status === "connecting" || status === "planning";
  const showTimeline = isPlanning || status === "completed";

  return (
    <div className="flex flex-col">
      {/* ─── Hero Section ─── */}
      <section className="hero-gradient px-4 py-16 sm:py-24">
        <div className="container mx-auto max-w-4xl">
          {/* Badge */}
          <div className="mb-6 flex justify-center">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-400/30 bg-blue-500/20 px-3 py-1 text-xs font-medium text-blue-200">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-300" />
              </span>
              Powered by LangGraph Multi-Agent AI
            </span>
          </div>

          {/* Headline */}
          <h1 className="mb-4 text-center text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Plan Your Perfect Trip
            <span className="block text-blue-300">in Seconds</span>
          </h1>
          <p className="mx-auto mb-10 max-w-2xl text-center text-base text-blue-100/80 sm:text-lg">
            Tell us where you want to go. Our AI agents search flights, curate hotels,
            and craft a personalised day-by-day itinerary — all from one sentence.
          </p>

          {/* Form Card */}
          <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 sm:p-8">
            <TripForm />
          </div>

          {/* Agent Timeline — visible while planning */}
          {showTimeline && (
            <div className="mt-6 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-5">
              <AgentTimeline steps={agentSteps} />
              {status === "completed" && (
                <div className="mt-6 flex justify-center">
                  <a
                    href={`/trip/${useTripStore.getState().sessionId}`}
                    className="inline-flex h-10 items-center justify-center rounded-md bg-blue-600 px-8 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-blue-600/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
                  >
                    See the Plan
                  </a>
                </div>
              )}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4">
              <ErrorAlert
                message={error}
                onDismiss={clearError}
              />
            </div>
          )}
        </div>
      </section>

      {/* ─── Features Section ─── */}
      <section className="px-4 py-16 bg-background">
        <div className="container mx-auto max-w-5xl">
          <div className="mb-10 text-center">
            <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
              Four Specialist Agents, One Seamless Plan
            </h2>
            <p className="mt-2 text-muted-foreground">
              Each agent is an expert in its domain — they collaborate through a shared LangGraph state.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="group rounded-xl border p-5 transition-shadow hover:shadow-md"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 group-hover:bg-blue-100 transition-colors">
                  <feature.icon className="h-5 w-5 text-blue-600" />
                </div>
                <h3 className="mb-1.5 text-sm font-semibold">{feature.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>

          {/* Pipeline diagram */}
          <div className="mt-12 rounded-xl border bg-muted/30 p-6">
            <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground text-center">
              Agent Pipeline
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {[
                { label: "Parse Query", color: "bg-blue-100 text-blue-800" },
                { label: "→", color: "text-muted-foreground" },
                { label: "Flight Search", color: "bg-sky-100 text-sky-800" },
                { label: "→", color: "text-muted-foreground" },
                { label: "Hotel Search", color: "bg-amber-100 text-amber-800" },
                { label: "→", color: "text-muted-foreground" },
                { label: "Itinerary", color: "bg-emerald-100 text-emerald-800" },
                { label: "→", color: "text-muted-foreground" },
                { label: "Final Plan", color: "bg-purple-100 text-purple-800" },
              ].map((step, i) =>
                step.label === "→" ? (
                  <span key={i} className="text-lg text-muted-foreground">
                    →
                  </span>
                ) : (
                  <span
                    key={i}
                    className={`rounded-full px-3 py-1 text-xs font-medium ${step.color}`}
                  >
                    {step.label}
                  </span>
                )
              )}
            </div>
            <p className="mt-3 text-center text-xs text-muted-foreground">
              All agents share a single <code className="font-mono text-xs bg-muted px-1 py-0.5 rounded">TravelState</code> — persisted via PostgreSQL checkpointing
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
