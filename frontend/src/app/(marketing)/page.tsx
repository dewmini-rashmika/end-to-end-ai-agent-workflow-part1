"use client";

import Image from "next/image";
import { Sparkles, Plane, BookOpen, Heart, HelpCircle, ArrowRight, Loader2, MapPin, Calendar } from "lucide-react";
import { TripForm } from "@/components/trip/TripForm";
import { AgentTimeline } from "@/components/trip/AgentTimeline";
import { ErrorAlert } from "@/components/shared/ErrorAlert";
import { Navbar } from "@/components/layout/Navbar";
import { useTripStore } from "@/store/trip-store";

const FEATURES = [
  {
    icon: Sparkles,
    gradient: "from-purple-500 to-indigo-600",
    shadow: "shadow-purple-500/30",
    title: "AI Powered Plans",
    description: "Smart itineraries tailored to your interests",
  },
  {
    icon: Plane,
    gradient: "from-teal-400 to-cyan-500",
    shadow: "shadow-teal-400/30",
    title: "Best Flights & Hotels",
    description: "Find the best deals across top providers",
  },
  {
    icon: BookOpen,
    gradient: "from-amber-400 to-orange-500",
    shadow: "shadow-amber-400/30",
    title: "Day-by-Day Itineraries",
    description: "Explore, eat, and experience like a local",
  },
  {
    icon: Heart,
    gradient: "from-pink-500 to-rose-500",
    shadow: "shadow-pink-500/30",
    title: "Personalised for You",
    description: "Your style. Your budget. Your trip.",
  },
];

const DESTINATIONS = [
  { src: "/images/dest-tokyo.png", label: "Tokyo, Japan" },
  { src: "/images/dest-maldives.png", label: "Maldives" },
  { src: "/images/dest-santorini.png", label: "Santorini, Greece" },
  { src: "/images/dest-bali.png", label: "Bali, Indonesia" },
];

export default function HomePage() {
  const { status, agentSteps, error, clearError, sessionId } = useTripStore();

  const isPlanning = status === "connecting" || status === "planning";
  const isCompleted = status === "completed";
  const showTimeline = isPlanning || isCompleted;

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative min-h-screen overflow-hidden">
        {/* Background image */}
        <Image
          src="/images/hero-bg.jpg"
          alt="Traveler overlooking scenic landscape"
          fill
          priority
          className="object-cover object-center"
        />

        {/* Gradient overlay — darkens bottom so text/form readable */}
        <div className="absolute inset-0 bg-gradient-to-b from-blue-950/30 via-blue-900/20 to-blue-950/60" />
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/20 to-transparent" />

        {/* Decorative elements */}
        <div className="absolute left-8 top-32 z-10 hidden lg:block -rotate-6">
          <p className="font-pacifico text-3xl text-white/90 drop-shadow-md leading-tight">
            New Places
            <br />
            <span className="ml-4">Bigger Dreams</span>
          </p>
        </div>

        <div className="absolute right-12 top-24 z-10 hidden lg:block w-64 opacity-80">
          <svg viewBox="0 0 200 60" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
            <path
              d="M0,40 Q50,40 100,10 T200,10"
              stroke="white"
              strokeWidth="2"
              strokeDasharray="4 4"
              className="animate-dash"
            />
            <Plane className="h-6 w-6 text-white animate-plane-fly absolute -right-4 -top-2 rotate-45" />
          </svg>
        </div>

        {/* Navbar rendered as overlay */}
        <Navbar />

        {/* Hero content */}
        <div className="relative z-10 flex flex-col items-center px-4 pt-24 pb-16 sm:pt-32">
          {/* Headline */}
          <div className="mb-2 text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl drop-shadow-lg">
              Plan Your{" "}
              <span className="bg-gradient-to-r from-blue-300 via-purple-300 to-pink-300 bg-clip-text text-transparent">
                Perfect Trip
              </span>
              <br />
              in Seconds
            </h1>
            <p className="mx-auto mt-4 max-w-xl text-center text-sm text-white/80 sm:text-base leading-relaxed drop-shadow">
              Tell us where you want to go. Our AI agents search flights, curate hotels,
              and craft a personalised day-by-day itinerary — all from one sentence.
            </p>
          </div>

          {/* White form card */}
          <div className="mt-8 w-full max-w-2xl rounded-2xl bg-white shadow-2xl shadow-blue-900/40 overflow-hidden">
            <TripForm />
          </div>

          {/* Agent Timeline — visible while planning or completed */}
          {showTimeline && (
            <div className="mt-6 w-full max-w-2xl rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md p-5 shadow-xl">
              <AgentTimeline steps={agentSteps} />
              {isCompleted && sessionId && (
                <div className="mt-6 flex justify-center">
                  <a
                    href={`/trip/${sessionId}`}
                    className="inline-flex h-11 items-center gap-2 rounded-full bg-blue-600 px-8 text-sm font-semibold text-white shadow-lg shadow-blue-600/40 transition-all hover:bg-blue-500 hover:shadow-blue-500/40"
                  >
                    See the Plan
                    <ArrowRight className="h-4 w-4" />
                  </a>
                </div>
              )}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-4 w-full max-w-2xl">
              <ErrorAlert message={error} onDismiss={clearError} />
            </div>
          )}

          {/* Features Strip */}
          <div className="mt-16 w-full max-w-5xl">
            <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
              {FEATURES.map((feature) => (
                <div key={feature.title} className="flex flex-col items-center text-center gap-3">
                  <div
                    className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${feature.gradient} shadow-lg ${feature.shadow}`}
                  >
                    <feature.icon className="h-7 w-7 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white drop-shadow-md">{feature.title}</p>
                    <p className="mt-1 text-xs text-blue-100 drop-shadow">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Destinations Gallery */}
          <div className="mt-16 w-full max-w-6xl flex flex-col lg:flex-row items-center justify-center gap-8 pb-12">
            {/* Cards */}
            <div className="flex gap-4 overflow-visible w-full lg:w-auto justify-center">
              {DESTINATIONS.map((dest, i) => (
                <div
                  key={dest.label}
                  className="relative h-48 w-60 shrink-0 overflow-hidden rounded-2xl shadow-2xl border-4 border-white/20"
                  style={{ transform: `rotate(${[-4, 2, -2, 4][i]}deg)` }}
                >
                  <Image
                    src={dest.src}
                    alt={dest.label}
                    fill
                    className="object-cover transition-transform duration-500 hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  <div className="absolute bottom-3 left-3 flex items-center gap-1.5">
                    <div className="flex items-center gap-1 rounded-full bg-black/40 backdrop-blur-sm px-2.5 py-1">
                      <MapPin className="h-3 w-3 text-white" />
                      <span className="text-xs font-medium text-white">{dest.label}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Tagline */}
            <div className="shrink-0 text-center lg:text-right mt-6 lg:mt-0 lg:ml-8 transform rotate-[-5deg]">
              <p className="font-pacifico text-3xl leading-snug text-white drop-shadow-lg">
                Your next
              </p>
              <p className="font-pacifico text-4xl leading-snug text-white drop-shadow-lg">
                adventure starts
              </p>
              <p className="font-pacifico text-3xl leading-snug text-white drop-shadow-lg text-right">
                here 
              </p>
            </div>
          </div>
        </div>

      {/* Decorative Wave Overlay (bottom left) */}
        <div className="absolute bottom-0 left-0 w-1/3 opacity-40 pointer-events-none">
          <svg viewBox="0 0 400 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto">
            <path d="M0 200V100C100 100 150 150 250 120C350 90 400 150 400 150V200H0Z" fill="url(#paint0_linear)" />
            <path d="M0 200V140C80 140 120 170 200 150C280 130 350 170 400 160V200H0Z" fill="url(#paint1_linear)" />
            <defs>
              <linearGradient id="paint0_linear" x1="0" y1="100" x2="400" y2="200" gradientUnits="userSpaceOnUse">
                <stop stopColor="#3b82f6" stopOpacity="0.5" />
                <stop offset="1" stopColor="#1d4ed8" stopOpacity="0.8" />
              </linearGradient>
              <linearGradient id="paint1_linear" x1="0" y1="140" x2="400" y2="200" gradientUnits="userSpaceOnUse">
                <stop stopColor="#60a5fa" stopOpacity="0.6" />
                <stop offset="1" stopColor="#2563eb" stopOpacity="0.9" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </section>
    </div>
  );
}
